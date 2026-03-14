# Business Rules - Unit 1: Mock Data Pipeline

## BR-01: Mock 데이터 현실성 규칙

### BR-01-01: ETF 데이터 일관성
- category_l2는 category_l1에 종속 (국내주식→반도체/2차전지/배당, 해외주식→S&P500/나스닥/선진국)
- 해외 ETF의 holdings는 해외 종목, 국내 ETF는 국내 종목
- 환헤지(currency_hedge)는 해외주식/해외채권 ETF에만 적용
- aum과 shares_outstanding는 비례 관계
- nav와 market_price 차이는 +/- 1% 이내

### BR-01-02: 채권 데이터 일관성
- coupon_rate는 credit_rating에 반비례 (AAA: 2.5~3.5%, BBB: 5.0~6.5%)
- 국채는 항상 AAA, coupon_type은 항상 "고정"
- maturity_date > issue_date (만기 > 발행)
- bond_prices의 yield_rate와 clean_price는 역관계
- spread는 국채 대비 가산금리: AA급 30~80bp, A급 80~200bp, BBB급 200~400bp
- 일별 가격 변동은 전일 대비 +/- 0.5% 이내

### BR-01-03: 펀드 데이터 일관성
- fund_type에 따른 holdings 구성:
  - 주식형: 주식 80%+, 현금 20% 이하
  - 채권형: 채권 80%+, 현금 20% 이하
  - 혼합형: 주식 40~60%, 채권 30~50%, 현금 10~20%
- total_expense_ratio: 주식형 > 혼합형 > 채권형
- risk_grade: 주식형 1~2, 혼합형 2~3, 채권형 3~5
- fund_holdings의 weight_pct 합계 = 100% (오차 +/- 0.5%)
- bm_return과 fund_return 차이: 일반적으로 +/- 5% 이내

---

## BR-02: 데이터 생성 규칙

### BR-02-01: 고유 식별자
- ETF: ksd_fund_code는 UNIQUE, "KR7" + 숫자 형식
- Bond: bond_code는 UNIQUE, "KR" + 12자리
- Fund: fund_code는 UNIQUE, "FN" + 10자리

### BR-02-02: 날짜 규칙
- 모든 날짜는 한국 시간 기준 (KST)
- listing_date/issue_date/inception_date: 과거 날짜만 허용
- as_of_date: 최근 영업일 기준
- trade_date: 영업일만 (주말/공휴일 제외)

### BR-02-03: 숫자 정밀도
- 수익률: 소수점 4자리 (NUMERIC(8,4))
- 금액: 소수점 2자리 (NUMERIC(20,2))
- 비중: 소수점 4자리, 합계 100% +/- 0.5%

---

## BR-03: MD 파일 생성 규칙

### BR-03-01: 파일명 규칙
- 상품 MD: `{domain}_{순번:03d}_{상품코드}.md` (예: etf_001_KR7069500.md)
- 개요 MD: `{domain}_overview.md` (예: etf_overview.md)

### BR-03-02: MD 내용 규칙
- 모든 MD는 한국어로 작성
- 상품 MD: 500~1000자, 5개 섹션 (기본정보/투자전략/보유종목/위험요소/시장동향)
- 개요 MD: 1500~2000자, 도메인 시장 전체 개요
- GraphRAG 엔티티 추출을 위해 명시적 관계 표현 포함
  - "TIGER S&P500 ETF는 S&P500 지수를 추적합니다"
  - "삼성전자 채권은 삼성전자가 발행한 회사채입니다"
- 수치 데이터도 자연어로 포함 (RAG 검색 품질 향상)

---

## BR-04: 적재 규칙

### BR-04-01: DB 적재
- 적재 전 해당 테이블 TRUNCATE (멱등성)
- FK 순서 준수: 부모 테이블 먼저 적재
- batch INSERT (1000건 단위)
- 적재 후 건수 검증 (CSV 건수 == DB 건수)

### BR-04-02: GraphRAG 인덱싱
- 기존 tenant 데이터가 있으면 삭제 후 재인덱싱
- Neptune 노드의 `__tenant__` 속성으로 도메인 분리
- OpenSearch graphrag-{domain} 인덱스: 없으면 생성, 있으면 삭제 후 재생성
- Bedrock Titan Embed v2 사용 (dimension=1024)

### BR-04-03: RAG 인덱싱
- Chunking: 500자 단위, 100자 오버랩
- OpenSearch rag-{domain} 인덱스: 없으면 생성, 있으면 삭제 후 재생성
- 각 청크에 source(파일명), chunk_index, domain 메타데이터 포함
- kNN 검색 설정: HNSW, ef_search=512

---

## BR-05: 예시 질문 규칙

### BR-05-01: 질문 분류
- 각 도메인(ETF/Bond/Fund) x 4가지 방식(Text2SQL/RAG/GraphRAG/OpenCypher)
- 방식당 3~5개 질문
- 총 36~60개 예시 질문

### BR-05-02: 질문 특성
- **Text2SQL**: 수치 조회, 필터링, 집계, 정렬 키워드 포함 ("상위", "이상", "비교", "목록")
- **RAG**: 설명, 전략, 특성, 차이점 등 비정형 질문 ("설명해줘", "특성은", "차이점은")
- **GraphRAG**: 관계, 연결, 공통점 등 관계 탐색 ("관계", "연결", "공통", "네트워크")
- **OpenCypher**: 그래프 구조, 홉, 노드 중심 ("그래프", "연결된", "홉", "네트워크")

### BR-05-03: 출력 형식
```json
{
  "etf": {
    "text2sql": [
      {"question": "...", "description": "..."}
    ],
    "rag": [...],
    "graphrag": [...],
    "opencypher": [...]
  }
}
```
- UI 사이드바에서 도메인별 탭으로 표시
- [실행] 버튼 클릭 시 question을 Agent에 전달
