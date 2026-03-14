"""Token usage and cost calculation service."""

from backend.config import Config


def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pricing = Config.PRICING.get(model, {"input": 0, "output": 0})
    return tokens_in * pricing["input"] + tokens_out * pricing["output"]


def aggregate_token_usage(turns: list[dict], period: str = "daily") -> dict:
    """Aggregate token usage from turn records by period.

    Args:
        turns: List of DynamoDB turn items with total.tokens_in/out/cost.
        period: "daily", "weekly", or "monthly".

    Returns:
        {"period": period, "data": [...], "totals": {...}}
    """
    from collections import defaultdict
    from datetime import datetime

    buckets = defaultdict(lambda: {"tokens_in": 0, "tokens_out": 0, "cost": 0.0, "request_count": 0})
    total_in = 0
    total_out = 0
    total_cost = 0.0
    total_count = 0

    for turn in turns:
        ts = turn.get("timestamp", "")
        total = turn.get("total", {})
        t_in = total.get("tokens_in", 0)
        t_out = total.get("tokens_out", 0)
        cost = total.get("cost", 0.0)

        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue

        if period == "daily":
            key = dt.strftime("%Y-%m-%d")
        elif period == "weekly":
            key = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
        else:
            key = dt.strftime("%Y-%m")

        buckets[key]["tokens_in"] += t_in
        buckets[key]["tokens_out"] += t_out
        buckets[key]["cost"] += cost
        buckets[key]["request_count"] += 1

        total_in += t_in
        total_out += t_out
        total_cost += cost
        total_count += 1

    data = [{"period_key": k, **v} for k, v in sorted(buckets.items())]
    for item in data:
        item["cost"] = round(item["cost"], 6)

    return {
        "period": period,
        "data": data,
        "totals": {
            "tokens_in": total_in,
            "tokens_out": total_out,
            "cost": round(total_cost, 6),
            "request_count": total_count,
        },
    }
