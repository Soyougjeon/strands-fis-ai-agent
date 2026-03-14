import csv
import os

from pipeline.config import Config


def generate_all_md():
    generate_etf_md()
    generate_bond_md()
    generate_fund_md()


def generate_etf_md():
    out_dir = os.path.join(Config.DATA_DIR, "graphrag")
    os.makedirs(out_dir, exist_ok=True)
    products = _read_csv(os.path.join(Config.DATA_DIR, "etf", "etf_products.csv"))
    holdings_map = _group_by(
        _read_csv(os.path.join(Config.DATA_DIR, "etf", "etf_holdings.csv")),
        "ksd_fund_code",
    )
    perf_map = _group_by(
        _read_csv(os.path.join(Config.DATA_DIR, "etf", "etf_performance.csv")),
        "ksd_fund_code",
    )

    for i, p in enumerate(products):
        code = p["ksd_fund_code"]
        h_list = holdings_map.get(code, [])
        perf = perf_map.get(code, [{}])[0]
        top_holdings = h_list[:5]

        holdings_text = "\n".join(
            f"- {h['holding_name']} ({h['holding_ticker']}): {h['weight_pct']}%"
            for h in top_holdings
        )

        hedge_text = "환헤지가 적용되어 환율 변동 위험을 줄입니다." if p.get("currency_hedge") == "True" else ""

        md = f"""# {p['name_ko']}

## 기본 정보
- 코드: {code}
- 티커: {p['ticker']}
- 카테고리: {p['category_l1']} > {p['category_l2']}
- 추적 지수: {p['benchmark_index']}
- 상장일: {p['listing_date']}
- 총보수: {p['total_expense_ratio']}%
- 순자산(AUM): {_format_krw(p['aum'])}
- 기준가(NAV): {p['nav']}원

## 투자 전략
{p['name_ko']}는 {p['benchmark_index']} 지수를 추적하는 ETF입니다.
{p['category_l1']} 시장의 {p['category_l2']} 섹터에 투자하며, 미래에셋자산운용이 운용합니다.
{hedge_text}
총보수율은 {p['total_expense_ratio']}%로, 장기 투자에 적합한 비용 구조를 갖추고 있습니다.

## 주요 보유 종목
{holdings_text}

## 수익률 현황
- 1주: {perf.get('return_1w', 'N/A')}%
- 1개월: {perf.get('return_1m', 'N/A')}%
- 3개월: {perf.get('return_3m', 'N/A')}%
- 1년: {perf.get('return_1y', 'N/A')}%

## 위험 요소
- {p['category_l2']} 섹터의 시장 변동성에 노출됩니다.
- {p['category_l1']} 시장의 거시경제 리스크가 존재합니다.
{"- 환율 변동에 따른 추가 리스크가 있습니다." if p['category_l1'] == '해외주식' else ""}
- ETF 유동성에 따라 괴리율이 발생할 수 있습니다.
"""
        filepath = os.path.join(out_dir, f"etf_{i + 1:03d}_{code}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)

    _write_etf_overview(out_dir, products)
    print(f"ETF MD files generated: {len(products)} products + 1 overview")


def generate_bond_md():
    out_dir = os.path.join(Config.DATA_DIR, "graphrag")
    os.makedirs(out_dir, exist_ok=True)
    products = _read_csv(os.path.join(Config.DATA_DIR, "bond", "bond_products.csv"))

    for i, p in enumerate(products):
        code = p["bond_code"]
        md = f"""# {p['name']}

## 기본 정보
- 채권코드: {code}
- 발행사: {p['issuer']}
- 발행사 유형: {p['issuer_type']}
- 신용등급: {p['credit_rating']}
- 표면금리: {p['coupon_rate']}%
- 금리유형: {p['coupon_type']}
- 발행일: {p['issue_date']}
- 만기일: {p['maturity_date']}
- 발행금액: {_format_krw(p['issue_amount'])}억원

## 발행사 정보
{p['issuer']}는 한국의 {p['issuer_type']} 발행 기관입니다.
{p['issuer']}가 발행한 이 채권은 신용등급 {p['credit_rating']}을 받았습니다.
{p['coupon_type']}금리 {p['coupon_rate']}%로, {'안정적인 이자 수입을 제공합니다.' if p['coupon_type'] == '고정' else '시장 금리에 연동되어 변동됩니다.'}

## 투자 특성
- 만기까지 보유 시 원금과 이자를 받을 수 있습니다.
- {p['credit_rating']} 등급은 {'최고 수준의 신용도를 의미합니다.' if p['credit_rating'] in ('AAA', 'AA+') else '양호한 신용도를 나타내지만 경기 변동에 영향을 받을 수 있습니다.'}
- {p['issuer_type']}는 {'정부가 보증하여 안전성이 높습니다.' if p['issuer_type'] == '국채' else '발행사의 재무 상태에 따라 위험이 달라집니다.'}

## 위험 요소
- 금리 상승 시 채권 가격이 하락할 수 있습니다.
- 신용등급 하락 시 스프레드가 확대될 수 있습니다.
- 유동성이 낮은 장외 채권은 매도가 어려울 수 있습니다.

## 관련 시장 동향
한국 채권 시장에서 {p['issuer_type']}은 {'기준금리 변동에 민감하게 반응합니다.' if p['issuer_type'] == '국채' else f'신용 스프레드와 발행사의 재무 건전성이 주요 변수입니다.'}
"""
        filepath = os.path.join(out_dir, f"bond_{i + 1:03d}_{code}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)

    _write_bond_overview(out_dir, products)
    print(f"Bond MD files generated: {len(products)} products + 1 overview")


def generate_fund_md():
    out_dir = os.path.join(Config.DATA_DIR, "graphrag")
    os.makedirs(out_dir, exist_ok=True)
    products = _read_csv(os.path.join(Config.DATA_DIR, "fund", "fund_products.csv"))
    holdings_map = _group_by(
        _read_csv(os.path.join(Config.DATA_DIR, "fund", "fund_holdings.csv")),
        "fund_code",
    )
    perf_map = _group_by(
        _read_csv(os.path.join(Config.DATA_DIR, "fund", "fund_performance.csv")),
        "fund_code",
    )

    for i, p in enumerate(products):
        code = p["fund_code"]
        h_list = holdings_map.get(code, [])
        perf = perf_map.get(code, [{}])[0]
        top_stocks = [h for h in h_list if h.get("asset_class") == "주식"][:5]

        holdings_text = "\n".join(
            f"- {h['holding_name']} ({h['asset_class']}): {h['weight_pct']}%"
            for h in top_stocks
        ) if top_stocks else "- 정보 없음"

        md = f"""# {p['name']}

## 기본 정보
- 펀드코드: {code}
- 운용사: {p['management_company']}
- 유형: {p['fund_type']} > {p['sub_type']}
- 설정일: {p['inception_date']}
- 총보수: {p['total_expense_ratio']}%
- 순자산: {_format_krw(p['aum'])}
- 기준가: {p['nav']}원
- 위험등급: {p['risk_grade']}등급
- 벤치마크: {p['benchmark']}

## 운용 전략
{p['name']}는 {p['management_company']}이 운용하는 {p['fund_type']} 펀드입니다.
{p['sub_type']} 전략으로 {p['benchmark']}를 벤치마크로 합니다.
위험등급 {p['risk_grade']}등급으로, {'적극적인 수익 추구를 목표로 합니다.' if int(p['risk_grade']) <= 2 else '안정적인 수익을 추구합니다.'}

## 주요 보유 종목
{holdings_text}

## 수익률 현황
- 1개월: {perf.get('return_1m', 'N/A')}%
- 3개월: {perf.get('return_3m', 'N/A')}%
- 1년: {perf.get('return_1y', 'N/A')}%
- BM 대비 초과수익(1년): {_calc_excess(perf)}%

## 위험 요소
- {p['fund_type']} 특성상 {'주식 시장 변동성에 직접 노출됩니다.' if p['fund_type'] == '주식형' else '금리 변동 리스크가 존재합니다.' if p['fund_type'] == '채권형' else '주식과 채권 시장 모두의 영향을 받습니다.'}
- 운용사의 투자 판단에 따라 성과가 달라질 수 있습니다.
- 환매 시 수수료가 발생할 수 있습니다.
"""
        filepath = os.path.join(out_dir, f"fund_{i + 1:03d}_{code}.md")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)

    _write_fund_overview(out_dir, products)
    print(f"Fund MD files generated: {len(products)} products + 1 overview")


def _write_etf_overview(out_dir, products):
    cats = {}
    for p in products:
        cats.setdefault(p["category_l1"], []).append(p)
    cat_summary = "\n".join(
        f"- **{cat}**: {len(ps)}개 ETF" for cat, ps in cats.items()
    )
    md = f"""# 한국 ETF 시장 개요

## TIGER ETF 브랜드
TIGER ETF는 미래에셋자산운용이 운용하는 국내 대표 ETF 브랜드입니다.
국내주식, 해외주식, 채권, 원자재, 부동산 등 다양한 자산에 투자할 수 있습니다.

## 카테고리 구조
{cat_summary}

## ETF 투자의 특징
- 주식처럼 거래소에서 실시간 매매 가능
- 낮은 운용보수로 장기 투자에 유리
- 다양한 자산에 분산 투자 가능
- NAV(순자산가치)와 시장가의 괴리율 존재

## 주요 지표
- **AUM(순자산)**: ETF의 총 운용자산 규모
- **NAV(기준가)**: 1주당 순자산가치
- **총보수율(TER)**: 연간 운용 비용
- **괴리율**: 시장가와 NAV의 차이

## 투자 참고사항
- 추적오차(Tracking Error)를 확인하세요
- 유동성이 충분한 ETF를 선택하세요
- 환헤지 여부에 따라 수익률이 달라집니다
- 분배금 지급 정책을 확인하세요
"""
    with open(os.path.join(out_dir, "etf_overview.md"), "w", encoding="utf-8") as f:
        f.write(md)


def _write_bond_overview(out_dir, products):
    types = {}
    for p in products:
        types.setdefault(p["issuer_type"], []).append(p)
    type_summary = "\n".join(
        f"- **{t}**: {len(ps)}개 채권" for t, ps in types.items()
    )
    md = f"""# 한국 채권 시장 개요

## 채권 유형별 특성
{type_summary}

### 국채
정부가 발행하는 채권으로 최고 수준의 안전성을 제공합니다.
한국 국고채는 AAA 등급으로 기준금리와 밀접하게 연동됩니다.

### 특수채
한국전력, 도로공사 등 공공기관이 발행하며 정부 보증에 준하는 안전성을 보입니다.

### 금융채
은행 등 금융기관이 발행하며 AA급 신용등급을 유지합니다.

### 회사채
기업이 발행하며 신용등급에 따라 수익률과 위험이 차등됩니다.
투자적격 등급(BBB- 이상)과 투기등급으로 나뉩니다.

## 신용등급 체계
- AAA: 최고 수준, 채무 불이행 위험 극히 낮음
- AA+/AA/AA-: 매우 우수, 환경 변화에 대한 대응 능력 우수
- A+/A/A-: 우수, 경기 침체 시 영향 가능
- BBB+/BBB/BBB-: 양호, 경기 변동에 민감

## 금리 환경
한국은행 기준금리에 따라 채권 시장 전체가 영향을 받습니다.
금리 인상기에는 채권 가격이 하락하고, 금리 인하기에는 상승합니다.
신용 스프레드는 경기 상황과 기업의 재무 건전성에 따라 변동합니다.
"""
    with open(os.path.join(out_dir, "bond_overview.md"), "w", encoding="utf-8") as f:
        f.write(md)


def _write_fund_overview(out_dir, products):
    types = {}
    for p in products:
        types.setdefault(p["fund_type"], []).append(p)
    type_summary = "\n".join(
        f"- **{t}**: {len(ps)}개 펀드" for t, ps in types.items()
    )
    md = f"""# 한국 공모펀드 시장 개요

## 펀드 유형별 구성
{type_summary}

### 주식형 펀드
순자산의 60% 이상을 주식에 투자합니다.
대형가치, 대형성장, 중소형, 인덱스, 액티브, 배당 등 다양한 전략이 있습니다.

### 혼합형 펀드
주식과 채권에 분산 투자합니다.
주식혼합(주식 50% 이상)과 채권혼합(채권 50% 이상)으로 나뉩니다.

### 채권형 펀드
순자산의 60% 이상을 채권에 투자합니다.
국공채, 크레딧, 종합채권, 단기채 전략이 있습니다.

## 보수 구조
- 운용보수: 자산운용사에 지급
- 판매보수: 판매사(은행/증권사)에 지급
- 수탁보수: 수탁은행에 지급
- 일반사무관리보수: 사무 관리 비용

## 위험등급 체계
- 1등급(매우 높은 위험): 주식 비중 높은 적극 투자형
- 2등급(높은 위험): 주식형 펀드
- 3등급(다소 높은 위험): 혼합형 펀드
- 4등급(보통 위험): 채권혼합형
- 5등급(낮은 위험): 채권형, MMF

## 펀드 선택 가이드
- 투자 목적과 기간에 맞는 유형 선택
- 벤치마크 대비 초과수익률 확인
- 총보수율(TER) 비교
- 운용사의 운용 역량 및 트랙레코드 확인
"""
    with open(os.path.join(out_dir, "fund_overview.md"), "w", encoding="utf-8") as f:
        f.write(md)


def _read_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _group_by(rows, key):
    groups = {}
    for r in rows:
        groups.setdefault(r[key], []).append(r)
    return groups


def _format_krw(val):
    try:
        v = float(val)
        if v >= 10000:
            return f"{v / 10000:.1f}조"
        if v >= 1:
            return f"{v:,.0f}억"
        return f"{v:,.2f}"
    except (ValueError, TypeError):
        return str(val)


def _calc_excess(perf):
    try:
        r = float(perf.get("return_1y", 0))
        bm = float(perf.get("bm_return_1y", 0))
        return f"{r - bm:.2f}"
    except (ValueError, TypeError):
        return "N/A"
