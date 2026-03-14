"""Admin API routes - token usage stats and conversation management."""

from fastapi import APIRouter, Query

from backend.services.conversation import ConversationService
from backend.services.token_tracker import aggregate_token_usage

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/token-usage")
async def get_token_usage(
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get aggregated token usage statistics."""
    service = ConversationService()
    turns = service.get_all_turns(start_date=start_date, end_date=end_date)
    stats = aggregate_token_usage(turns, period)
    return stats


@router.get("/conversations")
async def admin_conversations():
    """Admin view of all conversations with full metrics."""
    service = ConversationService()
    sessions = service.list_sessions()
    return {"conversations": sessions, "total_count": len(sessions)}
