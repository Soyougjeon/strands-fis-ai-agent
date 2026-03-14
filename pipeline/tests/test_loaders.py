import csv
import os
from unittest.mock import MagicMock, patch

import pytest


class TestDbLoader:
    def test_read_csv(self, tmp_path):
        csv_path = tmp_path / "test.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "value"])
            writer.writeheader()
            writer.writerow({"name": "test", "value": "123"})

        from pipeline.loaders.db_loader import _read_csv
        rows = _read_csv(str(csv_path))
        assert len(rows) == 1
        assert rows[0]["name"] == "test"

    def test_clean_row_handles_empty_strings(self):
        from pipeline.loaders.db_loader import _clean_row
        row = {"name": "test", "value": "", "active": "true", "count": "5"}
        cleaned = _clean_row(row)
        assert cleaned["value"] is None
        assert cleaned["active"] is True
        assert cleaned["count"] == "5"

    def test_clean_row_handles_boolean(self):
        from pipeline.loaders.db_loader import _clean_row
        row = {"flag1": "True", "flag2": "false", "flag3": "yes"}
        cleaned = _clean_row(row)
        assert cleaned["flag1"] is True
        assert cleaned["flag2"] is False
        assert cleaned["flag3"] == "yes"


class TestRagIndexer:
    def test_chunk_documents(self):
        from pipeline.loaders.rag_indexer import _chunk_documents

        docs = [{"content": "A" * 1200, "source": "test.md"}]
        chunks = _chunk_documents(docs, "etf")

        assert len(chunks) >= 2
        assert chunks[0]["domain"] == "etf"
        assert chunks[0]["source"] == "test.md"
        assert chunks[0]["chunk_index"] == 0

    def test_chunk_overlap(self):
        from pipeline.loaders.rag_indexer import _chunk_documents

        text = "ABCDE" * 200  # 1000 chars
        docs = [{"content": text, "source": "test.md"}]

        with patch("pipeline.config.Config.RAG_CHUNK_SIZE", 500), \
             patch("pipeline.config.Config.RAG_CHUNK_OVERLAP", 100):
            chunks = _chunk_documents(docs, "etf")

        assert len(chunks) >= 2
        # Verify overlap: end of chunk 0 should overlap with start of chunk 1
        assert chunks[0]["text"][-100:] == chunks[1]["text"][:100]

    def test_dry_run_without_endpoint(self, tmp_path):
        with patch("pipeline.config.Config.DATA_DIR", str(tmp_path)), \
             patch("pipeline.config.Config.OPENSEARCH_ENDPOINT", ""):
            graphrag_dir = tmp_path / "graphrag"
            graphrag_dir.mkdir(parents=True)
            (graphrag_dir / "etf_001_test.md").write_text("Test content " * 50)

            from pipeline.loaders.rag_indexer import index_rag
            index_rag("etf")

            log_dir = graphrag_dir / "_logs"
            assert (log_dir / "rag_etf_dry_run.txt").exists()


class TestGraphragIndexer:
    def test_dry_run_without_endpoint(self, tmp_path):
        with patch("pipeline.config.Config.DATA_DIR", str(tmp_path)), \
             patch("pipeline.config.Config.NEPTUNE_ENDPOINT", ""), \
             patch("pipeline.config.Config.OPENSEARCH_ENDPOINT", ""):
            graphrag_dir = tmp_path / "graphrag"
            graphrag_dir.mkdir(parents=True)
            (graphrag_dir / "etf_001_test.md").write_text("Test content")

            from pipeline.loaders.graphrag_indexer import index_graphrag
            index_graphrag("etf")

            log_dir = graphrag_dir / "_logs"
            assert (log_dir / "graphrag_etf_dry_run.txt").exists()
