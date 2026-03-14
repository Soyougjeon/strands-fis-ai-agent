"""Agent Service - manages agent engine lifecycle."""

from backend.agent.engine import AgentEngine
from backend.services.data_access import get_tools


class AgentService:
    def __init__(self):
        self.engine = AgentEngine()
        self.tools = get_tools()

    async def run(self, message: str, context: dict):
        """Run agent and yield SSE events. Returns metadata via engine._last_result."""
        async for event in self.engine.process_message(message, context, self.tools):
            yield event

    def get_last_result(self) -> dict:
        return getattr(self.engine, "_last_result", {})
