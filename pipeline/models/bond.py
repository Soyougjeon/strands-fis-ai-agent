from datetime import date
from typing import Optional

from sqlalchemy import (
    Boolean, Date, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from pipeline.models.base import Base, TimestampMixin


class BondProduct(TimestampMixin, Base):
    __tablename__ = "bond_products"
    __table_args__ = {"schema": "bond"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bond_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer_type: Mapped[str] = mapped_column(String(50), nullable=False)
    coupon_rate: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    coupon_type: Mapped[str] = mapped_column(String(20), nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    credit_rating: Mapped[Optional[str]] = mapped_column(String(10))
    face_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    issue_amount: Mapped[Optional[float]] = mapped_column(Numeric(20, 2))
    currency: Mapped[str] = mapped_column(String(3), default="KRW")
    market: Mapped[Optional[str]] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    prices = relationship("BondPrice", back_populates="product")


class BondPrice(Base):
    __tablename__ = "bond_prices"
    __table_args__ = (
        UniqueConstraint("bond_code", "trade_date"),
        Index("idx_bond_prices_date", "trade_date"),
        {"schema": "bond"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bond_code: Mapped[str] = mapped_column(
        String(20), ForeignKey("bond.bond_products.bond_code"), nullable=False
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    yield_rate: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))
    clean_price: Mapped[Optional[float]] = mapped_column(Numeric(14, 4))
    dirty_price: Mapped[Optional[float]] = mapped_column(Numeric(14, 4))
    spread: Mapped[Optional[float]] = mapped_column(Numeric(8, 4))

    product = relationship("BondProduct", back_populates="prices")
