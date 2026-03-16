"""Direct Neptune indexer - inserts Entity nodes and RELATION edges
using simple OpenCypher queries, matching graphrag-toolkit format.

Used as fallback when graphrag-toolkit's build pipeline fails due to
Neptune engine limitations.
"""

import csv
import os
import time
import uuid
from urllib.parse import urlencode

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

from pipeline.config import Config


def _execute_cypher(cypher: str, endpoint: str, port: int, region: str) -> dict:
    url = f"https://{endpoint}:{port}/openCypher"
    body = urlencode({"query": cypher})

    session = boto3.Session()
    creds = session.get_credentials().get_frozen_credentials()
    req = AWSRequest(
        method="POST", url=url, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    SigV4Auth(creds, "neptune-db", region).add_auth(req)

    resp = requests.post(url, data=body, headers=dict(req.headers), timeout=30)
    resp.raise_for_status()
    return resp.json()


def _create_entity(endpoint, port, region, tenant, value, entity_class=""):
    node_id = f"entity-{tenant}-{uuid.uuid5(uuid.NAMESPACE_DNS, f'{tenant}:{value}')}"
    cypher = (
        f"MERGE (e:`__Entity__{tenant}__` {{`~id`: '{_esc(node_id)}'}}) "
        f"SET e.value = '{_esc(value)}', e.class = '{_esc(entity_class)}' "
        f"RETURN e.value AS v"
    )
    try:
        _execute_cypher(cypher, endpoint, port, region)
    except Exception as e:
        print(f"    WARN: create entity '{value}' failed: {e}")


def _create_relation(endpoint, port, region, tenant, src_value, rel_name, tgt_value):
    src_id = f"entity-{tenant}-{uuid.uuid5(uuid.NAMESPACE_DNS, f'{tenant}:{src_value}')}"
    tgt_id = f"entity-{tenant}-{uuid.uuid5(uuid.NAMESPACE_DNS, f'{tenant}:{tgt_value}')}"
    rel_id = f"rel-{tenant}-{uuid.uuid5(uuid.NAMESPACE_DNS, f'{tenant}:{src_value}:{rel_name}:{tgt_value}')}"
    cypher = (
        f"MATCH (a:`__Entity__{tenant}__` {{`~id`: '{_esc(src_id)}'}}), "
        f"(b:`__Entity__{tenant}__` {{`~id`: '{_esc(tgt_id)}'}}) "
        f"MERGE (a)-[r:`__RELATION__` {{`~id`: '{_esc(rel_id)}'}}]->(b) "
        f"SET r.value = '{_esc(rel_name)}' "
        f"RETURN r.value AS v"
    )
    try:
        _execute_cypher(cypher, endpoint, port, region)
    except Exception as e:
        print(f"    WARN: create relation '{src_value}'-[{rel_name}]->'{tgt_value}' failed: {e}")


def _esc(s: str) -> str:
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


def _read_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def index_bond():
    endpoint = Config.NEPTUNE_ENDPOINT
    port = Config.NEPTUNE_PORT
    region = Config.OPENSEARCH_REGION
    tenant = "bond"

    if not endpoint:
        print("  SKIP: NEPTUNE_ENDPOINT not set")
        return

    csv_path = os.path.join(Config.DATA_DIR, "bond", "bond_products.csv")
    if not os.path.exists(csv_path):
        print(f"  SKIP: {csv_path} not found. Run generate-csv first.")
        return

    products = _read_csv(csv_path)
    print(f"  Bond direct indexing: {len(products)} products")

    # Collect unique entities
    issuers = set()
    ratings = set()
    issuer_types = set()
    bonds = []

    for p in products:
        name = p["name"]
        issuer = p["issuer"]
        rating = p["credit_rating"]
        issuer_type = p["issuer_type"]
        bonds.append(p)
        issuers.add(issuer)
        ratings.add(rating)
        issuer_types.add(issuer_type)

    # Create entities
    print("    Creating entities...")
    for name_val in [p["name"] for p in bonds]:
        _create_entity(endpoint, port, region, tenant, name_val, "Bond")
    for issuer in issuers:
        _create_entity(endpoint, port, region, tenant, issuer, "Issuer")
    for rating in ratings:
        _create_entity(endpoint, port, region, tenant, rating, "CreditRating")
    for it in issuer_types:
        _create_entity(endpoint, port, region, tenant, it, "IssuerType")
    # Market entities
    _create_entity(endpoint, port, region, tenant, "한국 채권 시장", "Market")

    # Create relationships
    print("    Creating relationships...")
    for p in bonds:
        _create_relation(endpoint, port, region, tenant, p["name"], "ISSUED_BY", p["issuer"])
        _create_relation(endpoint, port, region, tenant, p["name"], "RATED", p["credit_rating"])
        _create_relation(endpoint, port, region, tenant, p["issuer"], "TYPE_OF", p["issuer_type"])
        _create_relation(endpoint, port, region, tenant, p["name"], "TRADED_IN", "한국 채권 시장")
        # Coupon type relation
        coupon = p.get("coupon_type", "")
        if coupon:
            _create_entity(endpoint, port, region, tenant, f"{coupon}금리", "CouponType")
            _create_relation(endpoint, port, region, tenant, p["name"], "HAS_COUPON", f"{coupon}금리")

    # Cross-relations: same issuer bonds
    issuer_bonds = {}
    for p in bonds:
        issuer_bonds.setdefault(p["issuer"], []).append(p["name"])
    for issuer, bond_names in issuer_bonds.items():
        if len(bond_names) > 1:
            for i, b1 in enumerate(bond_names):
                for b2 in bond_names[i+1:]:
                    _create_relation(endpoint, port, region, tenant, b1, "SAME_ISSUER", b2)

    print(f"  Bond indexing complete: {len(bonds)} bonds, {len(issuers)} issuers, {len(ratings)} ratings")


def index_fund():
    endpoint = Config.NEPTUNE_ENDPOINT
    port = Config.NEPTUNE_PORT
    region = Config.OPENSEARCH_REGION
    tenant = "fund"

    if not endpoint:
        print("  SKIP: NEPTUNE_ENDPOINT not set")
        return

    csv_path = os.path.join(Config.DATA_DIR, "fund", "fund_products.csv")
    if not os.path.exists(csv_path):
        print(f"  SKIP: {csv_path} not found. Run generate-csv first.")
        return

    products = _read_csv(csv_path)
    print(f"  Fund direct indexing: {len(products)} products")

    holdings_path = os.path.join(Config.DATA_DIR, "fund", "fund_holdings.csv")
    holdings_map = {}
    if os.path.exists(holdings_path):
        for h in _read_csv(holdings_path):
            holdings_map.setdefault(h["fund_code"], []).append(h)

    # Collect unique entities
    companies = set()
    fund_types = set()
    benchmarks = set()
    holdings_set = set()

    for p in products:
        companies.add(p["management_company"])
        fund_types.add(p["fund_type"])
        if p.get("sub_type"):
            fund_types.add(p["sub_type"])
        benchmarks.add(p["benchmark"])

    for code, hs in holdings_map.items():
        for h in hs[:5]:
            holdings_set.add(h["holding_name"])

    # Create entities
    print("    Creating entities...")
    for p in products:
        _create_entity(endpoint, port, region, tenant, p["name"], "Fund")
    for c in companies:
        _create_entity(endpoint, port, region, tenant, c, "ManagementCompany")
    for ft in fund_types:
        _create_entity(endpoint, port, region, tenant, ft, "FundType")
    for bm in benchmarks:
        _create_entity(endpoint, port, region, tenant, bm, "Benchmark")
    for h in holdings_set:
        _create_entity(endpoint, port, region, tenant, h, "Holding")
    # Risk grade entities
    for grade in range(1, 6):
        _create_entity(endpoint, port, region, tenant, f"{grade}등급", "RiskGrade")

    # Create relationships
    print("    Creating relationships...")
    for p in products:
        _create_relation(endpoint, port, region, tenant, p["name"], "MANAGED_BY", p["management_company"])
        _create_relation(endpoint, port, region, tenant, p["name"], "TYPE_OF", p["fund_type"])
        if p.get("sub_type"):
            _create_relation(endpoint, port, region, tenant, p["name"], "SUB_TYPE", p["sub_type"])
        _create_relation(endpoint, port, region, tenant, p["name"], "BENCHMARKS", p["benchmark"])
        _create_relation(endpoint, port, region, tenant, p["name"], "RISK_GRADE", f"{p['risk_grade']}등급")

        # Holdings
        code = p["fund_code"]
        for h in holdings_map.get(code, [])[:5]:
            if h["holding_name"] in holdings_set:
                _create_relation(endpoint, port, region, tenant, p["name"], "HOLDS", h["holding_name"])

    # Cross-relations: same management company
    company_funds = {}
    for p in products:
        company_funds.setdefault(p["management_company"], []).append(p["name"])
    for company, fund_names in company_funds.items():
        if len(fund_names) > 1:
            for i, f1 in enumerate(fund_names):
                for f2 in fund_names[i+1:]:
                    _create_relation(endpoint, port, region, tenant, f1, "SAME_COMPANY", f2)

    # Cross-relations: shared holdings
    holding_funds = {}
    for p in products:
        code = p["fund_code"]
        for h in holdings_map.get(code, [])[:5]:
            holding_funds.setdefault(h["holding_name"], []).append(p["name"])
    for holding, fund_names in holding_funds.items():
        if len(fund_names) > 1:
            for i, f1 in enumerate(fund_names):
                for f2 in fund_names[i+1:]:
                    _create_relation(endpoint, port, region, tenant, f1, "SHARES_HOLDING", f2)

    print(f"  Fund indexing complete: {len(products)} funds, {len(companies)} companies, {len(holdings_set)} holdings")


def index_etf():
    endpoint = Config.NEPTUNE_ENDPOINT
    port = Config.NEPTUNE_PORT
    region = Config.OPENSEARCH_REGION
    tenant = "etf"

    if not endpoint:
        print("  SKIP: NEPTUNE_ENDPOINT not set")
        return

    products_path = os.path.join(Config.DATA_DIR, "etf", "etf_products.csv")
    if not os.path.exists(products_path):
        print(f"  SKIP: {products_path} not found. Run generate-csv first.")
        return

    products = _read_csv(products_path)
    print(f"  ETF direct indexing: {len(products)} products")

    holdings_path = os.path.join(Config.DATA_DIR, "etf", "etf_holdings.csv")
    holdings_map = {}
    if os.path.exists(holdings_path):
        for h in _read_csv(holdings_path):
            holdings_map.setdefault(h["ksd_fund_code"], []).append(h)

    # Collect unique entities
    categories_l1 = set()
    categories_l2 = set()
    benchmarks = set()
    holdings_set = set()

    for p in products:
        categories_l1.add(p["category_l1"])
        categories_l2.add(p["category_l2"])
        benchmarks.add(p["benchmark_index"])

    for code, hs in holdings_map.items():
        for h in hs[:5]:
            holdings_set.add(h["holding_name"])

    # Create entities
    print("    Creating entities...")
    for p in products:
        _create_entity(endpoint, port, region, tenant, p["name_ko"], "ETF")
    _create_entity(endpoint, port, region, tenant, "미래에셋자산운용", "AssetManager")
    for c1 in categories_l1:
        _create_entity(endpoint, port, region, tenant, c1, "Category")
    for c2 in categories_l2:
        _create_entity(endpoint, port, region, tenant, c2, "Sector")
    for bm in benchmarks:
        _create_entity(endpoint, port, region, tenant, bm, "Index")
    for h in holdings_set:
        _create_entity(endpoint, port, region, tenant, h, "Holding")

    # Create relationships
    print("    Creating relationships...")
    for p in products:
        name = p["name_ko"]
        _create_relation(endpoint, port, region, tenant, name, "MANAGED_BY", "미래에셋자산운용")
        _create_relation(endpoint, port, region, tenant, name, "TRACKS", p["benchmark_index"])
        _create_relation(endpoint, port, region, tenant, name, "CATEGORY", p["category_l1"])
        _create_relation(endpoint, port, region, tenant, name, "SECTOR", p["category_l2"])

        # Holdings
        code = p["ksd_fund_code"]
        for h in holdings_map.get(code, [])[:5]:
            if h["holding_name"] in holdings_set:
                _create_relation(endpoint, port, region, tenant, name, "HOLDS", h["holding_name"])

    # Cross-relations: same benchmark
    bm_etfs = {}
    for p in products:
        bm_etfs.setdefault(p["benchmark_index"], []).append(p["name_ko"])
    for bm, etf_names in bm_etfs.items():
        if len(etf_names) > 1:
            for i, e1 in enumerate(etf_names):
                for e2 in etf_names[i+1:]:
                    _create_relation(endpoint, port, region, tenant, e1, "SAME_BENCHMARK", e2)

    # Cross-relations: shared holdings
    holding_etfs = {}
    for p in products:
        code = p["ksd_fund_code"]
        for h in holdings_map.get(code, [])[:5]:
            holding_etfs.setdefault(h["holding_name"], []).append(p["name_ko"])
    for holding, etf_names in holding_etfs.items():
        if len(etf_names) > 1:
            for i, e1 in enumerate(etf_names):
                for e2 in etf_names[i+1:]:
                    _create_relation(endpoint, port, region, tenant, e1, "SHARES_HOLDING", e2)

    print(f"  ETF indexing complete: {len(products)} ETFs, {len(benchmarks)} benchmarks, {len(holdings_set)} holdings")


def index_all():
    print("=== Direct Neptune Indexing ===")
    start = time.time()
    index_etf()
    index_bond()
    index_fund()
    elapsed = time.time() - start
    print(f"=== Done in {elapsed:.1f}s ===")
