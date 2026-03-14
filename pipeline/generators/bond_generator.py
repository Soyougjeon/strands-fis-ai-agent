import csv
import os
import random
from datetime import date, timedelta

from pipeline.config import Config

ISSUERS = {
    "국채": [("대한민국정부", "AAA")],
    "특수채": [
        ("한국전력공사", "AAA"), ("한국도로공사", "AAA"),
        ("한국수자원공사", "AAA"), ("한국토지주택공사", "AAA"),
        ("한국산업은행", "AA+"),
    ],
    "금융채": [
        ("국민은행", "AA+"), ("신한은행", "AA+"), ("하나은행", "AA"),
        ("우리은행", "AA"), ("NH농협은행", "AA"),
    ],
    "회사채": [
        ("삼성전자", "AA+"), ("SK", "AA"), ("LG", "AA"),
        ("현대차", "AA-"), ("POSCO", "AA-"), ("KT", "A+"),
        ("SK텔레콤", "AA"), ("LG화학", "AA-"), ("현대건설", "A+"),
        ("롯데케미칼", "A"), ("한화솔루션", "A"), ("두산에너빌리티", "A-"),
        ("대한항공", "A-"), ("CJ제일제당", "A+"), ("GS건설", "BBB+"),
    ],
}

RATING_COUPON_RANGE = {
    "AAA": (2.5, 3.5), "AA+": (2.8, 3.8), "AA": (3.0, 4.0), "AA-": (3.2, 4.3),
    "A+": (3.5, 4.8), "A": (4.0, 5.3), "A-": (4.5, 5.8), "BBB+": (5.0, 6.5),
}

RATING_SPREAD = {
    "AAA": (0, 10), "AA+": (30, 60), "AA": (40, 80), "AA-": (50, 100),
    "A+": (80, 150), "A": (100, 200), "A-": (150, 280), "BBB+": (200, 400),
}


def generate_bond_mock(count: int = None):
    count = count or Config.BOND_COUNT
    out_dir = os.path.join(Config.DATA_DIR, "bond")
    os.makedirs(out_dir, exist_ok=True)

    products = _generate_products(count)
    prices = _generate_prices(products)

    _write_csv(os.path.join(out_dir, "bond_products.csv"), products,
               ["bond_code", "name", "issuer", "issuer_type", "coupon_rate",
                "coupon_type", "maturity_date", "issue_date", "credit_rating",
                "face_value", "issue_amount", "currency", "market", "is_active"])

    _write_csv(os.path.join(out_dir, "bond_prices.csv"), prices,
               ["bond_code", "trade_date", "yield_rate", "clean_price",
                "dirty_price", "spread"])

    print(f"Bond mock data generated: {count} products, {len(prices)} prices")
    return products


def _generate_products(count):
    products = []
    type_dist = {"국채": 5, "특수채": 5, "금융채": 5, "회사채": 15}
    pool = []
    for itype, cnt in type_dist.items():
        for _ in range(cnt):
            pool.append(itype)
    random.shuffle(pool)
    pool = pool[:count]

    for i, itype in enumerate(pool):
        issuer, rating = random.choice(ISSUERS[itype])
        code = f"KR{random.randint(100000000000, 999999999999)}"
        lo, hi = RATING_COUPON_RANGE.get(rating, (3.0, 5.0))
        coupon = round(random.uniform(lo, hi), 4)

        if itype == "국채":
            maturity_years = random.choice([3, 5, 10, 20, 30])
            coupon_type = "고정"
        else:
            maturity_years = random.choice([1, 2, 3, 5, 7])
            coupon_type = random.choice(["고정", "고정", "고정", "변동"])

        issue_date = date.today() - timedelta(days=random.randint(365, 3650))
        maturity_date = issue_date + timedelta(days=365 * maturity_years)

        products.append({
            "bond_code": code,
            "name": f"{issuer} {i + 1:03d}회 {coupon_type}금리 채권",
            "issuer": issuer,
            "issuer_type": itype,
            "coupon_rate": coupon,
            "coupon_type": coupon_type,
            "maturity_date": maturity_date.isoformat(),
            "issue_date": issue_date.isoformat(),
            "credit_rating": rating,
            "face_value": 10000.00,
            "issue_amount": round(random.uniform(100, 50000), 2),
            "currency": "KRW",
            "market": "장내" if itype in ("국채", "특수채") else random.choice(["장내", "장외"]),
            "is_active": True,
        })
    return products


def _generate_prices(products):
    prices = []
    today = date.today()
    for p in products:
        base_yield = p["coupon_rate"]
        rating = p["credit_rating"]
        sp_lo, sp_hi = RATING_SPREAD.get(rating, (50, 150))
        base_spread = random.uniform(sp_lo, sp_hi)

        for day_offset in range(90):
            trade_date = today - timedelta(days=90 - day_offset)
            if trade_date.weekday() >= 5:
                continue
            daily_change = random.gauss(0, 0.02)
            yld = round(base_yield + daily_change * (day_offset / 90), 4)
            clean = round(100 - (yld - p["coupon_rate"]) * 2, 4)
            accrued = round(p["coupon_rate"] / 365 * (day_offset % 180), 4)
            dirty = round(clean + accrued, 4)
            spread = round(base_spread + random.gauss(0, 5), 4)

            prices.append({
                "bond_code": p["bond_code"],
                "trade_date": trade_date.isoformat(),
                "yield_rate": yld,
                "clean_price": clean,
                "dirty_price": dirty,
                "spread": spread,
            })
    return prices


def _write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
