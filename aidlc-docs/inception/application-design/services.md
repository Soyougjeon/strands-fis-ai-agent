# Service Definitions

## Service Architecture

```
+------------------------------------------------------------------+
|                    Service Layer                                   |
|                                                                    |
|  +------------------------------------------------------------+  |
|  | S1: Chat Service                                            |  |
|  | (API -> Agent -> Tools -> Response)                         |  |
|  +------------------------------------------------------------+  |
|       |              |              |              |               |
|       v              v              v              v               |
|  +----------+  +-----------+  +----------+  +------------+       |
|  | S2: Agent|  | S3: Data  |  | S4: Conv |  | S5: Token  |       |
|  | Service  |  | Access    |  | Service  |  | Service    |       |
|  +----------+  | Service   |  +----------+  +------------+       |
|                 +-----------+                                     |
|                 | S3a: SQL  |                                     |
|                 | S3b: RAG  |                                     |
|                 | S3c: Graph|                                     |
|                 | S3d: Cypher                                     |
|                 +-----------+                                     |
+------------------------------------------------------------------+
```

---

## S1: Chat Service

- **Purpose**: 대화 요청의 전체 흐름 조율 (Entry Point)
- **Responsibilities**:
  - WebSocket 연결에서 사용자 메시지 수신
  - Agent Service 호출
  - 스트리밍 이벤트를 WebSocket으로 전달
  - Conversation Service로 메시지 저장
  - Token Service로 사용량 기록
- **Interactions**:
  - -> S2 (Agent Service): 메시지 처리 요청
  - -> S4 (Conversation Service): 메시지 영구 저장
  - -> S5 (Token Service): 토큰 사용량 기록
- **Orchestration Pattern**: Event-Driven Streaming

```
WebSocket Message
  |
  v
S1: Chat Service
  |-- S4.create_session() (신규 시)
  |-- S4.get_session_context() (기존 시)
  |-- S2.process_message() -> AsyncGenerator[AgentEvent]
  |   |-- for each event:
  |   |   |-- WebSocket.send(event)       (실시간 전달)
  |   |   |-- S5.record_usage(event)      (토큰 기록)
  |-- S4.add_message() (최종 저장)
```

---

## S2: Agent Service

- **Purpose**: Strands Agent 관리 및 실행
- **Responsibilities**:
  - Agent 인스턴스 생성/관리
  - Intent Detection 실행
  - Tool Selection 및 실행 위임
  - 멀티턴 컨텍스트 관리
  - 실행 과정 이벤트 생성
- **Interactions**:
  - -> S3 (Data Access Service): Tool 실행 위임
  - -> Bedrock: LLM 호출 (Intent Detection, Response Generation)
- **Orchestration Pattern**: Agent Loop (Strands SDK)

```
S2.process_message(session_id, message)
  |
  |-- detect_intent(message) -> IntentDetectedEvent
  |-- select_tool(intent, message) -> ToolSelectedEvent
  |-- S3.execute_tool(tool, question, intent) -> ToolResult
  |   |-- QueryGeneratedEvent
  |   |-- QueryExecutedEvent
  |-- generate_response(context + tool_result) -> TextChunkEvents
  |-- ResponseCompleteEvent
```

---

## S3: Data Access Service

- **Purpose**: 4가지 데이터 접근 방식 통합 관리
- **Responsibilities**:
  - Tool별 실행 위임
  - 테넌트 라우팅 (Intent -> 해당 DB 인덱스/테넌트)
  - 결과 정규화 (ToolResult 공통 형식)
- **Sub-Services**:

### S3a: SQL Access Service
- Text2SQL Tool 래핑
- Intent별 스키마 매핑 (ETF -> tiger_etf.*, Bond -> bond_*, Fund -> fund_*)
- SQL 생성 + 실행 + 결과 반환

### S3b: RAG Access Service
- RAG Tool 래핑
- Intent별 인덱스 매핑 (ETF -> rag-etf, Bond -> rag-bond, Fund -> rag-fund)
- 벡터 검색 + 결과 반환

### S3c: GraphRAG Access Service
- GraphRAG Tool 래핑
- Intent별 테넌트 매핑 (ETF -> etf tenant, Bond -> bond tenant, Fund -> fund tenant)
- LexicalGraph 질의 + 결과 반환

### S3d: OpenCypher Access Service
- OpenCypher Tool 래핑
- Intent별 테넌트 매핑
- Cypher 생성 + Neptune 실행 + 그래프 데이터 반환

---

## S4: Conversation Service

- **Purpose**: 대화 이력 CRUD 및 검색
- **Responsibilities**:
  - 세션 생성/조회/삭제
  - 메시지 저장 (role, content, metadata)
  - 대화 검색
  - Admin 대화 관리
- **Interactions**:
  - -> Aurora PostgreSQL: conversations, messages 테이블

---

## S5: Token Service

- **Purpose**: 토큰 사용량 추적 및 비용 계산
- **Responsibilities**:
  - 단계별 토큰 기록 (input/output)
  - 모델별 비용 계산
  - 통계 집계 (일별, 누적, 모델별)
  - Admin 대시보드 데이터 제공
- **Interactions**:
  - -> Aurora PostgreSQL: token_usage 테이블

---

## S6: Visualization Service

- **Purpose**: 시각화 데이터 생성
- **Responsibilities**:
  - Neptune 그래프 데이터를 Cytoscape.js 형식으로 변환
  - SQL 결과를 차트 데이터 형식으로 변환
  - 테넌트별 그래프 조회
- **Interactions**:
  - -> Neptune DB: 그래프 데이터 조회
  - -> Aurora PG: 차트 데이터 조회

---

## S7: Mock Data Service

- **Purpose**: Mock 데이터 생성 및 적재 파이프라인
- **Responsibilities**:
  - CSV/MD 파일 생성
  - DB 적재
  - GraphRAG/RAG 인덱싱 실행
- **Interactions**:
  - -> Aurora PostgreSQL: CSV INSERT
  - -> Neptune DB: GraphRAG 인덱싱 (멀티테넌시)
  - -> OpenSearch: RAG 벡터 인덱싱
  - -> Bedrock (Titan): 임베딩 생성
