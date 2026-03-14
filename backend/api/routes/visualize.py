"""Visualization API routes - graph and chart data endpoints."""

from fastapi import APIRouter, HTTPException

from backend.services.conversation import ConversationService

router = APIRouter(prefix="/api/visualize", tags=["visualize"])


@router.get("/graph/{session_id}/{turn_id}")
async def get_graph(session_id: str, turn_id: str):
    """Get graph data for a specific turn."""
    service = ConversationService()
    session = service.get_session(session_id)

    for turn in session.get("turns", []):
        if turn.get("turn_id") == turn_id:
            exec_data = turn.get("agent_process", {}).get("query_execution", {})
            graph_data = exec_data.get("graph_data")
            if graph_data:
                return graph_data
            raise HTTPException(status_code=404, detail="해당 턴에 그래프 데이터가 없습니다.")

    raise HTTPException(status_code=404, detail="턴을 찾을 수 없습니다.")


@router.get("/chart/{session_id}/{turn_id}")
async def get_chart(session_id: str, turn_id: str):
    """Get chart data for a specific turn."""
    service = ConversationService()
    session = service.get_session(session_id)

    for turn in session.get("turns", []):
        if turn.get("turn_id") == turn_id:
            exec_data = turn.get("agent_process", {}).get("query_execution", {})
            chart_data = exec_data.get("chart_data")
            if chart_data:
                return chart_data
            raise HTTPException(status_code=404, detail="해당 턴에 차트 데이터가 없습니다.")

    raise HTTPException(status_code=404, detail="턴을 찾을 수 없습니다.")
