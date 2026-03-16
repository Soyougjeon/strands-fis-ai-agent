"""OpenCypher Tool - Neptune graph query generation and execution."""

import json
import logging
import re
import time
from urllib.parse import urlencode

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

from backend.agent.prompts import GRAPH_SCHEMA, OPENCYPHER_PROMPT_TEMPLATE
from backend.config import Config
from backend.services.token_tracker import calculate_cost

logger = logging.getLogger(__name__)

TENANT_MAP = {
    "ETF": "etf",
    "Bond": "bond",
    "Fund": "fund",
}

FORBIDDEN_CYPHER_PATTERN = re.compile(
    r"\b(CREATE|DELETE|SET|REMOVE|MERGE|DROP|DETACH)\b",
    re.IGNORECASE,
)


class OpenCypherTool:
    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=Config.AWS_REGION)
        self.model_id = Config.LLM_MODEL_ID
        self.neptune_endpoint = Config.NEPTUNE_ENDPOINT
        self.neptune_port = Config.NEPTUNE_PORT
        self.region = Config.AWS_REGION

    async def execute(self, message: str, intent: str) -> dict:
        """Generate OpenCypher query and execute against Neptune."""
        result = {"query_step": None, "execution": {}}

        tenant = TENANT_MAP.get(intent, "etf")
        graph_schema = GRAPH_SCHEMA.get(intent, {})

        # Step 1: Generate Cypher via LLM
        prompt = OPENCYPHER_PROMPT_TEMPLATE.format(
            tenant=graph_schema.get("tenant", tenant),
            question=message,
        )

        start = time.time()
        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
        )
        latency = time.time() - start

        output = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})
        tokens_in = usage.get("inputTokens", 0)
        tokens_out = usage.get("outputTokens", 0)
        cost = calculate_cost("claude-sonnet", tokens_in, tokens_out)

        cypher = self._extract_cypher(output)

        result["query_step"] = {
            "query_type": "opencypher",
            "query": cypher,
            "latency": round(latency, 3),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": round(cost, 6),
        }

        # Step 2: Validate Cypher
        if not self._validate_cypher(cypher):
            result["execution"] = {
                "result_summary": "Cypher 안전성 검증 실패: 읽기 전용 쿼리만 허용됩니다.",
                "raw_data": None,
                "graph_data": None,
                "chart_data": None,
                "latency": 0,
            }
            return result

        cypher = self._ensure_limit(cypher)

        # Step 3: Execute Cypher
        start = time.time()
        try:
            neptune_result = self._execute_cypher(cypher)
            exec_latency = time.time() - start

            graph_data = self._to_graph_data(neptune_result)
            graph_data = self._enrich_node_types(graph_data, tenant)
            raw_data = neptune_result.get("results", [])
            summary = f"{len(graph_data.get('nodes', []))}개 노드, {len(graph_data.get('edges', []))}개 관계 조회"

            result["execution"] = {
                "result_summary": summary,
                "raw_data": raw_data,
                "graph_data": graph_data,
                "chart_data": None,
                "latency": round(exec_latency, 3),
            }
        except Exception as e:
            exec_latency = time.time() - start
            result["execution"] = {
                "result_summary": f"Cypher 실행 오류: {str(e)}",
                "raw_data": None,
                "graph_data": None,
                "chart_data": None,
                "latency": round(exec_latency, 3),
            }

        return result

    def _extract_cypher(self, text: str) -> str:
        """Extract Cypher query from LLM response."""
        match = re.search(r"```(?:cypher)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        cypher_lines = []
        for line in lines:
            if line.upper().startswith("MATCH") or cypher_lines:
                cypher_lines.append(line)
        return "\n".join(cypher_lines) if cypher_lines else text.strip()

    def _validate_cypher(self, cypher: str) -> bool:
        """Validate Cypher is read-only."""
        if FORBIDDEN_CYPHER_PATTERN.search(cypher):
            return False
        return True

    def _ensure_limit(self, cypher: str) -> str:
        """Add LIMIT if not present."""
        if not re.search(r"\bLIMIT\b", cypher, re.IGNORECASE):
            cypher = cypher.rstrip(";").strip() + " LIMIT 50"
        return cypher

    def _execute_cypher(self, cypher: str) -> dict:
        """Execute OpenCypher query against Neptune via HTTPS."""
        url = f"https://{self.neptune_endpoint}:{self.neptune_port}/openCypher"
        body = urlencode({"query": cypher})

        session = boto3.Session()
        credentials = session.get_credentials().get_frozen_credentials()
        request = AWSRequest(
            method="POST",
            url=url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        SigV4Auth(credentials, "neptune-db", self.region).add_auth(request)

        response = requests.post(
            url,
            data=body,
            headers=dict(request.headers),
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def _to_graph_data(self, neptune_result: dict) -> dict:
        """Convert Neptune OpenCypher result to GraphData format."""
        nodes = {}
        edges = []

        src_keys = ["source", "etf", "etf1", "entity", "name", "bond", "fund", "etf_name",
                     "samsung", "samsung_entity", "src"]
        tgt_keys = ["target", "holding", "related", "related_entity", "etf2", "benchmark",
                     "index", "issuer", "rating", "connected", "connected_entity", "tgt"]
        rel_keys = ["relation", "relation1", "relation2", "rel", "type"]

        def _find_val(rec, candidates):
            for k in candidates:
                v = rec.get(k)
                if v and isinstance(v, str):
                    return v
            return None

        results = neptune_result.get("results", [])
        for record in results:
            # Neptune native node/edge format (dict with ~id)
            has_native = False
            for key, value in record.items():
                if isinstance(value, dict) and "~id" in value:
                    has_native = True
                    if "~labels" in value:
                        node_id = str(value["~id"])
                        if node_id not in nodes:
                            labels = value.get("~labels", [])
                            props = value.get("~properties", {})
                            nodes[node_id] = {
                                "id": node_id,
                                "label": props.get("value", props.get("name", node_id)),
                                "type": labels[0] if labels else "",
                                "properties": props,
                            }
                    elif "~type" in value:
                        edges.append({
                            "source": str(value.get("~start", "")),
                            "target": str(value.get("~end", "")),
                            "label": value.get("~type", ""),
                            "properties": value.get("~properties", {}),
                        })
            if has_native:
                continue

            # String column format: find source/relation/target by key name
            src = _find_val(record, src_keys)
            tgt = _find_val(record, tgt_keys)
            rel = _find_val(record, rel_keys) or ""

            # Fallback: use positional string columns
            if not src or not tgt:
                str_vals = [v for v in record.values() if isinstance(v, str) and v]
                if len(str_vals) >= 2:
                    src = src or str_vals[0]
                    tgt = tgt or str_vals[-1]
                    if len(str_vals) >= 3 and not rel:
                        rel = str_vals[1]

            if src and isinstance(src, str) and src not in nodes:
                nodes[src] = {"id": src, "label": src, "type": "Entity", "properties": {}}
            if tgt and isinstance(tgt, str) and tgt not in nodes:
                nodes[tgt] = {"id": tgt, "label": tgt, "type": "Entity", "properties": {}}
            if src and tgt:
                edges.append({"source": str(src), "target": str(tgt), "label": str(rel), "properties": {}})

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
        }

    def _enrich_node_types(self, graph_data: dict, tenant: str) -> dict:
        """Query Neptune for class info and update node types."""
        if not graph_data or not graph_data.get("nodes"):
            return graph_data

        # Collect nodes that need type enrichment
        entity_nodes = [n for n in graph_data["nodes"] if n.get("type") in ("Entity", "", None)]
        if not entity_nodes:
            return graph_data

        # Build value list for query
        values = [n["label"].replace("'", "\\'") for n in entity_nodes]
        values_str = ", ".join(f"'{v}'" for v in values[:100])

        try:
            cypher = (
                f"MATCH (e:`__Entity__{tenant}__`) "
                f"WHERE e.value IN [{values_str}] "
                f"RETURN e.value AS name, e.class AS cls"
            )
            result = self._execute_cypher(cypher)
            class_map = {}
            for rec in result.get("results", []):
                name = rec.get("name", "")
                cls = rec.get("cls", "")
                if name and cls:
                    class_map[name] = cls

            for node in graph_data["nodes"]:
                cls = class_map.get(node["label"])
                if cls:
                    node["type"] = cls
        except Exception as e:
            logger.warning(f"Node type enrichment failed: {e}")

        return graph_data
