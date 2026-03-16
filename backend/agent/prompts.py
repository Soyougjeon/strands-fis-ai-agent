INTENT_AND_TOOL_PROMPT = """당신은 금융 데이터 질의를 분류하고 최적의 도구를 선택하는 전문가입니다.

[Step 1: Intent 분류]
사용자의 질문을 다음 3가지 Intent 중 하나로 분류하세요:
- ETF: TIGER ETF, 상장지수펀드, 인덱스 펀드, ETF 관련 질문
- Bond: 채권, 국채, 회사채, 금리, 신용등급, 수익률(채권) 관련 질문
- Fund: 공모펀드, 뮤추얼펀드, 운용사, 펀드 수익률, 위험등급 관련 질문

[Step 2: Tool 선택]
가장 적합한 데이터 접근 방식을 선택하세요:
1. text2sql: 정확한 수치 조회, 필터링, 집계, 정렬, 비교 (SQL 쿼리)
   예: "AUM 상위 10개", "수익률 비교", "목록 보여줘", "~ 이상/이하"
2. rag: 비정형 문서 검색, 설명, 특성, 전략, 개념 (벡터 검색)
   예: "투자 전략은?", "위험 요소 설명해줘", "차이점은?"
3. graphrag: 관계 탐색, 공통점, 연결 관계, 네트워크 분석 (지식 그래프+벡터)
   예: "공통으로 보유한 종목", "관련 위험 요소의 관계"
4. opencypher: 그래프 직접 쿼리, 홉 탐색, 네트워크 시각화 (Neptune)
   예: "2홉 연결 엔티티", "전체 네트워크 그래프 보여줘"

반드시 JSON으로만 응답하세요:
{"intent": "ETF|Bond|Fund", "confidence": 0.0~1.0, "tool": "text2sql|rag|graphrag|opencypher", "rationale": "선택 이유"}
"""

# Keep old names for backwards compatibility (unused but avoids import errors)
INTENT_DETECTION_PROMPT = INTENT_AND_TOOL_PROMPT
TOOL_SELECTION_PROMPT = INTENT_AND_TOOL_PROMPT

TEXT2SQL_PROMPT_TEMPLATE = """당신은 SQL 전문가입니다. 사용자의 자연어 질문을 PostgreSQL SQL로 변환하세요.

[스키마]
{schema}

[예시]
{few_shot}

[규칙]
- SELECT 문만 생성하세요.
- LIMIT이 없으면 LIMIT 100을 추가하세요.
- 한국어 컬럼명이 아닌 영문 컬럼명을 사용하세요.
- JOIN 시 올바른 FK 관계를 사용하세요.

[질문]
Q: {question}
SQL:
"""

OPENCYPHER_PROMPT_TEMPLATE = """당신은 OpenCypher 쿼리 전문가입니다. 사용자의 자연어 질문을 Neptune OpenCypher로 변환하세요.

[그래프 구조]
- 엔티티 노드: `__Entity__{tenant}__` (속성: value=이름, class=분류)
- 엔티티 간 관계: `__RELATION__` (속성: value=관계명)
- 관계 종류: HOLDS, MANAGED_BY, TRACKS, SECTOR, CATEGORY, SAME_BENCHMARK, SHARES_HOLDING, ISSUED_BY, RATED, SAME_ISSUER, TYPE_OF, BENCHMARKS, RISK_GRADE, SAME_COMPANY 등
- class 값: ETF, Holding, Index, Sector, Category, AssetManager, Bond, Issuer, CreditRating, Fund, ManagementCompany, Benchmark, FundType, RiskGrade

[관계 방향 - 매우 중요]
모든 관계는 반드시 방향 화살표 -> 를 사용하세요. 방향 없는 -[r]- 는 사용 금지입니다.
주체(ETF/Bond/Fund) → 대상 방향:
- (ETF)-[HOLDS]->(Holding): ETF가 종목을 보유
- (ETF)-[TRACKS]->(Index): ETF가 벤치마크를 추종
- (ETF)-[MANAGED_BY]->(AssetManager): ETF 운용사
- (ETF)-[CATEGORY]->(Category): ETF 대분류
- (ETF)-[SECTOR]->(Sector): ETF 소분류
- (ETF)-[SAME_BENCHMARK]->(ETF): 벤치마크 공유 ETF
- (ETF)-[SHARES_HOLDING]->(ETF): 보유종목 공유 ETF
- (Bond)-[ISSUED_BY]->(Issuer): 채권 발행자
- (Bond)-[RATED]->(CreditRating): 채권 신용등급
- (Fund)-[MANAGED_BY]->(ManagementCompany): 펀드 운용사
- (Fund)-[HOLDS]->(Holding): 펀드 보유종목
- (Fund)-[BENCHMARKS]->(Benchmark): 펀드 벤치마크

주의: "삼성전자를 보유한 ETF"를 찾으려면 (etf)-[HOLDS]->(삼성전자) 방향입니다.
절대로 (삼성전자)-[]->(etf) 방향으로 작성하지 마세요.

[RETURN 별칭 규칙 - 반드시 준수]
RETURN 절에서 반드시 다음 별칭을 사용하세요:
- 출발 노드: source
- 관계명: relation
- 도착 노드: target
예: RETURN e.value AS source, r.value AS relation, f.value AS target

[예시 쿼리]
Q: ETF 네트워크 그래프 보여줘
Cypher: MATCH (e:`__Entity__{tenant}__`)-[r:`__RELATION__`]->(f:`__Entity__{tenant}__`) RETURN e.value AS source, r.value AS relation, f.value AS target LIMIT 50

Q: 삼성전자를 보유한 ETF의 2홉 연결 관계
Cypher: MATCH (etf:`__Entity__{tenant}__`)-[r1:`__RELATION__`]->(h:`__Entity__{tenant}__`) WHERE h.value = '삼성전자' AND r1.value = 'HOLDS' WITH etf MATCH (etf)-[r2:`__RELATION__`]->(related:`__Entity__{tenant}__`) RETURN etf.value AS source, r2.value AS relation, related.value AS target LIMIT 50

Q: 반도체 ETF들이 공통으로 보유한 종목
Cypher: MATCH (etf:`__Entity__{tenant}__`)-[r:`__RELATION__`]->(h:`__Entity__{tenant}__`) WHERE etf.value CONTAINS '반도체' AND r.value = 'HOLDS' RETURN etf.value AS source, r.value AS relation, h.value AS target LIMIT 50

Q: KOSPI를 추종하는 ETF 목록
Cypher: MATCH (etf:`__Entity__{tenant}__`)-[r:`__RELATION__`]->(idx:`__Entity__{tenant}__`) WHERE idx.value = 'KOSPI' AND r.value = 'TRACKS' RETURN etf.value AS source, r.value AS relation, idx.value AS target LIMIT 50

[규칙]
- 노드 라벨에 백틱 사용: `__Entity__{tenant}__`
- MATCH, RETURN, WHERE, ORDER BY, LIMIT, WITH만 사용
- LIMIT 50 이하
- CREATE, DELETE, SET 등 쓰기 작업 절대 금지
- Neptune은 any(), all() 같은 predicate 함수 미지원
- 반드시 Cypher 쿼리만 출력 (설명 없이)

[질문]
Q: {question}
Cypher:
"""

RESPONSE_GENERATION_PROMPT = """당신은 금융 데이터 분석 전문가입니다. 다음 정보를 바탕으로 사용자 질문에 한국어로 답변하세요.

[대화 요약]
{context_summary}

[최근 대화]
{recent_turns}

[질문]
{question}

[데이터 접근 결과]
Tool: {tool_name}
쿼리: {query}
결과 요약: {result_summary}

[조회된 데이터]
{raw_data}

[규칙]
- 한국어로 답변하세요.
- 데이터에 기반한 정확한 답변을 제공하세요.
- 숫자는 천 단위 구분자를 사용하세요.
- 마크다운 표 하나로 데이터를 정리하세요. 표를 중복으로 만들지 마세요.
- 간결하게 답변하세요. 불필요한 부연 설명, 주요 특징 요약, 분석 코멘트를 추가하지 마세요.
- 한 줄 소개 문장 + 표 + (필요시) 짧은 보충 한 문장 이내로 구성하세요.
"""

# Intent별 DB 스키마 (Text2SQL용)
SCHEMA_MAP = {
    "ETF": """
tiger_etf.etf_products (ksd_fund_code VARCHAR PK, ticker, name_ko, name_en, benchmark_index, category_l1, category_l2, total_expense_ratio NUMERIC, listing_date DATE, currency_hedge BOOLEAN, aum NUMERIC, nav NUMERIC, market_price NUMERIC, shares_outstanding BIGINT, is_active BOOLEAN)
tiger_etf.etf_holdings (ksd_fund_code VARCHAR FK→etf_products, as_of_date DATE, holding_name, holding_ticker, weight_pct NUMERIC, market_value NUMERIC)
tiger_etf.etf_performance (ksd_fund_code VARCHAR FK→etf_products, as_of_date DATE, return_1w, return_1m, return_3m, return_6m, return_1y, return_ytd NUMERIC)
tiger_etf.etf_distributions (ksd_fund_code VARCHAR FK→etf_products, record_date DATE, payment_date DATE, amount_per_share NUMERIC, distribution_rate NUMERIC)
""",
    "Bond": """
bond.bond_products (bond_code VARCHAR PK, name, issuer, issuer_type, coupon_rate NUMERIC, coupon_type, maturity_date DATE, issue_date DATE, credit_rating, face_value NUMERIC, issue_amount NUMERIC, currency, market, is_active BOOLEAN)
bond.bond_prices (bond_code VARCHAR FK→bond_products, trade_date DATE, yield_rate NUMERIC, clean_price NUMERIC, dirty_price NUMERIC, spread NUMERIC)
""",
    "Fund": """
fund.fund_products (fund_code VARCHAR PK, name, management_company, fund_type, sub_type, inception_date DATE, total_expense_ratio NUMERIC, aum NUMERIC, nav NUMERIC, benchmark, risk_grade INT, min_investment NUMERIC, currency, is_active BOOLEAN)
fund.fund_holdings (fund_code VARCHAR FK→fund_products, as_of_date DATE, holding_name, holding_ticker, asset_class, weight_pct NUMERIC, market_value NUMERIC)
fund.fund_performance (fund_code VARCHAR FK→fund_products, as_of_date DATE, return_1m, return_3m, return_6m, return_1y, return_3y, return_ytd, bm_return_1y NUMERIC)
""",
}

# Intent별 Few-shot SQL 예시
FEW_SHOT_MAP = {
    "ETF": """Q: AUM 상위 5개 ETF
SQL: SELECT name_ko, aum FROM tiger_etf.etf_products ORDER BY aum DESC LIMIT 5

Q: 반도체 ETF 보유종목
SQL: SELECT p.name_ko, h.holding_name, h.weight_pct FROM tiger_etf.etf_products p JOIN tiger_etf.etf_holdings h ON p.ksd_fund_code = h.ksd_fund_code WHERE p.category_l2 = '반도체' ORDER BY h.weight_pct DESC

Q: 배당 ETF 분배금 이력
SQL: SELECT p.name_ko, d.record_date, d.amount_per_share FROM tiger_etf.etf_products p JOIN tiger_etf.etf_distributions d ON p.ksd_fund_code = d.ksd_fund_code ORDER BY d.record_date DESC LIMIT 20
""",
    "Bond": """Q: AAA 등급 채권 목록
SQL: SELECT name, coupon_rate, credit_rating, issuer FROM bond.bond_products WHERE credit_rating = 'AAA' ORDER BY coupon_rate DESC

Q: 회사채 발행금액 순위
SQL: SELECT name, issuer, issue_amount FROM bond.bond_products WHERE issuer_type = '회사채' ORDER BY issue_amount DESC LIMIT 10

Q: 최근 수익률 변동 큰 채권
SQL: SELECT bp.bond_code, b.name, MAX(bp.yield_rate) - MIN(bp.yield_rate) as yield_range FROM bond.bond_prices bp JOIN bond.bond_products b ON bp.bond_code = b.bond_code GROUP BY bp.bond_code, b.name ORDER BY yield_range DESC LIMIT 10
""",
    "Fund": """Q: 주식형 펀드 수익률 상위 10개
SQL: SELECT fp.name, perf.return_1y FROM fund.fund_products fp JOIN fund.fund_performance perf ON fp.fund_code = perf.fund_code WHERE fp.fund_type = '주식형' ORDER BY perf.return_1y DESC LIMIT 10

Q: 총보수 1% 이하 펀드
SQL: SELECT name, fund_type, total_expense_ratio FROM fund.fund_products WHERE total_expense_ratio <= 1.0 ORDER BY total_expense_ratio ASC

Q: 벤치마크 대비 초과수익 펀드
SQL: SELECT fp.name, perf.return_1y, perf.bm_return_1y, (perf.return_1y - perf.bm_return_1y) as excess FROM fund.fund_products fp JOIN fund.fund_performance perf ON fp.fund_code = perf.fund_code WHERE perf.return_1y > perf.bm_return_1y ORDER BY excess DESC LIMIT 10
""",
}

# OpenCypher 그래프 스키마 (graphrag_toolkit 형식 - tenant가 라벨에 포함)
GRAPH_SCHEMA = {
    "ETF": {"tenant": "etf"},
    "Bond": {"tenant": "bond"},
    "Fund": {"tenant": "fund"},
}
