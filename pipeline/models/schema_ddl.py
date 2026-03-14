from sqlalchemy import text

from pipeline.models.base import Base, get_engine
from pipeline.models.etf import EtfProduct, EtfHolding, EtfPerformance, EtfDistribution
from pipeline.models.bond import BondProduct, BondPrice
from pipeline.models.fund import FundProduct, FundHolding, FundPerformance


SCHEMAS = ["tiger_etf", "bond", "fund"]


def create_schemas(engine=None):
    engine = engine or get_engine()
    with engine.connect() as conn:
        for schema in SCHEMAS:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.commit()


def create_tables(engine=None):
    engine = engine or get_engine()
    create_schemas(engine)
    Base.metadata.create_all(engine)


def truncate_tables(engine=None):
    engine = engine or get_engine()
    tables = [
        "tiger_etf.etf_distributions",
        "tiger_etf.etf_performance",
        "tiger_etf.etf_holdings",
        "tiger_etf.etf_products",
        "bond.bond_prices",
        "bond.bond_products",
        "fund.fund_performance",
        "fund.fund_holdings",
        "fund.fund_products",
    ]
    with engine.connect() as conn:
        for table in tables:
            conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        conn.commit()
