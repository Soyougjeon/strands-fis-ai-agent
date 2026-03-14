# Domain Entities - Unit 3: Frontend

## 1. TypeScript Type Definitions

### 1.1 Agent Event Types (WebSocket 수신)

```typescript
// 서버에서 수신하는 이벤트 기본 구조
interface AgentEvent {
  type: EventType;
  data: Record<string, unknown>;
  timestamp: string;
}

type EventType =
  | "intent_detected"
  | "tool_selected"
  | "query_generated"
  | "query_executed"
  | "text_chunk"
  | "response_complete"
  | "session_info"
  | "error";

// Step별 이벤트 데이터
interface IntentDetectedData {
  intent: "ETF" | "Bond" | "Fund";
  confidence: number;
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

interface ToolSelectedData {
  tool: "text2sql" | "rag" | "graphrag" | "opencypher";
  rationale: string;
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

interface QueryGeneratedData {
  query_type: string;
  query: string;
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

interface QueryExecutedData {
  result_summary: string;
  raw_data: unknown;
  graph_data: GraphData | null;
  chart_data: ChartData | null;
  latency: number;
}

interface ResponseCompleteData {
  total_latency: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_cost: number;
}
```

### 1.2 시각화 모델

```typescript
// 그래프 시각화 (Cytoscape.js)
interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
  properties: Record<string, unknown>;
}

// 차트 시각화 (ECharts)
interface ChartData {
  chart_type: "bar" | "line" | "pie";
  title: string;
  data: Record<string, unknown>[];
  x_axis: string;
  y_axis: string;
}
```

### 1.3 대화 모델

```typescript
// 대화 세션
interface ConversationSummary {
  session_id: string;
  title: string;
  turn_count: number;
  last_intent: string;
  updated_at: string;
}

// 대화 상세
interface ConversationDetail {
  session_id: string;
  title: string;
  turns: Turn[];
}

// 개별 턴
interface Turn {
  turn_id: string;
  timestamp: string;
  question: string;
  response: string;
  intent: string;
  agent_process: AgentProcess;
  total: TotalMetrics;
}

interface AgentProcess {
  intent_detection: StepMetrics | null;
  tool_selection: StepMetrics | null;
  query_generation: QueryStepMetrics | null;
  query_execution: ExecutionResult | null;
  response_generation: StepMetrics | null;
}

interface StepMetrics {
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

interface QueryStepMetrics extends StepMetrics {
  query_type: string;
  query: string;
}

interface ExecutionResult {
  result_summary: string;
  raw_data: unknown;
  graph_data: GraphData | null;
  chart_data: ChartData | null;
  latency: number;
}

interface TotalMetrics {
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}
```

### 1.4 Admin 모델

```typescript
// 토큰 사용량 통계
interface TokenUsageStats {
  period: "daily" | "weekly" | "monthly";
  data: TokenUsageBucket[];
  totals: TotalMetrics & { request_count: number };
}

interface TokenUsageBucket {
  period_key: string;
  tokens_in: number;
  tokens_out: number;
  cost: number;
  request_count: number;
}
```

### 1.5 예시 쿼리 모델

```typescript
interface ExampleQueries {
  domains: {
    [domain: string]: {
      [tool: string]: ExampleQuery[];
    };
  };
}

interface ExampleQuery {
  question: string;
  description: string;
}
```

## 2. UI State 모델

```typescript
// 앱 전역 상태
interface AppState {
  activeTab: "chat" | "graph" | "admin";
  sidebarOpen: boolean;
  currentSessionId: string | null;
  conversations: ConversationSummary[];
  examples: ExampleQueries | null;
}

// Chat 상태
interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  currentAgentProcess: Partial<AgentProcess>;
  currentTotal: TotalMetrics | null;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentProcess?: AgentProcess;
  total?: TotalMetrics;
  chartData?: ChartData;
  graphData?: GraphData;
  rawData?: unknown;
  timestamp: string;
}

// Graph Network 상태
interface GraphState {
  activeTenant: "ETF" | "Bond" | "Fund";
  graphData: GraphData | null;
  loading: boolean;
  selectedNode: GraphNode | null;
}

// Admin 상태
interface AdminState {
  tokenUsage: TokenUsageStats | null;
  conversations: ConversationSummary[];
  selectedPeriod: "daily" | "weekly" | "monthly";
}
```
