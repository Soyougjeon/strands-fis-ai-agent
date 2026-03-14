"""GraphRAG Tool - Neptune knowledge graph + OpenSearch vector search."""

import time

from backend.config import Config

TENANT_MAP = {
    "ETF": "etf",
    "Bond": "bond",
    "Fund": "fund",
}


class GraphRAGTool:
    def __init__(self):
        self.neptune_endpoint = Config.NEPTUNE_ENDPOINT
        self.neptune_port = Config.NEPTUNE_PORT
        self.opensearch_endpoint = Config.OPENSEARCH_ENDPOINT
        self.region = Config.AWS_REGION

    async def execute(self, message: str, intent: str) -> dict:
        """Execute GraphRAG query using LexicalGraphQueryEngine."""
        result = {"query_step": None, "execution": {}}

        tenant = TENANT_MAP.get(intent, "etf")

        start = time.time()
        try:
            from graphrag_toolkit.lexical_graph import (
                LexicalGraphIndex,
                GraphRAGConfig,
            )
            from graphrag_toolkit.lexical_graph.storage import (
                GraphStoreFactory,
                VectorStoreFactory,
            )

            GraphRAGConfig.extraction_llm = "us.anthropic.claude-sonnet-4-20250514-v1:0"
            GraphRAGConfig.response_llm = "us.anthropic.claude-sonnet-4-20250514-v1:0"

            neptune_url = f"https://{self.neptune_endpoint}:{self.neptune_port}"
            graph_store = GraphStoreFactory.for_graph_store(neptune_url)
            vector_store = VectorStoreFactory.for_vector_store(
                self.opensearch_endpoint,
            )

            graph_index = LexicalGraphIndex(
                graph_store=graph_store,
                vector_store=vector_store,
                tenant_id=tenant,
            )
            query_engine = graph_index.as_query_engine()

            response = query_engine.query(message)
            latency = time.time() - start

            response_text = str(response)
            source_nodes = getattr(response, "source_nodes", [])
            graph_data = self._extract_graph_data(source_nodes)

            result["execution"] = {
                "result_summary": response_text[:1000],
                "raw_data": {
                    "response": response_text,
                    "source_count": len(source_nodes),
                },
                "graph_data": graph_data,
                "chart_data": None,
                "latency": round(latency, 3),
            }
        except ImportError:
            latency = time.time() - start
            result["execution"] = {
                "result_summary": "GraphRAG toolkit이 설치되지 않았습니다.",
                "raw_data": None,
                "graph_data": None,
                "chart_data": None,
                "latency": round(latency, 3),
            }
        except Exception as e:
            latency = time.time() - start
            result["execution"] = {
                "result_summary": f"GraphRAG 실행 오류: {str(e)}",
                "raw_data": None,
                "graph_data": None,
                "chart_data": None,
                "latency": round(latency, 3),
            }

        return result

    def _extract_graph_data(self, source_nodes) -> dict | None:
        """Extract graph nodes and edges from source nodes if available."""
        if not source_nodes:
            return None

        nodes = {}
        edges = []

        for node in source_nodes:
            metadata = getattr(node, "metadata", {})
            node_id = metadata.get("id", str(id(node)))
            if node_id not in nodes:
                nodes[node_id] = {
                    "id": node_id,
                    "label": metadata.get("label", metadata.get("name", node_id)),
                    "type": metadata.get("type", ""),
                    "properties": {k: v for k, v in metadata.items()
                                   if k not in ("id", "label", "type")},
                }

            for rel in metadata.get("relationships", []):
                edges.append({
                    "source": node_id,
                    "target": rel.get("target", ""),
                    "label": rel.get("type", ""),
                    "properties": rel.get("properties", {}),
                })

        if not nodes:
            return None

        return {
            "nodes": list(nodes.values()),
            "edges": edges,
        }
