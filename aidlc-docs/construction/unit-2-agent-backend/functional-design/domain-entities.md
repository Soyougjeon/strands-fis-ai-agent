# Domain Entities - Unit 2: Agent Backend

## DynamoDB Table (1테이블)

### conversation_turns (세션별 대화별 저장)
| Attribute | Type | Key | Description |
|-----------|------|-----|-------------|
| session_id | S | PK | 세션 ID (UUID) |
| turn_id | S | SK | 턴 ID (timestamp_seq, 시간순 정렬) |
| session_title | S | - | 대화 제목 (첫 질문 기반 자동 생성) |
| context_summary | S | - | 대화 요약 (멀티턴 컨텍스트용) |
| timestamp | S | - | 턴 시각 (ISO 8601) |
| question | S | - | 사용자 질문 |
| agent_process | M | - | Agent 실행 과정 (Map) |
| response | S | - | Agent 응답 |
| total | M | - | 총 latency/tokens/cost |

#### agent_process 구조 (Map)
```json
{
  "intent_detection": {
    "intent": "ETF",
    "confidence": 0.95,
    "latency": 0.3,
    "tokens_in": 120,
    "tokens_out": 15,
    "cost": 0.0004
  },
  "tool_selection": {
    "tool": "text2sql",
    "rationale": "수치 조회 질의",
    "latency": 0.2,
    "tokens_in": 85,
    "tokens_out": 20,
    "cost": 0.0003
  },
  "query_generation": {
    "query_type": "sql",
    "query": "SELECT ... FROM ...",
    "latency": 0.5,
    "tokens_in": 200,
    "tokens_out": 50,
    "cost": 0.001
  },
  "query_execution": {
    "result_summary": "10 rows returned",
    "raw_data": [...],
    "latency": 0.1
  },
  "response_generation": {
    "latency": 1.2,
    "tokens_in": 500,
    "tokens_out": 300,
    "cost": 0.006
  }
}
```

#### total 구조 (Map)
```json
{
  "latency": 2.3,
  "tokens_in": 905,
  "tokens_out": 385,
  "cost": 0.0077
}
```

---

## Pydantic Models (FastAPI)

### Request Models
```
ChatRequest:
  session_id: Optional[str]    # 없으면 새 세션 생성
  message: str

WebSocketMessage:
  type: "message" | "ping"
  session_id: Optional[str]
  message: str
```

### Response Models
```
ChatResponse:
  session_id: str
  turn_id: str
  response: str
  agent_process: AgentProcess
  total: TotalMetrics

AgentProcess:
  intent_detection: StepResult
  tool_selection: StepResult
  query_generation: QueryStepResult
  query_execution: ExecutionResult
  response_generation: StepResult

StepResult:
  latency: float
  tokens_in: int
  tokens_out: int
  cost: float

QueryStepResult(StepResult):
  query_type: str       # sql | cypher | vector | graphrag
  query: str

ExecutionResult:
  result_summary: str
  raw_data: Any
  graph_data: Optional[GraphData]
  chart_data: Optional[ChartData]
  latency: float

TotalMetrics:
  latency: float
  tokens_in: int
  tokens_out: int
  cost: float
```

### AgentEvent (WebSocket 스트리밍)
```
AgentEvent:
  type: str               # event type
  data: dict              # event-specific data
  timestamp: str

Event Types:
  - intent_detected: { intent, confidence, latency, tokens_in, tokens_out, cost }
  - tool_selected: { tool, rationale, latency, tokens_in, tokens_out, cost }
  - query_generated: { query_type, query, latency, tokens_in, tokens_out, cost }
  - query_executed: { result_summary, raw_data, graph_data, chart_data, latency }
  - text_chunk: { text }
  - response_complete: { total_latency, total_tokens_in, total_tokens_out, total_cost }
```

### Visualization Models
```
GraphData:
  nodes: List[GraphNode]
  edges: List[GraphEdge]

GraphNode:
  id: str
  label: str
  type: str
  properties: dict

GraphEdge:
  source: str
  target: str
  label: str
  properties: dict

ChartData:
  chart_type: str         # bar | line | pie | scatter
  title: str
  data: List[dict]
  x_axis: str
  y_axis: str
```

### Conversation Models
```
ConversationSummary:
  session_id: str
  title: str
  turn_count: int
  last_intent: str
  updated_at: str

ConversationDetail:
  session_id: str
  title: str
  turns: List[TurnDetail]

TurnDetail:
  turn_id: str
  timestamp: str
  question: str
  response: str
  agent_process: AgentProcess
  total: TotalMetrics

TokenUsageStats:
  period: str             # daily | weekly | monthly
  data: List[UsagePeriod]
  totals: UsageTotals

UsagePeriod:
  date: str
  tokens_in: int
  tokens_out: int
  cost: float
  request_count: int

UsageTotals:
  total_tokens_in: int
  total_tokens_out: int
  total_cost: float
  total_requests: int
```
