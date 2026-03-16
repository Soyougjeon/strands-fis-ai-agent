# Doc 5: Backend API & Agent Specification

## 1. API 엔드포인트

### 1.1 REST API

| Method | Path | 설명 | 요청 | 응답 |
|--------|------|------|------|------|
| POST | /api/chat | 동기 대화 | `ChatRequest` | `ChatResponse` |
| GET | /api/conversations | 대화 목록 | - | `ConversationSummary[]` |
| GET | /api/conversations/{id} | 대화 상세 | - | `ConversationDetail` |
| DELETE | /api/conversations/{id} | 대화 삭제 | - | 204 |
| GET | /api/visualize/graph | 그래프 데이터 | `?tenant=&query=` | `GraphData` |
| GET | /api/visualize/chart | 차트 데이터 | `?chart_type=&params=` | `ChartData` |
| GET | /api/admin/token-usage | 토큰 통계 | `?period=daily` | `TokenUsageStats` |
| GET | /api/admin/conversations | Admin 대화 | `?search=&page=` | `PaginatedConversations` |
| GET | /api/examples | 예시 쿼리 | - | `ExampleQueries` |
| GET | /api/health | 헬스체크 | - | `{"status": "ok"}` |

### 1.2 WebSocket

```
Endpoint: /ws/chat

Client → Server:
{
  "session_id": "uuid" | null,   // null이면 새 세션
  "message": "사용자 질문"
}

Server → Client (순서대로):
1. { "type": "intent_detected", "data": { "intent", "confidence", "latency", "tokens_in", "tokens_out", "cost" } }
2. { "type": "tool_selected",   "data": { "tool", "rationale", "latency", "tokens_in", "tokens_out", "cost" } }
3. { "type": "query_generated", "data": { "query_type", "query", "latency", "tokens_in", "tokens_out", "cost" } }
4. { "type": "query_executed",  "data": { "result_summary", "raw_data", "graph_data", "chart_data", "latency" } }
5. { "type": "text_chunk",      "data": { "text" } }  × N회 (스트리밍)
6. { "type": "response_complete","data": { "total_latency", "total_tokens_in", "total_tokens_out", "total_cost" } }
7. { "type": "session_info",    "data": { "session_id", "turn_id" } }
```

### 1.3 Pydantic 스키마

```python
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    turn_id: str
    response: str
    agent_process: AgentProcess
    total: TotalMetrics

class GraphData(BaseModel):
    nodes: list[GraphNode]    # { id, label, type, properties }
    edges: list[GraphEdge]    # { source, target, label, properties }

class ChartData(BaseModel):
    chart_type: str           # "bar" | "line" | "pie"
    title: str
    data: list[dict]
    x_axis: str
    y_axis: str
```

## 2. Agent 아키텍처

### 2.1 Agent Loop

```
process_message(message, context, tools)
  │
  ├─ Step 1+2: Intent + Tool Selection (단일 LLM 호출)
  │   └─ Bedrock converse() → JSON { intent, confidence, tool, rationale }
  │   └─ yield IntentDetectedEvent
  │   └─ yield ToolSelectedEvent
  │
  ├─ Step 3: Tool Execution
  │   └─ tools[tool_name].execute(message, intent)
  │   └─ yield QueryGeneratedEvent
  │   └─ yield QueryExecutedEvent
  │
  └─ Step 4: Response Generation (스트리밍)
      └─ Bedrock converse_stream() → 텍스트 청크
      └─ yield TextChunkEvent × N
      └─ yield ResponseCompleteEvent
```

### 2.2 Intent + Tool Selection 프롬프트

시스템 프롬프트로 Intent 분류와 Tool 선택을 동시에 수행한다:

```
[Step 1: Intent 분류]
- ETF: 상장지수펀드 관련
- Bond: 채권, 금리, 신용등급 관련
- Fund: 공모펀드, 운용사 관련

[Step 2: Tool 선택]
1. text2sql: 수치 조회, 필터링, 집계 → SQL
2. rag: 비정형 문서 검색, 설명, 전략 → 벡터 검색
3. graphrag: 관계 탐색, 공통점, 네트워크 → 지식그래프+벡터
4. opencypher: 그래프 직접 쿼리, 홉 탐색 → Neptune

응답 형식: {"intent": "...", "confidence": 0.0~1.0, "tool": "...", "rationale": "..."}
```

### 2.3 Response Generation 프롬프트

Tool 실행 결과를 기반으로 최종 응답을 생성한다:

```
입력: 대화 요약 + 최근 대화 + 질문 + Tool 결과 (tool_name, query, result_summary, raw_data)
규칙: 한국어, 마크다운 표, 숫자 천단위 구분, 간결한 답변
```

## 3. Tool 인터페이스

### 3.1 공통 반환 타입 (ToolResult)

모든 Tool은 동일한 구조를 반환한다:

```python
{
    "query_step": {              # QueryGeneratedEvent용
        "query_type": "sql",     # sql | knn | graphrag | cypher
        "query": "SELECT ...",   # 실행된 쿼리
        "latency": 0.4,
        "tokens_in": 100,
        "tokens_out": 50,
        "cost": 0.0003
    },
    "execution": {               # QueryExecutedEvent용
        "result_summary": "5건 조회",
        "raw_data": [...],       # 쿼리 결과
        "graph_data": null,      # GraphData (opencypher/graphrag만)
        "chart_data": null,      # ChartData (text2sql만)
        "latency": 0.05
    }
}
```

### 3.2 Text2SQL Tool (`tools/text2sql.py`)

```
입력: question(str), intent(str)
동작: LLM으로 SQL 생성 → Aurora PG 실행 → 결과 + chart_data 반환
의존: Aurora PostgreSQL, Bedrock (SQL 생성)
커스터마이징: SCHEMA_MAP, FEW_SHOT_MAP (prompts.py)
```

### 3.3 RAG Tool (`tools/rag.py`)

```
입력: question(str), intent(str)
동작: Titan Embed로 질의 임베딩 → OpenSearch kNN 검색 → top-K 청크 반환
의존: OpenSearch Serverless, Bedrock Titan
커스터마이징: 인덱스명 매핑 (intent → rag-{domain})
```

### 3.4 GraphRAG Tool (`tools/graphrag.py`)

```
입력: question(str), intent(str)
동작: LexicalGraphQueryEngine 실행 → 벡터+그래프 결합 결과 반환
의존: Neptune DB, OpenSearch Serverless, Bedrock
커스터마이징: 테넌트명 매핑 (intent → {domain} tenant)
```

### 3.5 OpenCypher Tool (`tools/opencypher.py`)

```
입력: question(str), intent(str)
동작: LLM으로 Cypher 생성 → Neptune 실행 → graph_data 반환
의존: Neptune DB, Bedrock (Cypher 생성)
커스터마이징: OPENCYPHER_PROMPT_TEMPLATE (prompts.py), 그래프 스키마
```

## 4. Config 설정

```python
class Config:
    # Aurora PostgreSQL
    DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_URL

    # Neptune
    NEPTUNE_ENDPOINT, NEPTUNE_PORT

    # OpenSearch Serverless
    OPENSEARCH_ENDPOINT

    # AWS
    AWS_REGION = "us-east-1"

    # Bedrock
    LLM_MODEL_ID = "us.anthropic.claude-sonnet-4-6-v1:0"
    EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
    EMBEDDING_DIMENSION = 1024

    # DynamoDB
    DYNAMODB_TABLE = "conversation_turns"

    # Agent
    MAX_CONTEXT_TURNS = 3              # 최근 N턴 컨텍스트
    SUMMARY_REFRESH_INTERVAL = 3       # N턴마다 요약 갱신
    MAX_SUMMARY_LENGTH = 500

    # SQL Safety
    SQL_TIMEOUT_SECONDS = 10
    SQL_MAX_ROWS = 1000

    # Token Pricing (USD per token)
    PRICING = {
        "claude-sonnet": {"input": 3.00/1M, "output": 15.00/1M},
        "titan-embed-v2": {"input": 0.02/1M, "output": 0},
    }
```

## 5. 도메인 커스터마이징 가이드

### 5.1 Intent 추가/변경

`agent/prompts.py`의 `INTENT_AND_TOOL_PROMPT`에서:

```python
# 변경 전
- ETF: TIGER ETF, 상장지수펀드 ...
- Bond: 채권, 국채 ...
- Fund: 공모펀드 ...

# 변경 후 (예: 보험 도메인)
- Insurance: 보험상품, 보장내용, 보험료 ...
- Claim: 보험금 청구, 사고접수 ...
- Policy: 약관, 특약, 면책조항 ...
```

### 5.2 Text2SQL 스키마 매핑

`agent/prompts.py`의 `SCHEMA_MAP`에서:

```python
SCHEMA_MAP = {
    "Insurance": """
    insurance.products (product_id PK, name, type, premium NUMERIC, ...)
    insurance.coverages (product_id FK, coverage_name, amount NUMERIC, ...)
    """,
    ...
}
```

### 5.3 OpenCypher 스키마

`agent/prompts.py`의 `OPENCYPHER_PROMPT_TEMPLATE`에서 그래프 구조, 관계 방향, 예시 쿼리를 도메인에 맞게 수정.

### 5.4 Few-shot 예시

`agent/prompts.py`의 `FEW_SHOT_MAP`에서 도메인별 SQL 예시 3~5개 작성.
