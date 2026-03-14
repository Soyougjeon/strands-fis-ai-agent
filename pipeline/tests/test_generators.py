import csv
import json
import os
import tempfile
from unittest.mock import patch

import pytest


@pytest.fixture
def tmp_data_dir(tmp_path):
    with patch("pipeline.config.Config.DATA_DIR", str(tmp_path)):
        yield tmp_path


class TestEtfGenerator:
    def test_generate_creates_csv_files(self, tmp_data_dir):
        from pipeline.generators.etf_generator import generate_etf_mock

        generate_etf_mock(5)

        etf_dir = tmp_data_dir / "etf"
        assert (etf_dir / "etf_products.csv").exists()
        assert (etf_dir / "etf_holdings.csv").exists()
        assert (etf_dir / "etf_performance.csv").exists()
        assert (etf_dir / "etf_distributions.csv").exists()

    def test_generate_correct_count(self, tmp_data_dir):
        from pipeline.generators.etf_generator import generate_etf_mock

        products = generate_etf_mock(10)
        assert len(products) == 10

        with open(tmp_data_dir / "etf" / "etf_products.csv") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 10

    def test_product_fields(self, tmp_data_dir):
        from pipeline.generators.etf_generator import generate_etf_mock

        generate_etf_mock(1)
        with open(tmp_data_dir / "etf" / "etf_products.csv") as f:
            rows = list(csv.DictReader(f))
        row = rows[0]
        assert "ksd_fund_code" in row
        assert "name_ko" in row
        assert "category_l1" in row
        assert row["is_active"] == "True"

    def test_holdings_reference_products(self, tmp_data_dir):
        from pipeline.generators.etf_generator import generate_etf_mock

        generate_etf_mock(3)
        with open(tmp_data_dir / "etf" / "etf_products.csv") as f:
            product_codes = {r["ksd_fund_code"] for r in csv.DictReader(f)}
        with open(tmp_data_dir / "etf" / "etf_holdings.csv") as f:
            holding_codes = {r["ksd_fund_code"] for r in csv.DictReader(f)}
        assert holding_codes.issubset(product_codes)


class TestBondGenerator:
    def test_generate_creates_csv_files(self, tmp_data_dir):
        from pipeline.generators.bond_generator import generate_bond_mock

        generate_bond_mock(5)
        bond_dir = tmp_data_dir / "bond"
        assert (bond_dir / "bond_products.csv").exists()
        assert (bond_dir / "bond_prices.csv").exists()

    def test_generate_correct_count(self, tmp_data_dir):
        from pipeline.generators.bond_generator import generate_bond_mock

        products = generate_bond_mock(10)
        assert len(products) == 10

    def test_credit_rating_coupon_consistency(self, tmp_data_dir):
        from pipeline.generators.bond_generator import generate_bond_mock

        generate_bond_mock(30)
        with open(tmp_data_dir / "bond" / "bond_products.csv") as f:
            for row in csv.DictReader(f):
                if row["credit_rating"] == "AAA":
                    assert float(row["coupon_rate"]) <= 4.0


class TestFundGenerator:
    def test_generate_creates_csv_files(self, tmp_data_dir):
        from pipeline.generators.fund_generator import generate_fund_mock

        generate_fund_mock(5)
        fund_dir = tmp_data_dir / "fund"
        assert (fund_dir / "fund_products.csv").exists()
        assert (fund_dir / "fund_holdings.csv").exists()
        assert (fund_dir / "fund_performance.csv").exists()

    def test_fund_type_distribution(self, tmp_data_dir):
        from pipeline.generators.fund_generator import generate_fund_mock

        generate_fund_mock(30)
        with open(tmp_data_dir / "fund" / "fund_products.csv") as f:
            types = [r["fund_type"] for r in csv.DictReader(f)]
        assert "주식형" in types
        assert "채권형" in types


class TestMdGenerator:
    def test_generate_creates_md_files(self, tmp_data_dir):
        from pipeline.generators.etf_generator import generate_etf_mock
        from pipeline.generators.md_generator import generate_etf_md

        generate_etf_mock(3)
        generate_etf_md()

        graphrag_dir = tmp_data_dir / "graphrag"
        md_files = list(graphrag_dir.glob("etf_*.md"))
        assert len(md_files) >= 3
        assert (graphrag_dir / "etf_overview.md").exists()


class TestExampleQueries:
    def test_generate_creates_json(self, tmp_data_dir):
        from pipeline.generators.example_queries import generate_example_queries

        result = generate_example_queries()
        path = tmp_data_dir / "example_queries.json"
        assert path.exists()

        with open(path) as f:
            data = json.load(f)
        assert "etf" in data
        assert "bond" in data
        assert "fund" in data
        for domain in data.values():
            assert "text2sql" in domain
            assert "rag" in domain
            assert "graphrag" in domain
            assert "opencypher" in domain
