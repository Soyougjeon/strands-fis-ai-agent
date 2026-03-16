// Agent Event Types (WebSocket)
export type EventType =
  | "intent_detected"
  | "tool_selected"
  | "query_generated"
  | "query_executed"
  | "text_chunk"
  | "response_complete"
  | "session_info"
  | "error";

export interface AgentEvent {
  type: EventType;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface IntentDetectedData {
  intent: "ETF" | "Bond" | "Fund";
  confidence: number;
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

export interface ToolSelectedData {
  tool: "text2sql" | "rag" | "graphrag" | "opencypher";
  rationale: string;
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

export interface QueryGeneratedData {
  query_type: string;
  query: string;
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

export interface QueryExecutedData {
  result_summary: string;
  raw_data: unknown;
  graph_data: GraphData | null;
  chart_data: ChartData | null;
  lexical_graph_data: GraphData | null;
  latency: number;
}

export interface ResponseCompleteData {
  total_latency: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_cost: number;
  resp_latency: number;
  resp_tokens_in: number;
  resp_tokens_out: number;
  resp_cost: number;
}

// Visualization
export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  label: string;
  properties: Record<string, unknown>;
}

export interface ChartData {
  chart_type: "bar" | "line" | "pie";
  title: string;
  data: Record<string, unknown>[];
  x_axis: string;
  y_axis: string;
}

// Conversation
export interface ConversationSummary {
  session_id: string;
  title: string;
  turn_count: number;
  last_intent: string;
  updated_at: string;
}

export interface ConversationDetail {
  session_id: string;
  title: string;
  turns: Turn[];
}

export interface Turn {
  turn_id: string;
  timestamp: string;
  question: string;
  response: string;
  intent: string;
  agent_process: AgentProcess;
  total: TotalMetrics;
}

// Agent Process
export interface StepMetrics {
  [key: string]: unknown;
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

export interface QueryStepMetrics extends StepMetrics {
  query_type: string;
  query: string;
}

export interface ExecutionResult {
  result_summary: string;
  raw_data: unknown;
  graph_data: GraphData | null;
  chart_data: ChartData | null;
  latency: number;
}

export interface AgentProcess {
  intent_detection: (StepMetrics & { intent?: string; confidence?: number }) | null;
  tool_selection: (StepMetrics & { tool?: string; rationale?: string }) | null;
  query_generation: QueryStepMetrics | null;
  query_execution: ExecutionResult | null;
  response_generation: StepMetrics | null;
}

export interface TotalMetrics {
  latency: number;
  tokens_in: number;
  tokens_out: number;
  cost: number;
}

// Chat Message
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agentProcess?: AgentProcess;
  total?: TotalMetrics;
  chartData?: ChartData;
  graphData?: GraphData;
  lexicalGraphData?: GraphData;
  rawData?: unknown;
  timestamp: string;
}

// Admin
export interface TokenUsageStats {
  period: "daily" | "weekly" | "monthly";
  data: TokenUsageBucket[];
  totals: TotalMetrics & { request_count: number };
}

export interface TokenUsageBucket {
  period_key: string;
  tokens_in: number;
  tokens_out: number;
  cost: number;
  request_count: number;
}

// Example Queries
export interface ExampleQueries {
  domains: Record<string, Record<string, ExampleQuery[]>>;
}

export interface ExampleQuery {
  question: string;
  description: string;
}
