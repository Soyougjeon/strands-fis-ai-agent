# Domain Entities - Unit 1: Mock Data Pipeline

## Schema Overview

```
Aurora PostgreSQL
  +-- tiger_etf (기존)
  |   +-- etf_products
  |   +-- etf_daily_prices
  |   +-- etf_holdings
  |   +-- etf_distributions
  |   +-- etf_performance
  +-- bond (신규)
  |   +-- bond_products
  |   +-- bond_prices
  +-- fund (신규)
      +-- fund_products
      +-- fund_holdings
      +-- fund_performance
```

---

## ETF Domain (기존 tiger_etf 스키마)

### etf_products
기존 스키마 그대로 사용. 참조: `temp-repo/src/tiger_etf/models.py`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | 자동 증가 |
| ksd_fund_code | VARCHAR(20) UNIQUE | KSD 펀드코드 |
| ticker | VARCHAR(10) | 종목코드 |
| name_ko | VARCHAR(200) | 한글명 |
| name_en | VARCHAR(200) | 영문명 |
| benchmark_index | VARCHAR(200) | 추적 지수 |
| category_l1 | VARCHAR(100) | 대분류 (국내주식/해외주식/채권/원자재 등) |
| category_l2 | VARCHAR(100) | 소분류 (반도체/2차전지/배당 등) |
| total_expense_ratio | NUMERIC(8,4) | 총보수율 (%) |
| listing_date | DATE | 상장일 |
| currency_hedge | BOOLEAN | 환헤지 여부 |
| aum | NUMERIC(20,2) | 순자산 (원) |
| nav | NUMERIC(14,2) | NAV |
| market_price | NUMERIC(14,2) | 시장가 |
| shares_outstanding | BIGINT | 발행주식수 |
| is_active | BOOLEAN | 활성 여부 |
| created_at | TIMESTAMPTZ | 생성일시 |
| updated_at | TIMESTAMPTZ | 수정일시 |

### etf_holdings
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| ksd_fund_code | VARCHAR(20) FK | etf_products 참조 |
| as_of_date | DATE | 기준일 |
| holding_name | VARCHAR(300) | 보유종목명 |
| holding_ticker | VARCHAR(20) | 보유종목 코드 |
| weight_pct | NUMERIC(8,4) | 비중 (%) |
| market_value | NUMERIC(20,2) | 평가금액 |

### etf_performance
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| ksd_fund_code | VARCHAR(20) FK | etf_products 참조 |
| as_of_date | DATE | 기준일 |
| return_1w | NUMERIC(8,4) | 1주 수익률 (%) |
| return_1m | NUMERIC(8,4) | 1개월 수익률 |
| return_3m | NUMERIC(8,4) | 3개월 수익률 |
| return_6m | NUMERIC(8,4) | 6개월 수익률 |
| return_1y | NUMERIC(8,4) | 1년 수익률 |
| return_ytd | NUMERIC(8,4) | YTD 수익률 |

### etf_distributions
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | |
| ksd_fund_code | VARCHAR(20) FK | etf_products 참조 |
| record_date | DATE | 기준일 |
| payment_date | DATE | 지급일 |
| amount_per_share | NUMERIC(12,2) | 주당 분배금 |
| distribution_rate | NUMERIC(8,4) | 분배율 (%) |

---

## Bond Domain (신규 bond 스키마)

### bond_products
| Column | Type | Description | Mock 생성 규칙 |
|--------|------|-------------|---------------|
| id | INTEGER PK | 자동 증가 | |
| bond_code | VARCHAR(20) UNIQUE | 채권코드 | "KR" + 12자리 랜덤 |
| name | VARCHAR(200) | 채권명 | "{발행사} {회차} {금리유형}" |
| issuer | VARCHAR(200) | 발행사 | 30개 한국 기업/기관 |
| issuer_type | VARCHAR(50) | 발행사 유형 | 국채/지방채/특수채/금융채/회사채 |
| coupon_rate | NUMERIC(8,4) | 표면금리 (%) | 1.5 ~ 6.5 |
| coupon_type | VARCHAR(20) | 금리유형 | 고정/변동/제로쿠폰 |
| maturity_date | DATE | 만기일 | 1~30년 후 |
| issue_date | DATE | 발행일 | 과거 1~10년 |
| credit_rating | VARCHAR(10) | 신용등급 | AAA/AA+/AA/AA-/A+/A/A-/BBB+ |
| face_value | NUMERIC(20,2) | 액면가 (원) | 10,000 |
| issue_amount | NUMERIC(20,2) | 발행금액 (억원) | 100 ~ 50,000 |
| currency | VARCHAR(3) | 통화 | KRW |
| market | VARCHAR(50) | 거래 시장 | 장내/장외 |
| is_active | BOOLEAN | 활성 여부 | true |
| created_at | TIMESTAMPTZ | 생성일시 | |

### bond_prices
| Column | Type | Description | Mock 생성 규칙 |
|--------|------|-------------|---------------|
| id | INTEGER PK | | |
| bond_code | VARCHAR(20) FK | bond_products 참조 | |
| trade_date | DATE | 거래일 | 최근 90일 |
| yield_rate | NUMERIC(8,4) | 수익률 (%) | coupon_rate 기준 +/- 변동 |
| clean_price | NUMERIC(14,4) | 세전가격 | 95 ~ 105 |
| dirty_price | NUMERIC(14,4) | 세후가격 (경과이자 포함) | clean + accrued |
| spread | NUMERIC(8,4) | 스프레드 (bp) | 등급별 차등 |

---

## Fund Domain (신규 fund 스키마)

### fund_products
| Column | Type | Description | Mock 생성 규칙 |
|--------|------|-------------|---------------|
| id | INTEGER PK | 자동 증가 | |
| fund_code | VARCHAR(20) UNIQUE | 펀드코드 | "FN" + 10자리 랜덤 |
| name | VARCHAR(200) | 펀드명 | "{운용사} {유형} {전략} 펀드" |
| management_company | VARCHAR(200) | 운용사 | 삼성/미래에셋/KB/한국투자/신한 등 15개 |
| fund_type | VARCHAR(50) | 펀드유형 | 주식형/혼합형/채권형 |
| sub_type | VARCHAR(50) | 세부유형 | 대형/중소형/가치/성장/인덱스/액티브 |
| inception_date | DATE | 설정일 | 과거 1~15년 |
| total_expense_ratio | NUMERIC(8,4) | 총보수 (%) | 0.3 ~ 2.5 |
| aum | NUMERIC(20,2) | 순자산 (억원) | 50 ~ 50,000 |
| nav | NUMERIC(14,2) | 기준가 | 800 ~ 2,500 |
| benchmark | VARCHAR(200) | 벤치마크 | KOSPI/KOSPI200/KIS종합채권 등 |
| risk_grade | INTEGER | 위험등급 | 1(매우높음) ~ 5(매우낮음) |
| min_investment | NUMERIC(20,2) | 최소투자금 (원) | 10,000 ~ 1,000,000 |
| currency | VARCHAR(3) | 통화 | KRW |
| is_active | BOOLEAN | 활성 여부 | true |
| created_at | TIMESTAMPTZ | 생성일시 | |

### fund_holdings
| Column | Type | Description | Mock 생성 규칙 |
|--------|------|-------------|---------------|
| id | INTEGER PK | | |
| fund_code | VARCHAR(20) FK | fund_products 참조 | |
| as_of_date | DATE | 기준일 | 최근 1개월 |
| holding_name | VARCHAR(300) | 보유종목명 | 삼성전자/SK하이닉스 등 한국 주요 종목 |
| holding_ticker | VARCHAR(20) | 종목코드 | |
| asset_class | VARCHAR(50) | 자산군 | 주식/채권/현금/파생 |
| weight_pct | NUMERIC(8,4) | 비중 (%) | 합계 100% |
| market_value | NUMERIC(20,2) | 평가금액 (원) | |

### fund_performance
| Column | Type | Description | Mock 생성 규칙 |
|--------|------|-------------|---------------|
| id | INTEGER PK | | |
| fund_code | VARCHAR(20) FK | fund_products 참조 | |
| as_of_date | DATE | 기준일 | 최근 1개월 |
| return_1m | NUMERIC(8,4) | 1개월 수익률 (%) | -5 ~ +8 |
| return_3m | NUMERIC(8,4) | 3개월 수익률 | -10 ~ +15 |
| return_6m | NUMERIC(8,4) | 6개월 수익률 | -15 ~ +25 |
| return_1y | NUMERIC(8,4) | 1년 수익률 | -20 ~ +40 |
| return_3y | NUMERIC(8,4) | 3년 수익률 | -30 ~ +60 |
| return_ytd | NUMERIC(8,4) | YTD 수익률 | -15 ~ +30 |
| bm_return_1y | NUMERIC(8,4) | BM 1년 수익률 | 비교용 |

---

## GraphRAG Entity Types (Neptune)

### ETF Tenant
| Entity Type | Properties | Relationships |
|------------|------------|---------------|
| ETF | name, ticker, category, aum | TRACKS_INDEX, MANAGED_BY, HOLDS |
| Index | name, market | TRACKED_BY |
| AssetManager | name | MANAGES |
| Holding | name, ticker, weight | HELD_BY |
| Sector | name | CONTAINS |
| RiskFactor | name, description | AFFECTS |

### Bond Tenant
| Entity Type | Properties | Relationships |
|------------|------------|---------------|
| Bond | name, code, coupon_rate, maturity | ISSUED_BY, RATED_BY, TRADED_IN |
| Issuer | name, type | ISSUES |
| CreditRating | grade, agency | RATES |
| Market | name | LISTS |
| RiskFactor | name, description | AFFECTS |

### Fund Tenant
| Entity Type | Properties | Relationships |
|------------|------------|---------------|
| Fund | name, code, type, aum | MANAGED_BY, BENCHMARKS, HOLDS |
| ManagementCompany | name | MANAGES |
| Benchmark | name, index | BENCHMARKED_BY |
| Holding | name, ticker, weight | HELD_BY |
| Sector | name | CONTAINS |
| RiskFactor | name, description | AFFECTS |
