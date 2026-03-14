import csv
import os

from sqlalchemy import text

from pipeline.config import Config
from pipeline.models.base import get_engine
from pipeline.models.schema_ddl import create_tables, truncate_tables

TABLE_MAP = {
    "etf": [
        ("etf_products.csv", "tiger_etf.etf_products"),
        ("etf_holdings.csv", "tiger_etf.etf_holdings"),
        ("etf_performance.csv", "tiger_etf.etf_performance"),
        ("etf_distributions.csv", "tiger_etf.etf_distributions"),
    ],
    "bond": [
        ("bond_products.csv", "bond.bond_products"),
        ("bond_prices.csv", "bond.bond_prices"),
    ],
    "fund": [
        ("fund_products.csv", "fund.fund_products"),
        ("fund_holdings.csv", "fund.fund_holdings"),
        ("fund_performance.csv", "fund.fund_performance"),
    ],
}

BATCH_SIZE = 1000


def load_all():
    engine = get_engine()
    print("Creating schemas and tables...")
    create_tables(engine)
    print("Truncating existing data...")
    truncate_tables(engine)

    for domain in ["etf", "bond", "fund"]:
        load_domain(domain, engine)


def load_domain(domain: str, engine=None):
    engine = engine or get_engine()
    csv_dir = os.path.join(Config.DATA_DIR, domain)

    if domain not in TABLE_MAP:
        raise ValueError(f"Unknown domain: {domain}")

    for csv_file, table_name in TABLE_MAP[domain]:
        csv_path = os.path.join(csv_dir, csv_file)
        if not os.path.exists(csv_path):
            print(f"  SKIP: {csv_path} not found")
            continue
        _load_csv(engine, csv_path, table_name)


def _load_csv(engine, csv_path, table_name):
    rows = _read_csv(csv_path)
    if not rows:
        print(f"  SKIP: {csv_path} is empty")
        return

    columns = list(rows[0].keys())
    placeholders = ", ".join(f":{col}" for col in columns)
    col_list = ", ".join(columns)
    sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

    loaded = 0
    with engine.connect() as conn:
        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i : i + BATCH_SIZE]
            cleaned = [_clean_row(r) for r in batch]
            conn.execute(text(sql), cleaned)
            loaded += len(batch)
        conn.commit()

    print(f"  Loaded {loaded} rows -> {table_name}")


def _read_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _clean_row(row):
    cleaned = {}
    for k, v in row.items():
        if v == "" or v is None:
            cleaned[k] = None
        elif v.lower() in ("true", "false"):
            cleaned[k] = v.lower() == "true"
        else:
            cleaned[k] = v
    return cleaned
