"""Unit tests for services."""

from unittest.mock import MagicMock, patch

import pytest

from backend.services.token_tracker import aggregate_token_usage
from backend.services.visualization import detect_chart_data


class TestTokenAggregation:
    def test_daily_aggregation(self):
        turns = [
            {"timestamp": "2025-01-15T10:00:00+00:00", "total": {"tokens_in": 100, "tokens_out": 50, "cost": 0.001}},
            {"timestamp": "2025-01-15T14:00:00+00:00", "total": {"tokens_in": 200, "tokens_out": 100, "cost": 0.002}},
            {"timestamp": "2025-01-16T10:00:00+00:00", "total": {"tokens_in": 150, "tokens_out": 75, "cost": 0.0015}},
        ]
        result = aggregate_token_usage(turns, "daily")
        assert result["period"] == "daily"
        assert len(result["data"]) == 2
        assert result["totals"]["tokens_in"] == 450
        assert result["totals"]["request_count"] == 3

    def test_monthly_aggregation(self):
        turns = [
            {"timestamp": "2025-01-15T10:00:00+00:00", "total": {"tokens_in": 100, "tokens_out": 50, "cost": 0.001}},
            {"timestamp": "2025-02-15T10:00:00+00:00", "total": {"tokens_in": 200, "tokens_out": 100, "cost": 0.002}},
        ]
        result = aggregate_token_usage(turns, "monthly")
        assert len(result["data"]) == 2

    def test_empty_turns(self):
        result = aggregate_token_usage([], "daily")
        assert result["data"] == []
        assert result["totals"]["request_count"] == 0


class TestVisualization:
    def test_bar_chart_detection(self):
        data = [
            {"name": "ETF A", "aum": 5000},
            {"name": "ETF B", "aum": 3000},
            {"name": "ETF C", "aum": 1000},
        ]
        result = detect_chart_data(data, ["name", "aum"])
        assert result is not None
        assert result["chart_type"] == "bar"
        assert result["x_axis"] == "name"
        assert result["y_axis"] == "aum"

    def test_pie_chart_detection(self):
        data = [
            {"sector": "IT", "weight": 40.0},
            {"sector": "Finance", "weight": 30.0},
            {"sector": "Health", "weight": 30.0},
        ]
        result = detect_chart_data(data, ["sector", "weight"])
        assert result is not None
        assert result["chart_type"] == "pie"

    def test_no_chart_single_column(self):
        data = [{"name": "A"}]
        result = detect_chart_data(data, ["name"])
        assert result is None

    def test_no_chart_empty_data(self):
        result = detect_chart_data([], ["a", "b"])
        assert result is None

    def test_no_numeric_columns(self):
        data = [{"a": "x", "b": "y"}]
        result = detect_chart_data(data, ["a", "b"])
        assert result is None


class TestConversationService:
    @patch("backend.services.conversation.boto3")
    def test_generate_session_id(self, mock_boto3):
        from backend.services.conversation import ConversationService
        mock_boto3.resource.return_value.Table.return_value = MagicMock()
        service = ConversationService()
        sid = service.generate_session_id()
        assert len(sid) == 36  # UUID format

    @patch("backend.services.conversation.boto3")
    def test_generate_turn_id(self, mock_boto3):
        from backend.services.conversation import ConversationService
        mock_boto3.resource.return_value.Table.return_value = MagicMock()
        service = ConversationService()
        tid = service.generate_turn_id(1)
        assert tid.startswith("turn#0001#")
