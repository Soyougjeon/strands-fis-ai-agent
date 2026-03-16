import csv
import os
import random
from datetime import date, timedelta

from pipeline.config import Config

CATEGORIES = {
    "국내주식": {
        "subs": ["반도체", "2차전지", "배당", "대형가치", "중소형", "바이오", "금융"],
        "benchmarks": ["KOSPI", "KOSPI200", "KRX300"],
        "hedge": False,
    },
    "해외주식": {
        "subs": ["S&P500", "나스닥100", "선진국", "신흥국", "일본", "중국"],
        "benchmarks": ["S&P500", "NASDAQ100", "MSCI World", "MSCI EM"],
        "hedge": True,
    },
    "채권": {
        "subs": ["국고채", "회사채", "미국채", "하이일드"],
        "benchmarks": ["KIS국고채", "KIS종합채권", "Bloomberg US Agg"],
        "hedge": False,
    },
    "원자재": {
        "subs": ["금", "은", "원유", "구리"],
        "benchmarks": ["S&P GSCI Gold", "WTI Crude", "S&P GSCI"],
        "hedge": True,
    },
    "부동산": {
        "subs": ["리츠", "글로벌리츠"],
        "benchmarks": ["KRX 리츠 TOP10", "FTSE NAREIT"],
        "hedge": False,
    },
}

DOMESTIC_HOLDINGS = [
    ("삼성전자", "005930"), ("SK하이닉스", "000660"), ("LG에너지솔루션", "373220"),
    ("삼성바이오로직스", "207940"), ("현대차", "005380"), ("기아", "000270"),
    ("셀트리온", "068270"), ("KB금융", "105560"), ("POSCO홀딩스", "005490"),
    ("NAVER", "035420"), ("카카오", "035720"), ("삼성SDI", "006400"),
    ("LG화학", "051910"), ("현대모비스", "012330"), ("삼성물산", "028260"),
    ("SK이노베이션", "096770"), ("한국전력", "015760"), ("신한지주", "055550"),
    ("LG전자", "066570"), ("하나금융지주", "086790"),
]

FOREIGN_HOLDINGS = [
    ("Apple", "AAPL"), ("Microsoft", "MSFT"), ("NVIDIA", "NVDA"),
    ("Amazon", "AMZN"), ("Alphabet", "GOOGL"), ("Meta", "META"),
    ("Tesla", "TSLA"), ("Broadcom", "AVGO"), ("TSMC", "TSM"),
    ("Berkshire Hathaway", "BRK.B"), ("JPMorgan", "JPM"),
    ("UnitedHealth", "UNH"), ("Visa", "V"), ("Johnson & Johnson", "JNJ"),
    ("Procter & Gamble", "PG"),
]


def generate_etf_mock(count: int = None):
    count = count or Config.ETF_COUNT
    out_dir = os.path.join(Config.DATA_DIR, "etf")
    os.makedirs(out_dir, exist_ok=True)

    products = _generate_products(count)
    holdings = _generate_holdings(products)
    perf = _generate_performance(products)
    distributions = _generate_distributions(products)

    _write_csv(os.path.join(out_dir, "etf_products.csv"), products,
               ["ksd_fund_code", "ticker", "name_ko", "name_en", "benchmark_index",
                "category_l1", "category_l2", "total_expense_ratio", "listing_date",
                "currency_hedge", "aum", "nav", "market_price", "shares_outstanding", "is_active"])

    _write_csv(os.path.join(out_dir, "etf_holdings.csv"), holdings,
               ["ksd_fund_code", "as_of_date", "holding_name", "holding_ticker",
                "weight_pct", "market_value"])

    _write_csv(os.path.join(out_dir, "etf_performance.csv"), perf,
               ["ksd_fund_code", "as_of_date", "return_1w", "return_1m",
                "return_3m", "return_6m", "return_1y", "return_ytd"])

    _write_csv(os.path.join(out_dir, "etf_distributions.csv"), distributions,
               ["ksd_fund_code", "record_date", "payment_date",
                "amount_per_share", "distribution_rate"])

    print(f"ETF mock data generated: {count} products, {len(holdings)} holdings, "
          f"{len(perf)} performance, {len(distributions)} distributions")
    return products


def _generate_products(count):
    products = []
    used_names = set()

    # Phase 1: Guarantee at least one ETF per sub-category
    guaranteed = []
    for cat, info in CATEGORIES.items():
        for sub in info["subs"]:
            guaranteed.append((cat, sub))

    # Phase 2: Fill remaining slots randomly
    cats = list(CATEGORIES.keys())
    remaining = count - len(guaranteed)
    extras = []
    for _ in range(max(0, remaining)):
        cat = random.choice(cats)
        info = CATEGORIES[cat]
        sub = random.choice(info["subs"])
        extras.append((cat, sub))

    all_slots = guaranteed + extras

    # Track sub-category counts for unique naming
    sub_count = {}
    for cat, sub in all_slots:
        sub_count[sub] = sub_count.get(sub, 0) + 1

    sub_idx = {}
    for cat, sub in all_slots:
        info = CATEGORIES[cat]
        idx = sub_idx.get(sub, 0) + 1
        sub_idx[sub] = idx

        code = f"KR7{random.randint(100000, 999999):06d}0"
        ticker = f"{random.randint(100000, 999999):06d}"
        nav = round(random.uniform(8000, 80000), 2)
        aum = round(random.lognormvariate(24, 1.5), 2)
        listing = date(2015, 1, 1) + timedelta(days=random.randint(0, 3650))
        hedge = info["hedge"] and random.random() > 0.4

        # Unique name: add number suffix if multiple ETFs share the same sub
        if sub_count[sub] > 1:
            name = f"TIGER {sub}{idx} {'(H)' if hedge else ''}".strip()
        else:
            name = f"TIGER {sub} {'(H)' if hedge else ''}".strip()

        products.append({
            "ksd_fund_code": code,
            "ticker": ticker,
            "name_ko": name,
            "name_en": f"TIGER {sub} ETF {idx}",
            "benchmark_index": random.choice(info["benchmarks"]),
            "category_l1": cat,
            "category_l2": sub,
            "total_expense_ratio": round(random.uniform(0.07, 0.50), 4),
            "listing_date": listing.isoformat(),
            "currency_hedge": hedge,
            "aum": aum,
            "nav": nav,
            "market_price": round(nav * random.uniform(0.99, 1.01), 2),
            "shares_outstanding": int(aum / nav * 1000) if nav > 0 else 0,
            "is_active": True,
        })
    return products


def _generate_holdings(products):
    holdings = []
    as_of = date.today() - timedelta(days=1)
    for p in products:
        is_foreign = p["category_l1"] in ("해외주식", "원자재")
        pool = FOREIGN_HOLDINGS if is_foreign else DOMESTIC_HOLDINGS
        n = random.randint(10, min(15, len(pool)))
        selected = random.sample(pool, n)
        weights = _random_weights(n)
        for (name, ticker), w in zip(selected, weights):
            holdings.append({
                "ksd_fund_code": p["ksd_fund_code"],
                "as_of_date": as_of.isoformat(),
                "holding_name": name,
                "holding_ticker": ticker,
                "weight_pct": round(w, 4),
                "market_value": round(p["aum"] * w / 100, 2),
            })
    return holdings


def _generate_performance(products):
    perf = []
    as_of = date.today() - timedelta(days=1)
    for p in products:
        vol = 0.15 if p["category_l1"] in ("국내주식", "해외주식") else 0.05
        perf.append({
            "ksd_fund_code": p["ksd_fund_code"],
            "as_of_date": as_of.isoformat(),
            "return_1w": round(random.gauss(0.2, vol * 0.3), 4),
            "return_1m": round(random.gauss(0.8, vol), 4),
            "return_3m": round(random.gauss(2.0, vol * 2), 4),
            "return_6m": round(random.gauss(5.0, vol * 3), 4),
            "return_1y": round(random.gauss(10.0, vol * 5), 4),
            "return_ytd": round(random.gauss(8.0, vol * 4), 4),
        })
    return perf


def _generate_distributions(products):
    dists = []
    dividend_etfs = [p for p in products if "배당" in p.get("category_l2", "")]
    if not dividend_etfs:
        dividend_etfs = random.sample(products, min(10, len(products)))
    for p in dividend_etfs:
        for q in range(4):
            rec = date(2025, 3 * (q + 1), 15)
            if rec > date.today():
                continue
            dists.append({
                "ksd_fund_code": p["ksd_fund_code"],
                "record_date": rec.isoformat(),
                "payment_date": (rec + timedelta(days=15)).isoformat(),
                "amount_per_share": round(random.uniform(50, 500), 2),
                "distribution_rate": round(random.uniform(0.5, 3.0), 4),
            })
    return dists


def _random_weights(n):
    raw = [random.random() for _ in range(n)]
    raw.sort(reverse=True)
    total = sum(raw)
    return [w / total * 100 for w in raw]


def _write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
