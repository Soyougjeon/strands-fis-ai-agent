# Business Logic Model - Unit 1: Mock Data Pipeline

## Pipeline Overview

```
pipeline/main.py run_all()
  |
  |-- Phase 1: CSV 생성
  |   +-- generate_etf_mock(30)   -> data/mock/etf/*.csv
  |   +-- generate_bond_mock(30)  -> data/mock/bond/*.csv
  |   +-- generate_fund_mock(30)  -> data/mock/fund/*.csv
  |
  |-- Phase 2: MD 생성
  |   +-- generate_etf_md()       -> data/mock/graphrag/etf_*.md + etf_overview.md
  |   +-- generate_bond_md()      -> data/mock/graphrag/bond_*.md + bond_overview.md
  |   +-- generate_fund_md()      -> data/mock/graphrag/fund_*.md + fund_overview.md
  |
  |-- Phase 3: 예시 질문 생성
  |   +-- generate_example_queries() -> data/mock/example_queries.json
  |
  |-- Phase 4: DB 적재
  |   +-- load_csv_to_db("etf")   -> tiger_etf.* INSERT
  |   +-- load_csv_to_db("bond")  -> bond.* INSERT
  |   +-- load_csv_to_db("fund")  -> fund.* INSERT
  |
  |-- Phase 5: GraphRAG 인덱싱
  |   +-- index_graphrag("etf")   -> Neptune(etf tenant) + OpenSearch(graphrag-etf)
  |   +-- index_graphrag("bond")  -> Neptune(bond tenant) + OpenSearch(graphrag-bond)
  |   +-- index_graphrag("fund")  -> Neptune(fund tenant) + OpenSearch(graphrag-fund)
  |
  |-- Phase 6: RAG 인덱싱
  |   +-- index_rag("etf")        -> OpenSearch(rag-etf)
  |   +-- index_rag("bond")       -> OpenSearch(rag-bond)
  |   +-- index_rag("fund")       -> OpenSearch(rag-fund)
```

---

## Phase 1: CSV Generation

### ETF Mock CSV Generator
기존 tiger_etf 스키마 기반으로 현실적 Mock 데이터 생성.

**etf_products.csv** (30건):
- ticker: "TIGER" + 카테고리 키워드 (예: "TIGER 반도체", "TIGER S&P500")
- category_l1: [국내주식, 해외주식, 채권, 원자재, 부동산] 중 랜덤
- category_l2: category_l1에 따른 하위 (반도체, 2차전지, 배당, S&P500 등)
- aum: 100억 ~ 50,000억 (로그 정규분포)
- nav: 8,000 ~ 80,000
- total_expense_ratio: 0.07 ~ 0.50
- listing_date: 2015-01-01 ~ 2025-12-31

**etf_holdings.csv** (30 ETF x 10~20 종목 = ~450건):
- 상위 종목: 삼성전자, SK하이닉스, LG에너지솔루션 등 한국 주요 종목
- 해외 ETF: Apple, Microsoft, NVIDIA 등
- weight_pct: 상위 5개 합 50~70%, 나머지 분산

**etf_performance.csv** (30건):
- 수익률: category에 따른 현실적 범위 (반도체 ETF = 변동성 높음)

**etf_distributions.csv** (배당 ETF 10개 x 4분기 = ~40건):
- 분기별 분배금

### Bond Mock CSV Generator

**bond_products.csv** (30건):
- issuer_type 분포: 국채 5, 특수채 5, 금융채 5, 회사채 15
- 발행사 풀:
  - 국채: 대한민국정부
  - 특수채: 한국전력, 한국도로공사, 한국수자원공사
  - 금융채: 국민은행, 신한은행, 하나은행, 우리은행
  - 회사채: 삼성전자, SK, LG, 현대차, POSCO, KT 등
- credit_rating: issuer_type에 따른 현실적 등급
  - 국채: AAA
  - 특수채: AAA~AA+
  - 금융채: AA+~AA-
  - 회사채: AA~BBB+
- coupon_rate: 등급/만기에 따른 차등 (AAA 2.5~3.5%, BBB 5.0~6.5%)
- maturity: 1~30년 (국채: 3/5/10/20/30년, 회사채: 1~5년)

**bond_prices.csv** (30 채권 x 90일 = ~2,700건):
- yield_rate: coupon_rate 기준 +/- 일일 변동 (변동폭 0.01~0.05%)
- clean_price: yield와 역관계 계산
- spread: 국고채 대비 가산금리 (등급별 차등)

### Fund Mock CSV Generator

**fund_products.csv** (30건):
- fund_type 분포: 주식형 15, 혼합형 8, 채권형 7
- management_company 풀: 삼성자산운용, 미래에셋자산운용, KB자산운용, 한국투자신탁, 신한자산운용, NH-Amundi, 키움투자, 한화자산운용, IBK자산운용, 교보악사, 하나UBS, 트러스톤, 메리츠, 동양, 유진
- sub_type: fund_type에 따른 세부 (주식: 대형/중소형/가치/성장/인덱스, 혼합: 주식혼합/채권혼합, 채권: 국공채/크레딧)
- total_expense_ratio: 유형별 차등 (주식 1.0~2.5%, 채권 0.3~0.8%)
- aum: 50억 ~ 50,000억

**fund_holdings.csv** (30 펀드 x 10~15 종목 = ~375건):
- 주식형: 한국 주요 상장사
- 채권형: 국고채, 회사채
- 혼합형: 주식 + 채권 혼합

**fund_performance.csv** (30건):
- 수익률: fund_type에 따른 현실적 범위
  - 주식형: 변동성 높음 (-20% ~ +40%)
  - 채권형: 안정적 (-5% ~ +8%)
  - 혼합형: 중간 (-10% ~ +20%)
- bm_return: benchmark에 따른 수익률 (초과수익 +/- 3%)

---

## Phase 2: MD File Generation

### 상품별 MD 파일 (총 90개)
각 상품에 대해 500~1000자 한국어 MD 파일 생성.

**MD 파일 구조**:
```markdown
# {상품명}

## 기본 정보
- 코드: {code}
- 유형: {type}
- 운용사/발행사: {company}
...

## 투자 전략
{상품 유형에 따른 투자 전략 서술}

## 주요 보유 종목 / 발행 조건
{holdings 또는 발행 조건 서술}

## 위험 요소
{상품 특성에 따른 위험 요소 서술}

## 관련 시장 동향
{카테고리/섹터 관련 시장 컨텍스트}
```

**ETF MD**: 추적 지수, 보유종목, 섹터 설명, 환헤지 전략 포함
**Bond MD**: 발행사 정보, 신용등급 의미, 금리 환경, 만기 전략 포함
**Fund MD**: 운용 전략, 벤치마크 대비 성과, 보유종목 특성, 위험등급 설명 포함

### 도메인 개요 MD (3개)
각 도메인에 대한 종합 개요 문서 (1500~2000자).

- **etf_overview.md**: 한국 ETF 시장 개요, TIGER ETF 브랜드, 카테고리 구조, 투자 참고사항
- **bond_overview.md**: 한국 채권 시장 개요, 채권 유형별 특성, 신용등급 체계, 금리 환경
- **fund_overview.md**: 한국 공모펀드 시장 개요, 펀드 유형별 특성, 보수 구조, 선택 가이드

---

## Phase 3: Example Query Generation

### 구조
```json
{
  "etf": {
    "text2sql": [...],
    "rag": [...],
    "graphrag": [...],
    "opencypher": [...]
  },
  "bond": { ... },
  "fund": { ... }
}
```

### ETF 예시 질문 (도메인당 4방식 x 3~5개)

**Text2SQL** (정확한 수치/필터 조회):
- "AUM 상위 10개 ETF를 보여줘"
- "반도체 섹터 ETF의 최근 1년 수익률 비교"
- "총보수율이 0.1% 이하인 ETF 목록"
- "해외주식 ETF 중 환헤지 상품은?"
- "2024년 이후 상장된 ETF는?"

**RAG** (비정형 문서 검색):
- "TIGER S&P500 ETF의 투자 전략은?"
- "반도체 ETF의 위험 요소를 설명해줘"
- "환헤지 전략이 있는 ETF의 장단점은?"
- "배당형 ETF의 분배금 정책은 어떻게 되나요?"

**GraphRAG** (관계 탐색):
- "반도체 섹터 ETF들이 공통으로 보유한 종목은?"
- "삼성전자를 보유한 ETF들의 관계를 보여줘"
- "해외주식 ETF와 관련된 위험 요소들의 연결 관계는?"

**OpenCypher** (그래프 직접 쿼리):
- "TIGER S&P500에서 2홉 내 연결된 엔티티를 보여줘"
- "반도체 섹터에 속한 모든 ETF와 보유종목 그래프"
- "미래에셋자산운용이 관리하는 ETF 네트워크"

### Bond 예시 질문

**Text2SQL**:
- "AAA 등급 채권 목록과 수익률"
- "만기 3년 이내 회사채 중 쿠폰 금리 상위 5개"
- "발행금액 1000억 이상 국채 목록"
- "최근 90일간 가장 큰 수익률 변동을 보인 채권은?"

**RAG**:
- "한국전력 채권의 투자 위험은?"
- "BBB 등급 회사채 투자 시 주의사항은?"
- "고정금리 vs 변동금리 채권의 차이점은?"

**GraphRAG**:
- "삼성전자가 발행한 채권들과 관련 신용등급의 관계는?"
- "AA등급 발행사들의 채권 네트워크를 보여줘"

**OpenCypher**:
- "국채 발행자와 연결된 모든 채권의 그래프"
- "신용등급 AA+ 이상인 발행사의 2홉 관계"

### Fund 예시 질문

**Text2SQL**:
- "주식형 펀드 중 1년 수익률 상위 10개"
- "총보수 1% 이하 채권형 펀드 목록"
- "순자산 1000억 이상 혼합형 펀드"
- "벤치마크 대비 초과수익을 낸 펀드는?"

**RAG**:
- "미래에셋 성장주 펀드의 운용 전략은?"
- "채권형 펀드의 위험등급별 특성은?"
- "가치주 vs 성장주 펀드의 차이점은?"

**GraphRAG**:
- "삼성전자를 보유한 펀드들의 관계 네트워크"
- "KB자산운용의 펀드들이 공통으로 투자하는 종목은?"

**OpenCypher**:
- "주식형 펀드에서 가장 많이 보유된 종목 Top 5와 연결 관계"
- "미래에셋자산운용이 관리하는 펀드의 전체 네트워크"

---

## Phase 4: DB Loading

### 로직
1. 스키마 생성 (DDL 실행)
   - `tiger_etf` 스키마: 기존 존재 확인, 없으면 생성
   - `bond` 스키마: CREATE SCHEMA IF NOT EXISTS bond
   - `fund` 스키마: CREATE SCHEMA IF NOT EXISTS fund
2. 테이블 생성 (CREATE TABLE IF NOT EXISTS)
3. 기존 데이터 삭제 (TRUNCATE) - 멱등성 보장
4. CSV 읽기 -> pandas DataFrame -> SQLAlchemy bulk INSERT
5. FK 순서: products -> holdings/prices/performance/distributions

### 테이블별 적재 순서
```
ETF:  etf_products -> etf_holdings -> etf_performance -> etf_distributions
Bond: bond_products -> bond_prices
Fund: fund_products -> fund_holdings -> fund_performance
```

---

## Phase 5: GraphRAG Indexing

### 로직 (기존 indexer.py 패턴 참조)
1. MD 파일 디렉토리 읽기 (도메인별)
2. graphrag-toolkit의 LexicalGraphIndex 초기화
   - Neptune endpoint 설정
   - OpenSearch endpoint 설정
   - Bedrock embedding model 설정 (Titan Embed v2)
3. 멀티테넌시 설정: `tenant={domain}` (etf/bond/fund)
4. MD 파일 → extract → build_graph → index
5. Neptune에 Entity/Relationship 노드 생성 (tenant 속성 포함)
6. OpenSearch에 graphrag-{domain} 인덱스 벡터 저장

### Neptune Multi-tenancy
모든 노드/엣지에 `__tenant__` 속성 추가:
```
MATCH (n) WHERE n.__tenant__ = 'etf' RETURN n
```

---

## Phase 6: RAG Indexing

### 로직
1. MD 파일 디렉토리 읽기 (도메인별)
2. Chunking: 각 MD를 500자 청크로 분할 (100자 오버랩)
3. Embedding: Bedrock Titan Embed v2로 각 청크 임베딩 (1024-dim)
4. OpenSearch 인덱스 생성: rag-{domain}
   - 매핑: { vector: knn_vector(1024), text: text, source: keyword, metadata: object }
5. 벡터 + 텍스트 + 메타데이터 bulk INSERT

### OpenSearch Index Settings
```json
{
  "settings": {
    "index.knn": true,
    "index.knn.algo_param.ef_search": 512
  },
  "mappings": {
    "properties": {
      "vector": { "type": "knn_vector", "dimension": 1024, "method": { "name": "hnsw", "engine": "nmslib" } },
      "text": { "type": "text" },
      "source": { "type": "keyword" },
      "chunk_index": { "type": "integer" },
      "domain": { "type": "keyword" }
    }
  }
}
```

---

## Phase Execution Order & Error Handling

### 실행 순서 (의존성 기반)
```
Phase 1 (CSV) -> Phase 2 (MD) -> Phase 3 (예시질문)
                                       |
                       +---------------+
                       v
              Phase 4 (DB 적재) -- Phase 1에 의존
              Phase 5 (GraphRAG) -- Phase 2에 의존
              Phase 6 (RAG) ------- Phase 2에 의존
```

Phase 4/5/6은 서로 독립적이므로 순차 또는 병렬 실행 가능.

### 오류 처리
- 각 Phase는 독립적으로 재실행 가능 (멱등성)
- DB 적재: TRUNCATE 후 INSERT (재실행 시 중복 없음)
- GraphRAG 인덱싱: 기존 tenant 데이터 삭제 후 재인덱싱
- RAG 인덱싱: 인덱스 삭제 후 재생성
- Phase별 성공/실패 로그 출력
- 실패 시 해당 Phase만 재실행 가능한 CLI 옵션 제공
