# Doc 4: Data Schema & Indexing Specification

## 1. Aurora PostgreSQL 스키마

### 1.1 스키마 구조

도메인별 PostgreSQL 스키마로 분리한다. 참조 구현에서는 3개 도메인을 사용:

```sql
CREATE SCHEMA IF NOT EXISTS tiger_etf;   -- ETF 도메인
CREATE SCHEMA IF NOT EXISTS bond;        -- 채권 도메인
CREATE SCHEMA IF NOT EXISTS fund;        -- 펀드 도메인
```

커스터마이징 시 자신의 도메인 스키마로 교체한다.

### 1.2 ETF 테이블 (참조 예시)

```sql
-- 상품 마스터
CREATE TABLE tiger_etf.etf_products (
    ksd_fund_code VARCHAR PRIMARY KEY,
    ticker VARCHAR,
    name_ko VARCHAR,
    name_en VARCHAR,
    benchmark_index VARCHAR,
    category_l1 VARCHAR,
    category_l2 VARCHAR,
    total_expense_ratio NUMERIC,
    listing_date DATE,
    currency_hedge BOOLEAN,
    aum NUMERIC,
    nav NUMERIC,
    market_price NUMERIC,
    shares_outstanding BIGINT,
    is_active BOOLEAN
);

-- 보유종목
CREATE TABLE tiger_etf.etf_holdings (
    ksd_fund_code VARCHAR REFERENCES tiger_etf.etf_products(ksd_fund_code),
    as_of_date DATE,
    holding_name VARCHAR,
    holding_ticker VARCHAR,
    weight_pct NUMERIC,
    market_value NUMERIC
);

-- 수익률
CREATE TABLE tiger_etf.etf_performance (
    ksd_fund_code VARCHAR REFERENCES tiger_etf.etf_products(ksd_fund_code),
    as_of_date DATE,
    return_1w NUMERIC, return_1m NUMERIC, return_3m NUMERIC,
    return_6m NUMERIC, return_1y NUMERIC, return_ytd NUMERIC
);

-- 분배금
CREATE TABLE tiger_etf.etf_distributions (
    ksd_fund_code VARCHAR REFERENCES tiger_etf.etf_products(ksd_fund_code),
    record_date DATE,
    payment_date DATE,
    amount_per_share NUMERIC,
    distribution_rate NUMERIC
);
```

### 1.3 채권 테이블 (참조 예시)

```sql
CREATE TABLE bond.bond_products (
    bond_code VARCHAR PRIMARY KEY,
    name VARCHAR,
    issuer VARCHAR,
    issuer_type VARCHAR,
    coupon_rate NUMERIC,
    coupon_type VARCHAR,
    maturity_date DATE,
    issue_date DATE,
    credit_rating VARCHAR,
    face_value NUMERIC,
    issue_amount NUMERIC,
    currency VARCHAR,
    market VARCHAR,
    is_active BOOLEAN
);

CREATE TABLE bond.bond_prices (
    bond_code VARCHAR REFERENCES bond.bond_products(bond_code),
    trade_date DATE,
    yield_rate NUMERIC,
    clean_price NUMERIC,
    dirty_price NUMERIC,
    spread NUMERIC
);
```

### 1.4 펀드 테이블 (참조 예시)

```sql
CREATE TABLE fund.fund_products (
    fund_code VARCHAR PRIMARY KEY,
    name VARCHAR,
    management_company VARCHAR,
    fund_type VARCHAR,
    sub_type VARCHAR,
    inception_date DATE,
    total_expense_ratio NUMERIC,
    aum NUMERIC,
    nav NUMERIC,
    benchmark VARCHAR,
    risk_grade INT,
    min_investment NUMERIC,
    currency VARCHAR,
    is_active BOOLEAN
);

CREATE TABLE fund.fund_holdings (
    fund_code VARCHAR REFERENCES fund.fund_products(fund_code),
    as_of_date DATE,
    holding_name VARCHAR,
    holding_ticker VARCHAR,
    asset_class VARCHAR,
    weight_pct NUMERIC,
    market_value NUMERIC
);

CREATE TABLE fund.fund_performance (
    fund_code VARCHAR REFERENCES fund.fund_products(fund_code),
    as_of_date DATE,
    return_1m NUMERIC, return_3m NUMERIC, return_6m NUMERIC,
    return_1y NUMERIC, return_3y NUMERIC, return_ytd NUMERIC,
    bm_return_1y NUMERIC
);
```

### 1.5 스키마 설계 규칙

커스터마이징 시 다음 규칙을 따른다:

1. 도메인별 별도 스키마 사용 (`{domain}.{table}`)
2. 상품 마스터 테이블에 PK 필수 (Text2SQL에서 JOIN 기준)
3. 영문 컬럼명 사용 (LLM이 SQL 생성 시 참조)
4. 숫자 컬럼은 NUMERIC 타입 (정밀도 보장)
5. FK 관계 명시 (LLM이 JOIN 관계 추론에 활용)

## 2. Neptune 그래프 모델

### 2.1 멀티테넌시 구조

graphrag-toolkit의 LexicalGraph가 생성하는 노드/엣지 구조:

```
노드 라벨: __Entity__{tenant}__
엣지 라벨: __RELATION__

tenant 값: etf, bond, fund (소문자)
```

### 2.2 노드 속성

```
__Entity__{tenant}__:
  - value: 엔티티 이름 (예: "TIGER S&P500", "삼성전자", "AAA")
  - class: 엔티티 분류 (예: "ETF", "Holding", "Index", "Issuer")
```

### 2.3 엣지 속성

```
__RELATION__:
  - value: 관계명 (예: "HOLDS", "MANAGED_BY", "TRACKS", "ISSUED_BY")
```

### 2.4 관계 타입 (참조 예시)

| 관계 | 방향 | 설명 |
|------|------|------|
| HOLDS | (ETF/Fund) → (Holding) | 보유종목 |
| MANAGED_BY | (ETF/Fund) → (AssetManager) | 운용사 |
| TRACKS | (ETF) → (Index) | 벤치마크 추종 |
| SECTOR | (ETF) → (Sector) | 소분류 |
| CATEGORY | (ETF) → (Category) | 대분류 |
| ISSUED_BY | (Bond) → (Issuer) | 발행자 |
| RATED | (Bond) → (CreditRating) | 신용등급 |
| BENCHMARKS | (Fund) → (Benchmark) | 벤치마크 |
| SAME_BENCHMARK | (ETF) → (ETF) | 벤치마크 공유 |
| SHARES_HOLDING | (ETF) → (ETF) | 보유종목 공유 |

### 2.5 커스터마이징 포인트

- `tenant` 값을 자신의 도메인명으로 변경
- 관계 타입은 MD 파일 내용에서 LLM이 자동 추출 (graphrag-toolkit)
- 명시적 관계가 필요하면 MD 파일에 관계를 서술적으로 기술

## 3. OpenSearch 인덱스

### 3.1 인덱스 명명 규칙

```
rag-{domain}       → 일반 RAG 벡터 검색용 (MD 청크 + 임베딩)
graphrag-{domain}  → GraphRAG 벡터 검색용 (graphrag-toolkit이 자동 생성)
```

참조 구현의 6개 인덱스:
```
rag-etf, rag-bond, rag-fund
graphrag-etf, graphrag-bond, graphrag-fund
```

### 3.2 RAG 인덱스 매핑

```json
{
  "mappings": {
    "properties": {
      "text": { "type": "text" },
      "embedding": {
        "type": "knn_vector",
        "dimension": 1024,
        "method": {
          "name": "hnsw",
          "engine": "nmslib",
          "space_type": "cosinesimil"
        }
      },
      "metadata": { "type": "object" },
      "tenant": { "type": "keyword" }
    }
  }
}
```

### 3.3 벡터 차원

- Titan Embed Text v2: 1024차원
- 모델 변경 시 `Config.EMBEDDING_DIMENSION`과 인덱스 매핑 동시 수정 필요

## 4. DynamoDB 테이블

```
테이블명: conversation_turns
PK: session_id (String)
SK: turn_id (String, 형식: "turn_001", "turn_002", ...)
Billing: On-Demand (PAY_PER_REQUEST)
```

저장 항목:
```json
{
  "session_id": "uuid",
  "turn_id": "turn_001",
  "question": "사용자 질문",
  "response": "Agent 응답",
  "intent": "ETF",
  "agent_process": { ... },
  "total": { "latency": 1.2, "tokens_in": 500, "tokens_out": 200, "cost": 0.0045 },
  "session_title": "AUM 상위 ETF는?",
  "context_summary": "대화 요약...",
  "timestamp": "2026-03-15T12:00:00Z"
}
```

## 5. MD 파일 포맷 (인덱싱용)

### 5.1 GraphRAG용 MD

graphrag-toolkit이 LLM으로 엔티티/관계를 자동 추출한다. MD 파일에 도메인 지식을 서술적으로 작성:

```markdown
# TIGER S&P500 ETF

TIGER S&P500 ETF(종목코드: 360750)는 미래에셋자산운용이 운용하는 상장지수펀드이다.
S&P 500 지수를 추종하며, 미국 대형주에 투자한다.

## 보유종목
주요 보유종목으로 Apple(7.2%), Microsoft(6.8%), Amazon(3.5%)을 포함한다.

## 투자 위험
환율 변동 위험이 있으며, 환헤지를 적용하지 않는다.
미국 시장 하락 시 직접적인 영향을 받는다.

## 분류
대분류: 해외주식, 소분류: 미국대형주
```

핵심: 엔티티 이름과 관계를 자연어로 명확히 서술하면 LLM이 그래프를 추출한다.

### 5.2 RAG용 MD

RAG 인덱싱은 MD 파일을 청크로 분할 → Titan Embed v2로 임베딩 → OpenSearch에 저장한다. GraphRAG용 MD와 동일한 파일을 사용해도 되고, 별도 작성해도 된다.

### 5.3 파일 구조

```
pipeline/data/mock/
├── etf/                    # ETF CSV 파일
├── bond/                   # 채권 CSV 파일
├── fund/                   # 펀드 CSV 파일
├── graphrag/               # GraphRAG/RAG용 MD 파일
│   ├── etf_*.md
│   ├── bond_*.md
│   └── fund_*.md
└── example_queries.json    # 예시 쿼리
```

## 6. 인덱싱 파이프라인

### 6.1 실행 순서

```bash
# 1. CSV 생성
python -m pipeline.main generate-csv

# 2. MD 생성
python -m pipeline.main generate-md

# 3. DB 적재 (Aurora PG)
python -m pipeline.main load-db

# 4. GraphRAG 인덱싱 (Neptune + OpenSearch)
python -m pipeline.main index-graphrag

# 5. RAG 인덱싱 (OpenSearch)
python -m pipeline.main index-rag

# 6. 예시 쿼리 생성
python -m pipeline.main generate-queries
```

### 6.2 커스터마이징 시 수정 파일

| 작업 | 파일 |
|------|------|
| 도메인 모델 정의 | `pipeline/models/{domain}.py` (SQLAlchemy ORM) |
| DDL 스키마 등록 | `pipeline/models/schema_ddl.py` (SCHEMAS 리스트) |
| CSV 생성기 | `pipeline/generators/{domain}_generator.py` |
| MD 생성기 | `pipeline/generators/md_generator.py` |
| DB 적재기 | `pipeline/loaders/db_loader.py` |
| GraphRAG 인덱서 | `pipeline/loaders/graphrag_indexer.py` (tenant명 변경) |
| RAG 인덱서 | `pipeline/loaders/rag_indexer.py` (인덱스명 변경) |
| 예시 쿼리 | `pipeline/data/mock/example_queries.json` |
| CLI 진입점 | `pipeline/main.py` |
