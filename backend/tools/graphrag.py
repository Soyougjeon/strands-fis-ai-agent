"""GraphRAG Tool - graphrag-toolkit traversal-based search.

Strategy:
1. graphrag-toolkit query() → toolkit 내장 LLM이 응답 생성 + source_nodes 반환
2. direct_response로 응답 전달 (engine.py LLM skip)
3. Lexical graph built from source_nodes for visualization
"""

import json
import logging
import re
import time
from urllib.parse import urlencode

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

from backend.config import Config

logger = logging.getLogger(__name__)

# graphrag-toolkit traversal search tenant namespace
GRAG_TENANT_MAP = {
    "ETF": "etfgrag",
    "Bond": "bondgrag",
    "Fund": "fundgrag",
}


class GraphRAGTool:
    def __init__(self):
        self.neptune_endpoint = Config.NEPTUNE_ENDPOINT
        self.neptune_port = Config.NEPTUNE_PORT
        self.opensearch_endpoint = Config.OPENSEARCH_ENDPOINT
        self.region = Config.AWS_REGION

    async def execute(self, message: str, intent: str) -> dict:
        """GraphRAG: toolkit query() for response + source_nodes for lexical graph."""
        result = {"query_step": None, "execution": {}}
        grag_tenant = GRAG_TENANT_MAP.get(intent, "etfgrag")
        start = time.time()

        response_text = ""
        source_nodes = []
        toolkit_latency = 0
        num_docs = 0

        # --- Phase 1: toolkit query() — 검색 + 응답 생성 한번에 ---
        try:
            response_text, source_nodes, toolkit_latency, num_docs = self._toolkit_query(message, grag_tenant)
            logger.info(f"Toolkit query (tenant={grag_tenant}): {num_docs} docs, {len(response_text)} chars in {toolkit_latency:.1f}s")
        except Exception as e:
            logger.warning(f"Toolkit query failed (non-fatal): {e}")

        total_latency = time.time() - start

        # Build toolkit traversal search parameters for display
        toolkit_params_info = json.dumps({
            "engine": "LexicalGraphQueryEngine.for_traversal_based_search()",
            "graph_store": f"neptune://{self.neptune_endpoint}:{self.neptune_port}",
            "vector_store": self.opensearch_endpoint,
            "tenant_id": grag_tenant,
            "retrievers": [
                {"name": "ChunkBasedSearch", "weight": 1.0},
                {"name": "EntityNetworkSearch", "weight": 1.0},
            ],
            "parameters": {
                "vss_top_k": 10,
                "max_search_results": 5,
                "max_statements": 200,
                "max_statements_per_topic": 10,
                "max_subqueries": 2,
                "max_keywords": 3,
                "reranker": "tfidf",
                "expand_entities": True,
            },
            "results": num_docs,
        }, ensure_ascii=False, indent=2)

        result["query_step"] = {
            "query_type": "graph_search",
            "query": f"traversal-based search (tenant={grag_tenant})",
            "toolkit_params": toolkit_params_info,
            "latency": round(toolkit_latency, 3),
            "tokens_in": 0,
            "tokens_out": 0,
            "cost": 0,
        }

        # --- Build raw_data for Agent Process display ---
        toolkit_results = []
        total_statements = 0
        for nws in source_nodes:
            node = getattr(nws, "node", nws)
            text = getattr(node, "text", "")
            score = getattr(nws, "score", 0)
            if text.strip():
                toolkit_results.append({"text": text.strip(), "score": round(score, 4) if score else 0})
                # Count statements
                try:
                    parsed = json.loads(text.strip())
                    stmts = parsed.get("statements", [])
                    total_statements += len(stmts)
                except (json.JSONDecodeError, AttributeError):
                    pass

        raw_data = {
            "opensearch_results": toolkit_results[:10],
        }

        # --- Estimate toolkit LLM token usage ---
        est_tokens_in = 0
        est_tokens_out = 0
        if source_nodes and response_text:
            # Rough estimation: 1 token ≈ 4 chars for English, ≈ 2 chars for Korean
            source_text_len = sum(len(getattr(getattr(nws, "node", nws), "text", "")) for nws in source_nodes)
            est_tokens_in = source_text_len // 3  # mixed Korean/English
            est_tokens_out = len(response_text) // 3

        # --- Phase 2: Build lexical graph from source_nodes ---
        lexical_graph_data = None
        if source_nodes:
            try:
                lexical_graph_data = self._build_lexical_graph(source_nodes)
                logger.info(f"Lexical graph: {len(lexical_graph_data.get('nodes', []))} nodes, {len(lexical_graph_data.get('edges', []))} edges")
            except Exception as e:
                logger.warning(f"Lexical graph build failed (non-fatal): {e}")

        summary_parts = []
        if num_docs:
            summary_parts.append(f"Toolkit Traversal: {num_docs}개 문서")
            if total_statements:
                summary_parts.append(f"{total_statements}개 statements")
            summary_parts.append(f"({toolkit_latency:.1f}s)")
            summary = " / ".join(summary_parts[:2]) + f" ({toolkit_latency:.1f}s)"
        else:
            summary = "검색 결과 없음"

        result["execution"] = {
            "result_summary": summary,
            "raw_data": raw_data,
            "graph_data": None,
            "lexical_graph_data": lexical_graph_data,
            "chart_data": None,
            "latency": round(total_latency, 3),
            "est_tokens_in": est_tokens_in,
            "est_tokens_out": est_tokens_out,
        }

        # toolkit LLM 응답을 직접 전달 (engine.py LLM skip)
        # Post-process: numbered citations
        if response_text:
            result["direct_response"] = self._format_citations(response_text)

        return result

    # ------------------------------------------------------------------ #
    #  graphrag-toolkit query (search + LLM response)
    # ------------------------------------------------------------------ #
    def _toolkit_query(self, message: str, tenant: str) -> tuple[str, list, float, int]:
        """Returns: (response_text, source_nodes, latency, num_docs)"""
        from graphrag_toolkit.lexical_graph import (
            LexicalGraphQueryEngine,
            GraphRAGConfig,
        )
        from graphrag_toolkit.lexical_graph.storage import (
            GraphStoreFactory,
            VectorStoreFactory,
        )

        GraphRAGConfig.extraction_llm = Config.LLM_MODEL_ID
        GraphRAGConfig.response_llm = Config.LLM_MODEL_ID

        neptune_url = f"https://{self.neptune_endpoint}:{self.neptune_port}"
        graph_store = GraphStoreFactory.for_graph_store(neptune_url)
        vector_store = VectorStoreFactory.for_vector_store(self.opensearch_endpoint)

        query_engine = LexicalGraphQueryEngine.for_traversal_based_search(
            graph_store=graph_store,
            vector_store=vector_store,
            tenant_id=tenant,
        )

        t0 = time.time()
        response = query_engine.query(message)
        latency = time.time() - t0

        response_text = str(response)
        source_nodes = getattr(response, "source_nodes", [])
        num_docs = len(source_nodes)

        return response_text, source_nodes, latency, num_docs

    @staticmethod
    def _format_citations(text: str) -> str:
        """Convert [Source: filename.md] or [filename.md, filename2.md] to numbered [1][2] citations with reference list."""
        sources_ordered = []
        source_map = {}

        def _get_num(source: str) -> int:
            display = re.sub(r'\s*\(etfgrag\)', '', source.strip())
            if display not in source_map:
                source_map[display] = len(sources_ordered) + 1
                sources_ordered.append(display)
            return source_map[display]

        def replace_multi(match):
            """Handle [Source: a.md, b.md] or [a.md, b.md] patterns."""
            inner = match.group(1).strip()
            # Remove "Source: " prefix
            inner = re.sub(r'^Source:\s*', '', inner)
            # Split by comma
            parts = [p.strip() for p in inner.split(',') if p.strip()]
            nums = [_get_num(p) for p in parts]
            return ''.join(f'[{n}]' for n in nums)

        # Match [Source: ...] or [filename.md ...] patterns (with possible comma-separated sources)
        result = re.sub(
            r'\[(?:Source:\s*)?([a-zA-Z0-9_\-]+\.md(?:\s*\([^\)]*\))?(?:\s*,\s*[a-zA-Z0-9_\-]+\.md(?:\s*\([^\)]*\))?)*)\]',
            replace_multi,
            text,
        )

        # Append reference list if any citations found
        if sources_ordered:
            result += "\n\n---\n**출처**\n"
            for i, src in enumerate(sources_ordered, 1):
                result += f"- [{i}] {src}\n"

        return result

    def _execute_cypher(self, cypher: str) -> dict:
        url = f"https://{self.neptune_endpoint}:{self.neptune_port}/openCypher"
        body = urlencode({"query": cypher})

        session = boto3.Session()
        creds = session.get_credentials().get_frozen_credentials()
        req = AWSRequest(
            method="POST", url=url, data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        SigV4Auth(creds, "neptune-db", self.region).add_auth(req)

        resp = requests.post(url, data=body, headers=dict(req.headers), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _build_lexical_graph(self, source_nodes: list) -> dict | None:
        """Build lexical graph using toolkit's display_results pattern (get_query_params + get_query)."""
        from graphrag_toolkit.lexical_graph.visualisation.graph_notebook.graph_notebook_visualisation import (
            get_query_params, get_query,
        )

        query_parameters = get_query_params(source_nodes)
        cypher = get_query(query_parameters, include_sources=True)

        if not cypher or not cypher.strip():
            return None

        result = self._execute_cypher(cypher)
        results = result.get("results", [])

        LABELS_TO_REFORMAT = ["Source", "Chunk", "Topic", "Statement", "Fact", "Entity"]

        nodes = {}
        edges = []
        for rec in results:
            path = rec.get("p", [])
            if not isinstance(path, list):
                continue
            for elem in path:
                etype = elem.get("~entityType", "")
                if etype == "node":
                    nid = elem.get("~id", "")
                    props = elem.get("~properties", {})
                    label = props.get("value") or props.get("source") or props.get("topic") or nid
                    ntype = "Entity"
                    for lbl in elem.get("~labels", []):
                        for t in LABELS_TO_REFORMAT:
                            if lbl.startswith(f"__{t}"):
                                ntype = t
                                break
                    if ntype == "Entity":
                        ntype = props.get("class", "Entity")
                    if nid not in nodes:
                        nodes[nid] = {"id": nid, "label": str(label), "type": ntype, "properties": {}}
                elif etype == "relationship":
                    rtype = elem.get("~type", "").lower().replace("__", "")
                    props = elem.get("~properties", {})
                    rvalue = props.get("value", rtype)
                    src = elem.get("~start", "")
                    tgt = elem.get("~end", "")
                    if src and tgt:
                        edges.append({"source": src, "target": tgt, "label": str(rvalue), "properties": {}})

        if not nodes:
            return None
        return {"nodes": list(nodes.values()), "edges": edges}

