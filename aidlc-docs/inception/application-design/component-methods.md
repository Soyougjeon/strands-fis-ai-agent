# Component Methods

## C2: API Server (FastAPI)

### Chat Endpoints
- `POST /api/chat(request: ChatRequest) -> ChatResponse` - 동기 대화 (비스트리밍)
- `WebSocket /ws/chat` - 스트리밍 대화 (Agent 실행 과정 포함)

### Conversation Endpoints
- `GET /api/conversations() -> List[ConversationSummary]` - 대화 목록
- `GET /api/conversations/{id}() -> ConversationDetail` - 대화 상세
- `DELETE /api/conversations/{id}() -> None` - 대화 삭제

### Visualization Endpoints
- `GET /api/visualize/graph(tenant: str, query: str) -> GraphData` - 그래프 시각화 데이터
- `GET /api/visualize/chart(chart_type: str, params: dict) -> ChartData` - 차트 데이터

### Admin Endpoints
- `GET /api/admin/token-usage(period: str) -> TokenUsageStats` - 토큰 사용량/비용 통계
- `GET /api/admin/conversations(search: str, page: int) -> PaginatedConversations` - Admin 대화 관리

### Example Endpoints
- `GET /api/examples() -> Dict[str, List[ExampleQuery]]` - 예시 쿼리 (ETF/채권/펀드별)

---

## C3: Agent Engine (Orchestrator)

### Core Methods
- `create_agent(model_id: str) -> Agent` - Strands Agent 인스턴스 생성
- `process_message(session_id: str, message: str) -> AsyncGenerator[AgentEvent]` - 메시지 처리 + 스트리밍
- `detect_intent(message: str) -> IntentResult` - Intent 분류 (ETF/Bond/Fund)
- `select_tool(intent: str, message: str) -> ToolSelection` - Tool 선택
- `get_session_context(session_id: str) -> List[Message]` - 세션 대화 컨텍스트 조회

### AgentEvent Types (스트리밍)
- `IntentDetectedEvent(intent, confidence, latency, tokens, cost)`
- `ToolSelectedEvent(tool_name, rationale, latency, tokens, cost)`
- `QueryGeneratedEvent(query_type, query_text, latency, tokens, cost)`
- `QueryExecutedEvent(result_summary, raw_data, latency)`
- `TextChunkEvent(text)` - 스트리밍 텍스트 청크
- `ResponseCompleteEvent(total_latency, total_tokens, total_cost)`

---

## C4a: Text2SQL Tool

- `execute(question: str, intent: str) -> ToolResult` - 자연어 -> SQL 실행
- `generate_sql(question: str, schema_info: str) -> str` - SQL 생성 (LLM)
- `execute_query(sql: str) -> List[dict]` - Aurora PG 쿼리 실행
- `get_schema_info(intent: str) -> str` - 테이블 스키마 정보 (ETF/Bond/Fund별)

## C4b: RAG Tool

- `execute(question: str, intent: str) -> ToolResult` - 벡터 검색 실행
- `embed_query(question: str) -> List[float]` - 질의 임베딩 (Titan v2)
- `search(embedding: List[float], index: str, top_k: int) -> List[SearchResult]` - OpenSearch kNN 검색

## C4c: GraphRAG Tool

- `execute(question: str, intent: str) -> ToolResult` - GraphRAG 질의 실행
- `get_query_engine(tenant: str) -> LexicalGraphQueryEngine` - 테넌트별 엔진 생성
- `query(engine, question: str) -> GraphRAGResult` - 질의 실행 + 중간 단계 수집

## C4d: OpenCypher Tool

- `execute(question: str, intent: str) -> ToolResult` - 자연어 -> OpenCypher 실행
- `generate_cypher(question: str, schema_info: str) -> str` - Cypher 생성 (LLM)
- `execute_cypher(cypher: str, tenant: str) -> CypherResult` - Neptune 쿼리 실행
- `to_graph_data(result: CypherResult) -> GraphData` - 시각화용 변환

### ToolResult (공통 반환 타입)
```
ToolResult:
  tool_name: str
  query: str                    # 실행된 쿼리 (SQL/Cypher/검색어)
  raw_data: Any                 # 원시 결과 데이터
  summary: str                  # 결과 요약
  graph_data: Optional[GraphData]  # 시각화 데이터 (OpenCypher/GraphRAG)
  chart_data: Optional[ChartData]  # 차트 데이터 (Text2SQL)
  metadata: ToolMetadata        # latency, tokens_in, tokens_out, cost
```

---

## C5: Conversation Manager

- `create_session() -> str` - 새 대화 세션 생성, session_id 반환
- `add_message(session_id: str, role: str, content: str, metadata: dict) -> Message` - 메시지 저장
- `get_session(session_id: str) -> ConversationDetail` - 세션 상세 조회
- `list_sessions(page: int, size: int) -> PaginatedConversations` - 세션 목록
- `delete_session(session_id: str) -> None` - 세션 삭제
- `search_sessions(query: str) -> List[ConversationSummary]` - 세션 검색

---

## C6: Token Tracker

- `record_usage(session_id: str, message_id: str, step: str, model: str, tokens_in: int, tokens_out: int) -> None` - 사용량 기록
- `calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float` - 비용 계산
- `get_usage_stats(period: str) -> TokenUsageStats` - 기간별 통계 (daily/weekly/monthly)
- `get_message_usage(message_id: str) -> List[StepUsage]` - 메시지별 단계별 사용량

### StepUsage
```
StepUsage:
  step: str         # intent_detection, tool_selection, query_generation, response_generation
  model: str
  tokens_in: int
  tokens_out: int
  cost: float
  latency: float
```

---

## C7: Mock Data Pipeline

- `generate_etf_mock(count: int) -> None` - ETF Mock CSV 생성
- `generate_bond_mock(count: int) -> None` - 채권 Mock CSV 생성
- `generate_fund_mock(count: int) -> None` - 펀드 Mock CSV 생성
- `generate_md_files(intent: str) -> None` - MD 파일 생성 (GraphRAG/RAG용)
- `load_csv_to_db(csv_path: str, table: str) -> None` - CSV -> Aurora PG INSERT
- `index_graphrag(md_dir: str, tenant: str) -> None` - MD -> GraphRAG 인덱싱 (Neptune 멀티테넌시)
- `index_rag(md_dir: str, index_name: str) -> None` - MD -> RAG 인덱싱 (OpenSearch 벡터)
- `run_all() -> None` - 전체 파이프라인 실행

---

## C8: Frontend (React SPA)

### Pages/Routes
- `/` - Chat 탭 (기본)
- `/graph` - Graph Network 탭
- `/admin` - Admin 탭

### Key Components
- `App` - 상단 탭 네비게이션
- `CoggleSidebar` - 접기/펼치기 사이드바 (대화 이력 + 예시 쿼리)
- `ChatPanel` - 대화 메시지 표시 + 입력
- `AgentProcessPanel` - 실행 과정 (단계별 시간/토큰/비용)
- `DetailTabs` - 상세 탭 (OpenCypher/OpenSearch/GraphRAG/SQL/결과)
- `DynamicChart` - ECharts/Plotly 동적 차트 렌더링
- `GraphNetwork` - Cytoscape.js 그래프 네트워크
- `GraphNetworkPage` - 테넌트별 서브탭 [ETF][채권][펀드]
- `AdminDashboard` - 토큰 사용량/비용, 대화 이력, 통계
- `MarkdownRenderer` - 마크다운 + 코드 하이라이팅
