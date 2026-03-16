"""RAG Tool - Titan Embed v2 + OpenSearch kNN vector search."""

import json
import time

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from backend.config import Config
from backend.services.token_tracker import calculate_cost

INDEX_MAP = {
    "ETF": "rag-etf",
    "Bond": "rag-bond",
    "Fund": "rag-fund",
}


class RAGTool:
    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=Config.AWS_REGION)
        session = boto3.Session()
        credentials = session.get_credentials()
        self.awsauth = AWS4Auth(
            credentials.access_key, credentials.secret_key,
            Config.AWS_REGION, "aoss",
            session_token=credentials.token,
        )
        os_host = Config.OPENSEARCH_ENDPOINT.replace("https://", "").replace("http://", "")
        self.os_client = OpenSearch(
            hosts=[{"host": os_host, "port": 443}],
            http_auth=self.awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )

    async def execute(self, message: str, intent: str) -> dict:
        """Embed query and perform kNN search on OpenSearch."""
        result = {"query_step": None, "execution": {}}

        index_name = INDEX_MAP.get(intent, "rag-etf")

        # Step 1: Generate embedding
        start = time.time()
        embedding, tokens_in = self._embed(message)
        embed_latency = time.time() - start
        cost = calculate_cost("titan-embed-v2", tokens_in, 0)

        search_body = {
            "size": 5,
            "query": {
                "knn": {
                    "vector": {
                        "vector": f"<embedding dim={len(embedding)}>",
                        "k": 5,
                    }
                }
            },
            "_source": {"excludes": ["vector"]},
        }
        opensearch_query_str = json.dumps(
            {"index": index_name, "body": search_body},
            ensure_ascii=False, indent=2,
        )

        result["query_step"] = {
            "query_type": "vector_search",
            "query": opensearch_query_str,
            "latency": round(embed_latency, 3),
            "tokens_in": tokens_in,
            "tokens_out": 0,
            "cost": round(cost, 6),
        }

        # Step 2: kNN search
        start = time.time()
        try:
            actual_search_body = {
                "size": 5,
                "query": {
                    "knn": {
                        "vector": {
                            "vector": embedding,
                            "k": 5,
                        }
                    }
                },
                "_source": {"excludes": ["vector"]},
            }

            response = self.os_client.search(index=index_name, body=actual_search_body)
            hits = response.get("hits", {}).get("hits", [])
            exec_latency = time.time() - start

            chunks = []
            for hit in hits:
                source = hit.get("_source", {})
                chunks.append({
                    "text": source.get("text", ""),
                    "metadata": source.get("metadata", {}),
                    "score": hit.get("_score", 0),
                })

            summary_parts = [
                f"{len(chunks)}개 문서 청크 검색 완료.",
            ]
            if chunks:
                top_text = chunks[0]["text"][:200]
                summary_parts.append(f"상위 결과: {top_text}...")

            result["execution"] = {
                "result_summary": " ".join(summary_parts),
                "raw_data": chunks,
                "graph_data": None,
                "chart_data": None,
                "latency": round(exec_latency, 3),
            }
        except Exception as e:
            exec_latency = time.time() - start
            result["execution"] = {
                "result_summary": f"RAG 검색 오류: {str(e)}",
                "raw_data": None,
                "graph_data": None,
                "chart_data": None,
                "latency": round(exec_latency, 3),
            }

        return result

    def _embed(self, text: str) -> tuple[list[float], int]:
        """Generate embedding using Bedrock Titan Embed v2."""
        response = self.bedrock.invoke_model(
            modelId=Config.EMBEDDING_MODEL_ID,
            body=json.dumps({"inputText": text}),
            contentType="application/json",
        )
        body = json.loads(response["body"].read())
        embedding = body.get("embedding", [])
        tokens = body.get("inputTextTokenCount", 0)
        return embedding, tokens
