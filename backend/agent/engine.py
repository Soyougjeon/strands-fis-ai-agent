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
    INTENT_AND_TOOL_PROMPT, RESPONSE_GENERATION_PROMPT,
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

        # Step 1+2: Intent Detection + Tool Selection (single LLM call)
        start = time.time()
        combined_result = self._call_llm(INTENT_AND_TOOL_PROMPT, message)
        latency = round(time.time() - start, 3)
        combined_data = json.loads(combined_result["text"])
        cost = calculate_cost("claude-sonnet", combined_result["tokens_in"], combined_result["tokens_out"])
        total_tokens_in += combined_result["tokens_in"]
        total_tokens_out += combined_result["tokens_out"]
        total_cost += cost

        # Split cost/tokens evenly for display purposes
        half_tokens_in = combined_result["tokens_in"] // 2
        half_tokens_out = combined_result["tokens_out"] // 2
        half_cost = round(cost / 2, 6)

        intent = combined_data["intent"]
        tool_name = combined_data["tool"]

        agent_process["intent_detection"] = {
            "intent": intent,
            "confidence": combined_data.get("confidence", 0),
            "latency": latency,
            "tokens_in": half_tokens_in,
            "tokens_out": half_tokens_out,
            "cost": half_cost,
        }
        yield intent_detected_event(
            intent, combined_data.get("confidence", 0),
            latency, half_tokens_in, half_tokens_out, half_cost,
        )

        agent_process["tool_selection"] = {
            "tool": tool_name,
            "rationale": combined_data.get("rationale", ""),
            "latency": latency,
            "tokens_in": combined_result["tokens_in"] - half_tokens_in,
            "tokens_out": combined_result["tokens_out"] - half_tokens_out,
            "cost": round(cost - half_cost, 6),
        }
        yield tool_selected_event(
            tool_name, combined_data.get("rationale", ""),
            latency, combined_result["tokens_in"] - half_tokens_in,
            combined_result["tokens_out"] - half_tokens_out, round(cost - half_cost, 6),
        )

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
            extra = {}
            if qs.get("toolkit_params"):
                extra["toolkit_params"] = qs["toolkit_params"]
            if qs.get("opensearch_query"):
                extra["opensearch_query"] = qs["opensearch_query"]
            yield query_generated_event(
                qs.get("query_type", ""), qs.get("query", ""),
                qs.get("latency", 0), qs.get("tokens_in", 0),
                qs.get("tokens_out", 0), qs.get("cost", 0),
                **extra,
            )

        # Query Executed event
        exec_data = tool_exec_result.get("execution", {})
        agent_process["query_execution"] = exec_data
        yield query_executed_event(
            exec_data.get("result_summary", ""),
            exec_data.get("raw_data"),
            exec_data.get("graph_data"),
            exec_data.get("chart_data"),
            exec_data.get("lexical_graph_data"),
            exec_data.get("latency", 0),
            exec_data.get("est_tokens_in", 0),
            exec_data.get("est_tokens_out", 0),
        )

        # Step 4: Response Generation
        start = time.time()
        response_text = ""

        if tool_exec_result.get("direct_response"):
            # GraphRAG: toolkit already generated response — stream directly
            direct = tool_exec_result["direct_response"]
            # Split into chunks for streaming effect
            chunk_size = 50
            for i in range(0, len(direct), chunk_size):
                chunk = direct[i:i + chunk_size]
                response_text += chunk
                yield text_chunk_event(chunk)

            latency = time.time() - start
            # Include estimated toolkit LLM tokens in totals
            est_in = exec_data.get("est_tokens_in", 0)
            est_out = exec_data.get("est_tokens_out", 0)
            est_cost = calculate_cost("claude-sonnet", est_in, est_out) if (est_in or est_out) else 0
            total_tokens_in += est_in
            total_tokens_out += est_out
            total_cost += est_cost
            agent_process["response_generation"] = {
                "latency": round(latency, 3),
                "tokens_in": est_in,
                "tokens_out": est_out,
                "cost": round(est_cost, 6),
                "estimated": True,
            }
        else:
            # Other tools: generate response via engine LLM (streaming)
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
                query=(tool_exec_result.get("query_step") or {}).get("query", ""),
                result_summary=exec_data.get("result_summary", ""),
                raw_data=raw_data_str,
            )

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
        resp_step = agent_process.get("response_generation", {})
        yield response_complete_event(
            total_latency, total_tokens_in, total_tokens_out, round(total_cost, 6),
            resp_latency=resp_step.get("latency", 0),
            resp_tokens_in=resp_step.get("tokens_in", 0),
            resp_tokens_out=resp_step.get("tokens_out", 0),
            resp_cost=resp_step.get("cost", 0),
            resp_estimated=resp_step.get("estimated", False),
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
