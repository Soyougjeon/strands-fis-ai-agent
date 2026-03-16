import json
from datetime import datetime, timezone
from decimal import Decimal


def _default_serializer(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def make_event(event_type: str, data: dict) -> str:
    event = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(event, ensure_ascii=False, default=_default_serializer)


def intent_detected_event(intent: str, confidence: float, latency: float,
                          tokens_in: int, tokens_out: int, cost: float) -> str:
    return make_event("intent_detected", {
        "intent": intent,
        "confidence": confidence,
        "latency": latency,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost": cost,
    })


def tool_selected_event(tool: str, rationale: str, latency: float,
                        tokens_in: int, tokens_out: int, cost: float) -> str:
    return make_event("tool_selected", {
        "tool": tool,
        "rationale": rationale,
        "latency": latency,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost": cost,
    })


def query_generated_event(query_type: str, query: str, latency: float,
                          tokens_in: int, tokens_out: int, cost: float,
                          **extra) -> str:
    data = {
        "query_type": query_type,
        "query": query,
        "latency": latency,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost": cost,
    }
    data.update(extra)
    return make_event("query_generated", data)


def query_executed_event(result_summary: str, raw_data, graph_data=None,
                         chart_data=None, lexical_graph_data=None,
                         latency: float = 0,
                         est_tokens_in: int = 0, est_tokens_out: int = 0) -> str:
    return make_event("query_executed", {
        "result_summary": result_summary,
        "raw_data": raw_data,
        "graph_data": graph_data,
        "chart_data": chart_data,
        "lexical_graph_data": lexical_graph_data,
        "latency": latency,
        "est_tokens_in": est_tokens_in,
        "est_tokens_out": est_tokens_out,
    })


def text_chunk_event(text: str) -> str:
    return make_event("text_chunk", {"text": text})


def response_complete_event(total_latency: float, total_tokens_in: int,
                            total_tokens_out: int, total_cost: float,
                            resp_latency: float = 0, resp_tokens_in: int = 0,
                            resp_tokens_out: int = 0, resp_cost: float = 0,
                            resp_estimated: bool = False) -> str:
    return make_event("response_complete", {
        "total_latency": total_latency,
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_cost": total_cost,
        "resp_latency": resp_latency,
        "resp_tokens_in": resp_tokens_in,
        "resp_tokens_out": resp_tokens_out,
        "resp_cost": resp_cost,
        "resp_estimated": resp_estimated,
    })
