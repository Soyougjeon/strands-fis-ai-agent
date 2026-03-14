"""Mock Data Pipeline CLI.

Usage:
    python -m pipeline.main run-all          # Full pipeline
    python -m pipeline.main generate-csv     # Phase 1: CSV generation only
    python -m pipeline.main generate-md      # Phase 2: MD generation only
    python -m pipeline.main generate-queries # Phase 3: Example queries only
    python -m pipeline.main load-db          # Phase 4: DB loading only
    python -m pipeline.main index-graphrag   # Phase 5: GraphRAG indexing only
    python -m pipeline.main index-rag        # Phase 6: RAG indexing only
"""

import click


@click.group()
def cli():
    """Strands FIS Mock Data Pipeline"""
    pass


@cli.command("run-all")
def run_all():
    """Execute full pipeline (Phase 1-6)."""
    print("=" * 60)
    print("PHASE 1: CSV Generation")
    print("=" * 60)
    _generate_csv()

    print("\n" + "=" * 60)
    print("PHASE 2: MD File Generation")
    print("=" * 60)
    _generate_md()

    print("\n" + "=" * 60)
    print("PHASE 3: Example Query Generation")
    print("=" * 60)
    _generate_queries()

    print("\n" + "=" * 60)
    print("PHASE 4: DB Loading")
    print("=" * 60)
    _load_db()

    print("\n" + "=" * 60)
    print("PHASE 5: GraphRAG Indexing")
    print("=" * 60)
    _index_graphrag()

    print("\n" + "=" * 60)
    print("PHASE 6: RAG Indexing")
    print("=" * 60)
    _index_rag()

    print("\n" + "=" * 60)
    print("Pipeline complete!")
    print("=" * 60)


@cli.command("generate-csv")
def generate_csv_cmd():
    """Phase 1: Generate mock CSV files."""
    _generate_csv()


@cli.command("generate-md")
def generate_md_cmd():
    """Phase 2: Generate MD files for GraphRAG/RAG."""
    _generate_md()


@cli.command("generate-queries")
def generate_queries_cmd():
    """Phase 3: Generate example query JSON."""
    _generate_queries()


@cli.command("load-db")
def load_db_cmd():
    """Phase 4: Load CSV to Aurora PostgreSQL."""
    _load_db()


@cli.command("index-graphrag")
def index_graphrag_cmd():
    """Phase 5: Index MD files to Neptune (GraphRAG)."""
    _index_graphrag()


@cli.command("index-rag")
def index_rag_cmd():
    """Phase 6: Index MD files to OpenSearch (RAG)."""
    _index_rag()


def _generate_csv():
    from pipeline.generators.etf_generator import generate_etf_mock
    from pipeline.generators.bond_generator import generate_bond_mock
    from pipeline.generators.fund_generator import generate_fund_mock

    generate_etf_mock()
    generate_bond_mock()
    generate_fund_mock()


def _generate_md():
    from pipeline.generators.md_generator import generate_all_md
    generate_all_md()


def _generate_queries():
    from pipeline.generators.example_queries import generate_example_queries
    generate_example_queries()


def _load_db():
    from pipeline.loaders.db_loader import load_all
    load_all()


def _index_graphrag():
    from pipeline.loaders.graphrag_indexer import index_all
    index_all()


def _index_rag():
    from pipeline.loaders.rag_indexer import index_all
    index_all()


if __name__ == "__main__":
    cli()
