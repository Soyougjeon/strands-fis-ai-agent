"""Conversations API routes - CRUD for conversation history."""

from fastapi import APIRouter, HTTPException

from backend.services.conversation import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
async def list_conversations():
    """List all conversation sessions."""
    service = ConversationService()
    sessions = service.list_sessions()
    return {"conversations": sessions}


@router.get("/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation detail with all turns."""
    service = ConversationService()
    session = service.get_session(session_id)
    if not session.get("turns"):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return session


@router.delete("/{session_id}")
async def delete_conversation(session_id: str):
    """Delete a conversation session and all its turns."""
    service = ConversationService()
    count = service.delete_session(session_id)
    if count == 0:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return {"deleted": count, "session_id": session_id}
