"""Strands Agent Engine - orchestrates Intent → Tool → Response."""

import json
import time
from typing import AsyncGenerator

import boto3

from backend.agent.events import (
    intent_detected_event, tool_selected_event,
    query_generated_event, query_executed_event,
    text_chunk_event, response_complete_event,
)
from backend.agent.prompts import (
    INTENT_DETECTION_PROMPT, TOOL_SELECTION_PROMPT, RESPONSE_GENERATION_PROMPT,
)
from backend.config import Config
from backend.services.token_tracker import calculate_cost


class AgentEngine:
    def __init__(self):
        self.bedrock = boto3.client("bedrock-runtime", region_name=Config.AWS_REGION)
        self.model_id = Config.LLM_MODEL_ID

    async def process_message(
        self, message: str, context: dict, tools: dict
    ) -> AsyncGenerator[str, None]:
        """Process a message through the full agent loop, yielding events."""
        total_start = time.time()
        total_tokens_in = 0
        total_tokens_out = 0
        total_cost = 0.0
        agent_process = {}

        # Step 1: Intent Detection
        start = time.time()
        intent_result = self._call_llm(INTENT_DETECTION_PROMPT, message)
        latency = time.time() - start
        intent_data = json.loads(intent_result["text"])
        cost = calculate_cost("claude-sonnet", intent_result["tokens_in"], intent_result["tokens_out"])
        total_tokens_in += intent_result["tokens_in"]
        total_tokens_out += intent_result["tokens_out"]
        total_cost += cost

        agent_process["intent_detection"] = {
            "intent": intent_data["intent"],
            "confidence": intent_data.get("confidence", 0),
            "latency": round(latency, 3),
            "tokens_in": intent_result["tokens_in"],
            "tokens_out": intent_result["tokens_out"],
            "cost": round(cost, 6),
        }
        yield intent_detected_event(
            intent_data["intent"], intent_data.get("confidence", 0),
            round(latency, 3), intent_result["tokens_in"],
            intent_result["tokens_out"], round(cost, 6),
        )

        intent = intent_data["intent"]

        # Step 2: Tool Selection
        start = time.time()
        tool_result = self._call_llm(TOOL_SELECTION_PROMPT, message)
        latency = time.time() - start
        tool_data = json.loads(tool_result["text"])
        cost = calculate_cost("claude-sonnet", tool_result["tokens_in"], tool_result["tokens_out"])
        total_tokens_in += tool_result["tokens_in"]
        total_tokens_out += tool_result["tokens_out"]
        total_cost += cost

        agent_process["tool_selection"] = {
            "tool": tool_data["tool"],
            "rationale": tool_data.get("rationale", ""),
            "latency": round(latency, 3),
            "tokens_in": tool_result["tokens_in"],
            "tokens_out": tool_result["tokens_out"],
            "cost": round(cost, 6),
        }
        yield tool_selected_event(
            tool_data["tool"], tool_data.get("rationale", ""),
            round(latency, 3), tool_result["tokens_in"],
            tool_result["tokens_out"], round(cost, 6),
        )

        tool_name = tool_data["tool"]

        # Step 3: Tool Execution
        tool_handler = tools.get(tool_name)
        if not tool_handler:
            yield text_chunk_event(f"Tool '{tool_name}'을 찾을 수 없습니다.")
            return

        tool_exec_result = await tool_handler.execute(message, intent)

        # Query Generated event
        if tool_exec_result.get("query_step"):
            qs = tool_exec_result["query_step"]
            total_tokens_in += qs.get("tokens_in", 0)
            total_tokens_out += qs.get("tokens_out", 0)
            total_cost += qs.get("cost", 0)
            agent_process["query_generation"] = qs
            yield query_generated_event(
                qs.get("query_type", ""), qs.get("query", ""),
                qs.get("latency", 0), qs.get("tokens_in", 0),
                qs.get("tokens_out", 0), qs.get("cost", 0),
            )

        # Query Executed event
        exec_data = tool_exec_result.get("execution", {})
        agent_process["query_execution"] = exec_data
        yield query_executed_event(
            exec_data.get("result_summary", ""),
            exec_data.get("raw_data"),
            exec_data.get("graph_data"),
            exec_data.get("chart_data"),
            exec_data.get("latency", 0),
        )

        # Step 4: Response Generation (streaming)
        start = time.time()
        context_summary = context.get("summary", "")
        recent_turns = context.get("recent_turns", [])
        recent_text = "\n".join(
            f"Q: {t.get('question', '')}\nA: {t.get('response', '')}"
            for t in recent_turns
        )

        raw_data = exec_data.get("raw_data")
        if raw_data is not None:
            raw_data_str = json.dumps(raw_data, ensure_ascii=False, default=str)
            if len(raw_data_str) > 8000:
                raw_data_str = raw_data_str[:8000] + "... (truncated)"
        else:
            raw_data_str = "없음"

        prompt = RESPONSE_GENERATION_PROMPT.format(
            context_summary=context_summary or "없음",
            recent_turns=recent_text or "없음",
            question=message,
            tool_name=tool_name,
            query=tool_exec_result.get("query_step", {}).get("query", ""),
            result_summary=exec_data.get("result_summary", ""),
            raw_data=raw_data_str,
        )

        response_text = ""
        resp_result = self._call_llm_streaming(prompt)
        for chunk in resp_result["chunks"]:
            response_text += chunk
            yield text_chunk_event(chunk)

        latency = time.time() - start
        cost = calculate_cost("claude-sonnet", resp_result["tokens_in"], resp_result["tokens_out"])
        total_tokens_in += resp_result["tokens_in"]
        total_tokens_out += resp_result["tokens_out"]
        total_cost += cost

        agent_process["response_generation"] = {
            "latency": round(latency, 3),
            "tokens_in": resp_result["tokens_in"],
            "tokens_out": resp_result["tokens_out"],
            "cost": round(cost, 6),
        }

        total_latency = round(time.time() - total_start, 3)
        yield response_complete_event(
            total_latency, total_tokens_in, total_tokens_out, round(total_cost, 6),
        )

        # Attach metadata for caller
        self._last_result = {
            "response": response_text,
            "agent_process": agent_process,
            "total": {
                "latency": total_latency,
                "tokens_in": total_tokens_in,
                "tokens_out": total_tokens_out,
                "cost": round(total_cost, 6),
            },
            "intent": intent,
        }

    def _call_llm(self, system_prompt: str, user_message: str) -> dict:
        response = self.bedrock.converse(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": user_message}]}],
            system=[{"text": system_prompt}],
        )
        output = response["output"]["message"]["content"][0]["text"]
        usage = response.get("usage", {})
        # Extract JSON from response (handle markdown code blocks)
        text = output.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rsplit("```", 1)[0].strip()
        return {
            "text": text,
            "tokens_in": usage.get("inputTokens", 0),
            "tokens_out": usage.get("outputTokens", 0),
        }

    def _call_llm_streaming(self, prompt: str) -> dict:
        response = self.bedrock.converse_stream(
            modelId=self.model_id,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
        )
        chunks = []
        tokens_in = 0
        tokens_out = 0

        for event in response.get("stream", []):
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"]
                if "text" in delta:
                    chunks.append(delta["text"])
            elif "metadata" in event:
                usage = event["metadata"].get("usage", {})
                tokens_in = usage.get("inputTokens", 0)
                tokens_out = usage.get("outputTokens", 0)

        return {
            "chunks": chunks,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
        }
