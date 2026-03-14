"""Chat Service - orchestrates conversation flow."""

import boto3

from backend.config import Config
from backend.services.agent_service import AgentService
from backend.services.conversation import ConversationService


class ChatService:
    def __init__(self):
        self.agent_service = AgentService()
        self.conversation = ConversationService()
        self.bedrock = boto3.client("bedrock-runtime", region_name=Config.AWS_REGION)

    async def handle_message(self, session_id: str | None, message: str):
        """Process a chat message, yielding events and saving the turn.

        Yields:
            SSE event strings from the agent.
        """
        is_new_session = session_id is None
        if is_new_session:
            session_id = self.conversation.generate_session_id()

        # Get context for multi-turn
        context = self.conversation.get_context(session_id) if not is_new_session else {"summary": "", "recent_turns": []}

        # Run agent
        async for event in self.agent_service.run(message, context):
            yield event

        # Post-processing: save turn
        result = self.agent_service.get_last_result()
        if not result:
            return

        turn_count = self.conversation.get_turn_count(session_id)
        turn_number = turn_count + 1
        turn_id = self.conversation.generate_turn_id(turn_number)

        # Generate session title on first turn
        session_title = ""
        if is_new_session or turn_count == 0:
            session_title = self._generate_title(message)
        else:
            prev = self.conversation.get_session(session_id)
            session_title = prev.get("title", "")

        # Update context summary every N turns
        context_summary = context.get("summary", "")
        if turn_number % Config.SUMMARY_REFRESH_INTERVAL == 0:
            context_summary = self._update_summary(context_summary, message, result.get("response", ""))

        turn_data = {
            "turn_id": turn_id,
            "question": message,
            "response": result.get("response", ""),
            "intent": result.get("intent", ""),
            "agent_process": result.get("agent_process", {}),
            "total": result.get("total", {}),
            "session_title": session_title,
            "context_summary": context_summary,
        }
        self.conversation.save_turn(session_id, turn_data)

        # Store session_id for caller
        self._last_session_id = session_id
        self._last_turn_id = turn_id

    def _generate_title(self, message: str) -> str:
        """Generate a short title from the first question (max 50 chars)."""
        title = message.strip()
        if len(title) > 50:
            title = title[:47] + "..."
        return title

    def _update_summary(self, prev_summary: str, question: str, answer: str) -> str:
        """Update context summary using LLM."""
        prompt = f"""이전 요약: {prev_summary or '없음'}
새 질문: {question}
새 답변: {answer[:300]}

위 대화를 포함하여 전체 대화 맥락을 500자 이내로 요약하세요. 한국어로 작성하세요."""

        try:
            response = self.bedrock.converse(
                modelId=Config.LLM_MODEL_ID,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
            )
            return response["output"]["message"]["content"][0]["text"][:Config.MAX_SUMMARY_LENGTH]
        except Exception:
            return prev_summary
