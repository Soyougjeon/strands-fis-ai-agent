# API Documentation

## REST APIs
이 시스템은 외부 REST API를 제공하지 않으며, CLI 기반 파이프라인으로 동작한다.

### External APIs Consumed (Mirae Asset Website)

#### ETF Category Tree
- **Method**: GET
- **Path**: `/tigeretf/getEtfTypeDataAll.ajax`
- **Purpose**: TIGER ETF 전체 카테고리 트리 조회
- **Response**: JSON - 카테고리 계층 (L1 대분류, L2 소분류)

#### ETF Products by Category
- **Method**: POST
- **Path**: `/tigeretf/getEtfTypeData.ajax`
- **Purpose**: 카테고리별 ETF 상품 목록 조회
- **Request**: `etfType={category_code}`
- **Response**: JSON - 상품 목록 (ticker, name, NAV, AUM, returns 등)

#### ETF Detail Page
- **Method**: GET
- **Path**: `/ko/product/search/detail/index.do?ksdFund={code}`
- **Purpose**: 개별 ETF 상세 정보 조회
- **Response**: HTML - 상품 상세 페이지

#### ETF Holdings (Excel)
- **Method**: POST
- **Path**: `/en/product/search/downloadPdfExcelTotal.do`
- **Purpose**: 전체 ETF 보유종목 엑셀 다운로드
- **Response**: XLS - 시트별 ETF 보유종목

#### ETF Distribution History
- **Method**: POST
- **Path**: `/ko/product/search/detail/refDivAjax.ajax`
- **Purpose**: 개별 ETF 분배금 지급 이력 조회
- **Request**: `ksdFund={code}`
- **Response**: HTML - 분배금 테이블

## Internal APIs (Python Interfaces)

### BaseScraper (scrapers/base.py)
- **Methods**:
  - `scrape(**kwargs) -> None` - 스크래핑 실행 (서브클래스 구현)
  - `start_run(scraper_name) -> ScrapeRun` - 실행 기록 시작
  - `finish_run(run, status, items_processed, items_failed, error_message)` - 실행 기록 완료
  - `_throttle()` - 요청 간 딜레이 적용
  - `_request_with_retry(method, url, **kwargs) -> httpx.Response` - 재시도 포함 HTTP 요청

### GraphRAG Indexer (graphrag/indexer.py)
- **Methods**:
  - `build_all(pdf_limit=None, rdb_limit=None) -> None` - PDF + RDB 전체 인덱싱
  - `build_from_pdfs(limit=None) -> None` - PDF만 인덱싱
  - `build_from_rdb(limit=None) -> None` - RDB만 인덱싱
  - `reset_all() -> None` - 그래프 + 벡터 스토어 초기화
  - `reset_graph() -> None` - Neptune 초기화
  - `reset_vector() -> None` - OpenSearch 초기화

### GraphRAG Loader (graphrag/loader.py)
- **Methods**:
  - `load_pdfs(limit=None) -> List[Document]` - PDF -> LlamaIndex 문서 로드
  - `load_rdb(limit=None) -> List[Document]` - RDB -> 자연어 문서 변환
  - `_product_to_document(session, product) -> Document` - EtfProduct -> Document 변환

### GraphRAG Query (graphrag/query.py)
- **Methods**:
  - `get_query_engine() -> LexicalGraphQueryEngine` - 질의 엔진 생성
  - `query(question: str) -> str` - 자연어 질의 실행
  - `get_graph_stats() -> dict` - Neptune 그래프 통계 (노드/엣지 수)

### GraphRAG Evaluator (graphrag/evaluator.py)
- **Methods**:
  - `load_eval_questions(path) -> List[EvalQuestion]` - 평가 질문 로드
  - `evaluate(questions, query_fn, use_llm_judge) -> EvalReport` - 전체 평가 실행
  - `compute_keyword_hit(response, keywords) -> float` - 키워드 히트율 계산
  - `compute_llm_judge(question, response) -> dict` - LLM-as-Judge 스코어 계산

### Database (db.py)
- **Methods**:
  - `get_session() -> Session` - Writer 세션 컨텍스트 매니저
  - `get_reader_session() -> Session` - Reader 세션 컨텍스트 매니저
  - `init_schema() -> None` - tiger_etf 스키마 + 테이블 생성

## Data Models

### EtfProduct
- **Fields**: ksd_fund_code (PK), ticker, name_ko, name_en, benchmark_index, category_l1, category_l2, total_expense_ratio, listed_on, aum, nav, market_price, shares_outstanding, creation_unit, currency_hedge, pension_individual, pension_retirement, bloomberg_ticker, is_active, raw_data (JSONB), created_at, updated_at
- **Relationships**: holdings (1:N), distributions (1:N), documents (1:N), performances (1:N), daily_prices (1:N)

### EtfHolding
- **Fields**: id (PK), ksd_fund_code (FK), as_of_date, holding_name, ticker, isin, weight_pct, shares, created_at
- **Unique Constraint**: (ksd_fund_code, as_of_date, holding_name)

### EtfPerformance
- **Fields**: id (PK), ksd_fund_code (FK), as_of_date, return_1w, return_1m, return_3m, return_6m, return_1y, return_3y, return_ytd, created_at
- **Unique Constraint**: (ksd_fund_code, as_of_date)

### EtfDistribution
- **Fields**: id (PK), ksd_fund_code (FK), record_date, payment_date, amount_per_share, distribution_rate, created_at
- **Unique Constraint**: (ksd_fund_code, record_date)

### EtfDocument
- **Fields**: id (PK), ksd_fund_code (FK), doc_type, source_url, local_path, file_hash (SHA256), file_size_bytes, published_date, downloaded_at, created_at
- **Unique Constraint**: (ksd_fund_code, doc_type, file_hash)

### EtfDailyPrice
- **Fields**: id (PK), ksd_fund_code (FK), trade_date, nav, market_price, volume, created_at
- **Unique Constraint**: (ksd_fund_code, trade_date)

### ScrapeRun
- **Fields**: id (PK), scraper_name, started_at, finished_at, status, items_processed, items_failed, error_message
