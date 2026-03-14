from datetime import date
from typing import Optional

from sqlalchemy import (
    Boolean, Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pipeline.models.base import Base, TimestampMixin


class FundProduct(TimestampMixin, Base):
    __tablename__ = "fund_products"
    __table_args__ = {"schema": "fund"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fund_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    management_company: Mapped[str] = mapped_column(String(200), nullable=False)
    fund_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sub_type: Mapped[Optional[str]] = mapped_column(String(50))
    inception_date: Mapped[Optional[date]] = mapped_column(Date)
    total_expense_ratio: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    aum: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    nav: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    benchmark: Mapped[Optional[str]] = mapped_column(String(200))
    risk_grade: Mapped[Optional[int]] = mapped_column(Integer)
    min_investment: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(3), default="KRW")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    holdings = relationship("FundHolding", back_populates="product")
    performance = relationship("FundPerformance", back_populates="product")


class FundHolding(Base):
    __tablename__ = "fund_holdings"
    __table_args__ = (
        UniqueConstraint("fund_code", "as_of_date", "holding_name"),
        Index("idx_fund_holdings_date", "as_of_date"),
        {"schema": "fund"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fund_code: Mapped[str] = mapped_column(
        String(20), ForeignKey("fund.fund_products.fund_code"), nullable=False
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    holding_name: Mapped[Optional[str]] = mapped_column(String(300))
    holding_ticker: Mapped[Optional[str]] = mapped_column(String(20))
    asset_class: Mapped[Optional[str]] = mapped_column(String(50))
    weight_pct: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    market_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))

    product = relationship("FundProduct", back_populates="holdings")


class FundPerformance(Base):
    __tablename__ = "fund_performance"
    __table_args__ = (
        UniqueConstraint("fund_code", "as_of_date"),
        {"schema": "fund"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fund_code: Mapped[str] = mapped_column(
        String(20), ForeignKey("fund.fund_products.fund_code"), nullable=False
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_1m: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_3m: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_6m: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_1y: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_3y: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    return_ytd: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    bm_return_1y: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))

    product = relationship("FundProduct", back_populates="performance")
