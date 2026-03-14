import csv
import os
import random
from datetime import date, timedelta

from pipeline.config import Config

MANAGEMENT_COMPANIES = [
    "삼성자산운용", "미래에셋자산운용", "KB자산운용", "한국투자신탁운용",
    "신한자산운용", "NH-Amundi자산운용", "키움투자자산운용", "한화자산운용",
    "IBK자산운용", "교보악사자산운용", "하나UBS자산운용", "트러스톤자산운용",
    "메리츠자산운용", "동양자산운용", "유진자산운용",
]

FUND_TYPE_CONFIG = {
    "주식형": {
        "sub_types": ["대형가치", "대형성장", "중소형", "인덱스", "액티브", "배당"],
        "benchmarks": ["KOSPI", "KOSPI200", "KRX300"],
        "ter_range": (1.0, 2.5),
        "risk_range": (1, 2),
        "return_vol": 0.20,
    },
    "혼합형": {
        "sub_types": ["주식혼합", "채권혼합", "균형혼합"],
        "benchmarks": ["KOSPI200 50% + KIS채권 50%", "혼합형 BM"],
        "ter_range": (0.7, 1.5),
        "risk_range": (2, 3),
        "return_vol": 0.12,
    },
    "채권형": {
        "sub_types": ["국공채", "크레딧", "종합채권", "단기채"],
        "benchmarks": ["KIS국고채", "KIS종합채권", "KIS단기채권"],
        "ter_range": (0.3, 0.8),
        "risk_range": (3, 5),
        "return_vol": 0.05,
    },
}

STOCK_HOLDINGS = [
    ("삼성전자", "005930"), ("SK하이닉스", "000660"), ("LG에너지솔루션", "373220"),
    ("삼성바이오로직스", "207940"), ("현대차", "005380"), ("기아", "000270"),
    ("셀트리온", "068270"), ("KB금융", "105560"), ("POSCO홀딩스", "005490"),
    ("NAVER", "035420"), ("카카오", "035720"), ("삼성SDI", "006400"),
    ("LG화학", "051910"), ("현대모비스", "012330"), ("삼성물산", "028260"),
]

BOND_HOLDINGS = [
    ("국고채 10년", "KR1"), ("국고채 3년", "KR2"), ("국고채 5년", "KR3"),
    ("한전채 AA+", "KR4"), ("산금채 AAA", "KR5"), ("삼성전자 회사채", "KR6"),
    ("SK 회사채", "KR7"), ("현대차 회사채", "KR8"),
]


def generate_fund_mock(count: int = None):
    count = count or Config.FUND_COUNT
    out_dir = os.path.join(Config.DATA_DIR, "fund")
    os.makedirs(out_dir, exist_ok=True)

    products = _generate_products(count)
    holdings = _generate_holdings(products)
    perf = _generate_performance(products)

    _write_csv(os.path.join(out_dir, "fund_products.csv"), products,
               ["fund_code", "name", "management_company", "fund_type", "sub_type",
                "inception_date", "total_expense_ratio", "aum", "nav", "benchmark",
                "risk_grade", "min_investment", "currency", "is_active"])

    _write_csv(os.path.join(out_dir, "fund_holdings.csv"), holdings,
               ["fund_code", "as_of_date", "holding_name", "holding_ticker",
                "asset_class", "weight_pct", "market_value"])

    _write_csv(os.path.join(out_dir, "fund_performance.csv"), perf,
               ["fund_code", "as_of_date", "return_1m", "return_3m", "return_6m",
                "return_1y", "return_3y", "return_ytd", "bm_return_1y"])

    print(f"Fund mock data generated: {count} products, {len(holdings)} holdings, "
          f"{len(perf)} performance")
    return products


def _generate_products(count):
    products = []
    type_dist = {"주식형": 15, "혼합형": 8, "채권형": 7}
    pool = []
    for ftype, cnt in type_dist.items():
        for _ in range(cnt):
            pool.append(ftype)
    random.shuffle(pool)
    pool = pool[:count]

    for i, ftype in enumerate(pool):
        cfg = FUND_TYPE_CONFIG[ftype]
        company = random.choice(MANAGEMENT_COMPANIES)
        sub = random.choice(cfg["sub_types"])
        code = f"FN{random.randint(1000000000, 9999999999)}"
        nav = round(random.uniform(800, 2500), 2)
        aum = round(random.lognormvariate(22, 1.5), 2)

        products.append({
            "fund_code": code,
            "name": f"{company} {sub} 펀드 {i + 1:02d}호",
            "management_company": company,
            "fund_type": ftype,
            "sub_type": sub,
            "inception_date": (date.today() - timedelta(days=random.randint(365, 5475))).isoformat(),
            "total_expense_ratio": round(random.uniform(*cfg["ter_range"]), 4),
            "aum": aum,
            "nav": nav,
            "benchmark": random.choice(cfg["benchmarks"]),
            "risk_grade": random.randint(*cfg["risk_range"]),
            "min_investment": random.choice([10000, 100000, 500000, 1000000]),
            "currency": "KRW",
            "is_active": True,
        })
    return products


def _generate_holdings(products):
    holdings = []
    as_of = date.today() - timedelta(days=1)
    for p in products:
        ftype = p["fund_type"]
        if ftype == "주식형":
            stock_w, bond_w, cash_w = 85, 5, 10
        elif ftype == "채권형":
            stock_w, bond_w, cash_w = 5, 85, 10
        else:
            stock_w, bond_w, cash_w = 50, 35, 15

        n_stocks = max(1, int(stock_w / 100 * random.randint(8, 12)))
        n_bonds = max(1, int(bond_w / 100 * random.randint(3, 6)))

        stock_sel = random.sample(STOCK_HOLDINGS, min(n_stocks, len(STOCK_HOLDINGS)))
        bond_sel = random.sample(BOND_HOLDINGS, min(n_bonds, len(BOND_HOLDINGS)))

        stock_weights = _random_weights(len(stock_sel), stock_w)
        bond_weights = _random_weights(len(bond_sel), bond_w)

        for (name, ticker), w in zip(stock_sel, stock_weights):
            holdings.append({
                "fund_code": p["fund_code"],
                "as_of_date": as_of.isoformat(),
                "holding_name": name,
                "holding_ticker": ticker,
                "asset_class": "주식",
                "weight_pct": round(w, 4),
                "market_value": round(p["aum"] * w / 100, 2),
            })

        for (name, ticker), w in zip(bond_sel, bond_weights):
            holdings.append({
                "fund_code": p["fund_code"],
                "as_of_date": as_of.isoformat(),
                "holding_name": name,
                "holding_ticker": ticker,
                "asset_class": "채권",
                "weight_pct": round(w, 4),
                "market_value": round(p["aum"] * w / 100, 2),
            })

        holdings.append({
            "fund_code": p["fund_code"],
            "as_of_date": as_of.isoformat(),
            "holding_name": "현금및현금성자산",
            "holding_ticker": "",
            "asset_class": "현금",
            "weight_pct": round(cash_w, 4),
            "market_value": round(p["aum"] * cash_w / 100, 2),
        })

    return holdings


def _generate_performance(products):
    perf = []
    as_of = date.today() - timedelta(days=1)
    for p in products:
        vol = FUND_TYPE_CONFIG[p["fund_type"]]["return_vol"]
        r1y = round(random.gauss(8.0, vol * 100), 4)
        perf.append({
            "fund_code": p["fund_code"],
            "as_of_date": as_of.isoformat(),
            "return_1m": round(random.gauss(1.0, vol * 30), 4),
            "return_3m": round(random.gauss(3.0, vol * 50), 4),
            "return_6m": round(random.gauss(5.0, vol * 70), 4),
            "return_1y": r1y,
            "return_3y": round(r1y * random.uniform(1.5, 3.0), 4),
            "return_ytd": round(r1y * random.uniform(0.5, 0.9), 4),
            "bm_return_1y": round(r1y + random.gauss(0, 3), 4),
        })
    return perf


def _random_weights(n, target_sum):
    raw = [random.random() for _ in range(n)]
    raw.sort(reverse=True)
    total = sum(raw)
    return [w / total * target_sum for w in raw]


def _write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
