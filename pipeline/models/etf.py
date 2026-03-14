from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey, Index,
    Integer, Numeric, String, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pipeline.models.base import Base, TimestampMixin


class EtfProduct(TimestampMixin, Base):
    __tablename__ = "etf_products"
    __table_args__ = {"schema": "tiger_etf"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ksd_fund_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    name_ko: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(200))
    benchmark_index: Mapped[Optional[str]] = mapped_column(String(200))
    category_l1: Mapped[Optional[str]] = mapped_column(String(100))
    category_l2: Mapped[Optional[str]] = mapped_column(String(100))
    total_expense_ratio: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    listing_date: Mapped[Optional[date]] = mapped_column(Date)
    currency_hedge: Mapped[Optional[bool]] = mapped_column(Boolean)
    aum: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    nav: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    market_price: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    shares_outstanding: Mapped[Optional[int]] = mapped_column(BigInteger)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    holdings = relationship("EtfHolding", back_populates="product")
    performance = relationship("EtfPerformance", back_populates="product")
    distributions = relationship("EtfDistribution", back_populates="product")


class EtfHolding(Base):
    __tablename__ = "etf_holdings"
    __table_args__ = (
        UniqueConstraint("ksd_fund_code", "as_of_date", "holding_name"),
        Index("idx_etf_holdings_date", "as_of_date"),
        {"schema": "tiger_etf"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ksd_fund_code: Mapped[str] = mapped_column(
        String(20), ForeignKey("tiger_etf.etf_products.ksd_fund_code"), nullable=False
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    holding_name: Mapped[Optional[str]] = mapped_column(String(300))
    holding_ticker: Mapped[Optional[str]] = mapped_column(String(20))
    weight_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    market_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))

    product = relationship("EtfProduct", back_populates="holdings")


class EtfPerformance(Base):
    __tablename__ = "etf_performance"
    __table_args__ = (
        UniqueConstraint("ksd_fund_code", "as_of_date"),
        {"schema": "tiger_etf"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ksd_fund_code: Mapped[str] = mapped_column(
        String(20), ForeignKey("tiger_etf.etf_products.ksd_fund_code"), nullable=False
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_1w: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_1m: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_3m: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_6m: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_1y: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_ytd: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))

    product = relationship("EtfProduct", back_populates="performance")


class EtfDistribution(Base):
    __tablename__ = "etf_distributions"
    __table_args__ = (
        UniqueConstraint("ksd_fund_code", "record_date"),
        {"schema": "tiger_etf"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ksd_fund_code: Mapped[str] = mapped_column(
        String(20), ForeignKey("tiger_etf.etf_products.ksd_fund_code"), nullable=False
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date)
    amount_per_share: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    distribution_rate: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))

    product = relationship("EtfProduct", back_populates="distributions")
