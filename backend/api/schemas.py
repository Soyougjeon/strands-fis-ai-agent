from typing import Any, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class StepResult(BaseModel):
    latency: float = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0


class QueryStepResult(StepResult):
    query_type: str = ""
    query: str = ""


class ExecutionResult(BaseModel):
    result_summary: str = ""
    raw_data: Any = None
    graph_data: Optional["GraphData"] = None
    chart_data: Optional["ChartData"] = None
    latency: float = 0


class AgentProcess(BaseModel):
    intent_detection: Optional[StepResult] = None
    tool_selection: Optional[StepResult] = None
    query_generation: Optional[QueryStepResult] = None
    query_execution: Optional[ExecutionResult] = None
    response_generation: Optional[StepResult] = None


class TotalMetrics(BaseModel):
    latency: float = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0


class ChatResponse(BaseModel):
    session_id: str
    turn_id: str
    response: str
    agent_process: AgentProcess
    total: TotalMetrics


class AgentEvent(BaseModel):
    type: str
    data: dict = {}
    timestamp: str = ""


class GraphNode(BaseModel):
    id: str
    label: str
    type: str = ""
    properties: dict = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = ""
    properties: dict = {}


class GraphData(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []


class ChartData(BaseModel):
    chart_type: str = "bar"
    title: str = ""
    data: list[dict] = []
    x_axis: str = ""
    y_axis: str = ""


class ConversationSummary(BaseModel):
    session_id: str
    title: str = ""
    turn_count: int = 0
    last_intent: str = ""
    updated_at: str = ""


class ConversationDetail(BaseModel):
    session_id: str
    title: str = ""
    turns: list[dict] = []


class TokenUsageStats(BaseModel):
    period: str
    data: list[dict] = []
    totals: dict = {}


class ErrorResponse(BaseModel):
    error: dict
