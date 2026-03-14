"""Chat API routes - POST /api/chat + WebSocket /ws/chat."""

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.api.schemas import ChatRequest
from backend.services.chat_service import ChatService

router = APIRouter()


@router.post("/api/chat")
async def chat_sync(request: ChatRequest):
    """Synchronous chat endpoint (non-streaming)."""
    service = ChatService()

    events = []
    async for event in service.handle_message(request.session_id, request.message):
        events.append(json.loads(event))

    result = service.agent_service.get_last_result()
    return {
        "session_id": service._last_session_id,
        "turn_id": service._last_turn_id,
        "response": result.get("response", ""),
        "agent_process": result.get("agent_process", {}),
        "total": result.get("total", {}),
    }


@router.websocket("/ws/chat")
async def chat_stream(websocket: WebSocket):
    """WebSocket streaming chat endpoint."""
    await websocket.accept()
    service = ChatService()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            session_id = msg.get("session_id")
            message = msg.get("message", "")

            if not message:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "메시지가 비어있습니다."},
                }))
                continue

            async for event in service.handle_message(session_id, message):
                await websocket.send_text(event)

            # Send session_id back if new session
            if hasattr(service, "_last_session_id"):
                await websocket.send_text(json.dumps({
                    "type": "session_info",
                    "data": {
                        "session_id": service._last_session_id,
                        "turn_id": service._last_turn_id,
                    },
                }))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"message": str(e)},
            }))
        except Exception:
            pass
