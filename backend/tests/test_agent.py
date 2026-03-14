"""Unit tests for Agent core (prompts, events, engine)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.agent.events import (
    intent_detected_event, tool_selected_event,
    query_generated_event, query_executed_event,
    text_chunk_event, response_complete_event,
)
from backend.agent.prompts import SCHEMA_MAP, FEW_SHOT_MAP, GRAPH_SCHEMA
from backend.services.token_tracker import calculate_cost


class TestEvents:
    def test_intent_detected_event(self):
        event = json.loads(intent_detected_event("ETF", 0.95, 0.5, 100, 20, 0.0006))
        assert event["type"] == "intent_detected"
        assert event["data"]["intent"] == "ETF"
        assert event["data"]["confidence"] == 0.95
        assert "timestamp" in event

    def test_tool_selected_event(self):
        event = json.loads(tool_selected_event("text2sql", "수치 조회", 0.3, 80, 15, 0.0005))
        assert event["type"] == "tool_selected"
        assert event["data"]["tool"] == "text2sql"

    def test_query_generated_event(self):
        event = json.loads(query_generated_event("sql", "SELECT 1", 0.2, 50, 10, 0.0003))
        assert event["type"] == "query_generated"
        assert event["data"]["query"] == "SELECT 1"

    def test_query_executed_event(self):
        event = json.loads(query_executed_event("5건 조회", [{"a": 1}], None, None, 0.1))
        assert event["type"] == "query_executed"
        assert event["data"]["raw_data"] == [{"a": 1}]

    def test_text_chunk_event(self):
        event = json.loads(text_chunk_event("안녕하세요"))
        assert event["type"] == "text_chunk"
        assert event["data"]["text"] == "안녕하세요"

    def test_response_complete_event(self):
        event = json.loads(response_complete_event(2.5, 500, 200, 0.005))
        assert event["type"] == "response_complete"
        assert event["data"]["total_latency"] == 2.5


class TestPrompts:
    def test_schema_map_has_all_intents(self):
        assert "ETF" in SCHEMA_MAP
        assert "Bond" in SCHEMA_MAP
        assert "Fund" in SCHEMA_MAP

    def test_few_shot_map_has_all_intents(self):
        assert "ETF" in FEW_SHOT_MAP
        assert "Bond" in FEW_SHOT_MAP
        assert "Fund" in FEW_SHOT_MAP

    def test_graph_schema_has_all_intents(self):
        for intent in ("ETF", "Bond", "Fund"):
            assert "node_types" in GRAPH_SCHEMA[intent]
            assert "relationship_types" in GRAPH_SCHEMA[intent]

    def test_schema_map_contains_table_names(self):
        assert "tiger_etf.etf_products" in SCHEMA_MAP["ETF"]
        assert "bond.bond_products" in SCHEMA_MAP["Bond"]
        assert "fund.fund_products" in SCHEMA_MAP["Fund"]


class TestTokenTracker:
    def test_calculate_cost_claude_sonnet(self):
        cost = calculate_cost("claude-sonnet", 1000, 500)
        expected = 1000 * (3.0 / 1_000_000) + 500 * (15.0 / 1_000_000)
        assert abs(cost - expected) < 1e-10

    def test_calculate_cost_titan_embed(self):
        cost = calculate_cost("titan-embed-v2", 500, 0)
        expected = 500 * (0.02 / 1_000_000)
        assert abs(cost - expected) < 1e-10

    def test_calculate_cost_unknown_model(self):
        cost = calculate_cost("unknown", 1000, 500)
        assert cost == 0
