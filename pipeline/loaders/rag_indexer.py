"""RAG indexer: MD files -> Chunking -> Titan Embed v2 -> OpenSearch kNN."""

import glob
import json
import os

import boto3

from pipeline.config import Config

TENANTS = ["etf", "bond", "fund"]

INDEX_SETTINGS = {
    "settings": {
        "index.knn": True,
        "index.knn.algo_param.ef_search": 512,
    },
    "mappings": {
        "properties": {
            "vector": {
                "type": "knn_vector",
                "dimension": Config.EMBEDDING_DIMENSION,
                "method": {"name": "hnsw", "engine": "nmslib"},
            },
            "text": {"type": "text"},
            "source": {"type": "keyword"},
            "chunk_index": {"type": "integer"},
            "domain": {"type": "keyword"},
        }
    },
}


def index_all():
    for tenant in TENANTS:
        index_rag(tenant)


def index_rag(tenant: str):
    md_dir = os.path.join(Config.DATA_DIR, "graphrag")
    md_pattern = os.path.join(md_dir, f"{tenant}_*.md")
    md_files = sorted(glob.glob(md_pattern))

    if not md_files:
        print(f"  SKIP: No MD files found for tenant '{tenant}'")
        return

    print(f"RAG indexing for tenant '{tenant}': {len(md_files)} files")

    documents = []
    for md_path in md_files:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        documents.append({
            "content": content,
            "source": os.path.basename(md_path),
        })

    chunks = _chunk_documents(documents, tenant)
    print(f"  Chunked into {len(chunks)} chunks")

    if not Config.OPENSEARCH_ENDPOINT:
        print("  SKIP: OpenSearch endpoint not configured. "
              "Set OPENSEARCH_ENDPOINT env var.")
        _save_dry_run_log(tenant, chunks)
        return

    embeddings = _embed_chunks(chunks)
    _index_to_opensearch(tenant, chunks, embeddings)


def _chunk_documents(documents, tenant):
    chunks = []
    chunk_size = Config.RAG_CHUNK_SIZE
    overlap = Config.RAG_CHUNK_OVERLAP

    for doc in documents:
        text = doc["content"]
        source = doc["source"]
        start = 0
        idx = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text,
                    "source": source,
                    "chunk_index": idx,
                    "domain": tenant,
                })
                idx += 1
            start = end - overlap
    return chunks


def _embed_chunks(chunks):
    client = boto3.client("bedrock-runtime", region_name=Config.BEDROCK_REGION)
    embeddings = []

    for i, chunk in enumerate(chunks):
        response = client.invoke_model(
            modelId=Config.EMBEDDING_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "inputText": chunk["text"],
                "dimensions": Config.EMBEDDING_DIMENSION,
            }),
        )
        result = json.loads(response["body"].read())
        embeddings.append(result["embedding"])

        if (i + 1) % 50 == 0:
            print(f"  Embedded {i + 1}/{len(chunks)} chunks")

    print(f"  Embedding complete: {len(embeddings)} vectors")
    return embeddings


def _index_to_opensearch(tenant, chunks, embeddings):
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth

    session = boto3.Session()
    credentials = session.get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        Config.OPENSEARCH_REGION,
        "aoss",
        session_token=credentials.token,
    )

    client = OpenSearch(
        hosts=[{"host": Config.OPENSEARCH_ENDPOINT, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )

    index_name = f"rag-{tenant}"

    if client.indices.exists(index=index_name):
        print(f"  Deleting existing index: {index_name}")
        client.indices.delete(index=index_name)

    print(f"  Creating index: {index_name}")
    client.indices.create(index=index_name, body=INDEX_SETTINGS)

    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
        doc = {
            "vector": vector,
            "text": chunk["text"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
            "domain": chunk["domain"],
        }
        client.index(index=index_name, body=doc)

        if (i + 1) % 100 == 0:
            print(f"  Indexed {i + 1}/{len(chunks)} documents")

    print(f"  RAG indexing complete: {len(chunks)} docs -> {index_name}")


def _save_dry_run_log(tenant, chunks):
    log_dir = os.path.join(Config.DATA_DIR, "graphrag", "_logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"rag_{tenant}_dry_run.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Tenant: {tenant}\n")
        f.write(f"Total chunks: {len(chunks)}\n")
        f.write(f"Chunk size: {Config.RAG_CHUNK_SIZE}, Overlap: {Config.RAG_CHUNK_OVERLAP}\n")
        for c in chunks[:5]:
            f.write(f"\n--- Chunk {c['chunk_index']} from {c['source']} ---\n")
            f.write(c["text"][:200] + "...\n")
    print(f"  Dry run log saved: {log_path}")
