"""GraphRAG indexer using graphrag-toolkit.

References temp-repo/src/tiger_etf/graphrag/indexer.py for patterns
but does NOT modify the original source.
"""

import glob
import os

from pipeline.config import Config

TENANTS = ["etf", "bond", "fund"]


def index_all():
    for tenant in TENANTS:
        index_graphrag(tenant)


def index_graphrag(tenant: str):
    md_dir = os.path.join(Config.DATA_DIR, "graphrag")
    md_pattern = os.path.join(md_dir, f"{tenant}_*.md")
    md_files = sorted(glob.glob(md_pattern))

    if not md_files:
        print(f"  SKIP: No MD files found for tenant '{tenant}' at {md_pattern}")
        return

    print(f"GraphRAG indexing for tenant '{tenant}': {len(md_files)} files")

    if not Config.NEPTUNE_ENDPOINT or not Config.OPENSEARCH_ENDPOINT:
        print("  SKIP: Neptune/OpenSearch endpoints not configured. "
              "Set NEPTUNE_ENDPOINT and OPENSEARCH_ENDPOINT env vars.")
        _save_dry_run_log(tenant, md_files)
        return

    _run_indexing(tenant, md_files)


def _run_indexing(tenant, md_files):
    try:
        from graphrag_toolkit import LexicalGraphIndex
        from graphrag_toolkit.storage import GraphStoreFactory, VectorStoreFactory
    except ImportError:
        print("  ERROR: graphrag-toolkit not installed. Install with: pip install graphrag-toolkit")
        _save_dry_run_log(tenant, md_files)
        return

    neptune_url = f"https://{Config.NEPTUNE_ENDPOINT}:{Config.NEPTUNE_PORT}"
    opensearch_url = Config.OPENSEARCH_ENDPOINT

    graph_store = GraphStoreFactory.for_neptune(
        neptune_url,
        region=Config.OPENSEARCH_REGION,
    )
    vector_store = VectorStoreFactory.for_opensearch_serverless(
        opensearch_url,
        region=Config.OPENSEARCH_REGION,
    )

    index = LexicalGraphIndex(
        graph_store=graph_store,
        vector_store=vector_store,
        tenant_id=tenant,
        embedding_model_id=Config.EMBEDDING_MODEL_ID,
    )

    documents = []
    for md_path in md_files:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        documents.append({
            "content": content,
            "metadata": {
                "source": os.path.basename(md_path),
                "tenant": tenant,
            },
        })

    print(f"  Indexing {len(documents)} documents to Neptune (tenant={tenant})...")
    index.extract_and_build(documents)
    print(f"  GraphRAG indexing complete for tenant '{tenant}'")


def _save_dry_run_log(tenant, md_files):
    log_dir = os.path.join(Config.DATA_DIR, "graphrag", "_logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"graphrag_{tenant}_dry_run.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"Tenant: {tenant}\n")
        f.write(f"Files to index: {len(md_files)}\n")
        for md in md_files:
            f.write(f"  - {os.path.basename(md)}\n")
    print(f"  Dry run log saved: {log_path}")
