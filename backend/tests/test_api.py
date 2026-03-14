"""API endpoint tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from backend.api.main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestExamplesEndpoint:
    @patch("backend.api.routes.examples._load_examples")
    def test_get_examples(self, mock_load, client):
        mock_load.return_value = {"domains": {"ETF": []}}
        response = client.get("/api/examples")
        assert response.status_code == 200


class TestConversationsEndpoint:
    @patch("backend.api.routes.conversations.ConversationService")
    def test_list_conversations(self, mock_cls, client):
        mock_service = MagicMock()
        mock_service.list_sessions.return_value = []
        mock_cls.return_value = mock_service
        response = client.get("/api/conversations")
        assert response.status_code == 200
        assert response.json() == {"conversations": []}

    @patch("backend.api.routes.conversations.ConversationService")
    def test_get_conversation_not_found(self, mock_cls, client):
        mock_service = MagicMock()
        mock_service.get_session.return_value = {"session_id": "x", "title": "", "turns": []}
        mock_cls.return_value = mock_service
        response = client.get("/api/conversations/nonexistent")
        assert response.status_code == 404

    @patch("backend.api.routes.conversations.ConversationService")
    def test_delete_conversation_not_found(self, mock_cls, client):
        mock_service = MagicMock()
        mock_service.delete_session.return_value = 0
        mock_cls.return_value = mock_service
        response = client.delete("/api/conversations/nonexistent")
        assert response.status_code == 404


class TestAdminEndpoint:
    @patch("backend.api.routes.admin.ConversationService")
    def test_token_usage(self, mock_cls, client):
        mock_service = MagicMock()
        mock_service.get_all_turns.return_value = []
        mock_cls.return_value = mock_service
        response = client.get("/api/admin/token-usage?period=daily")
        assert response.status_code == 200
        assert response.json()["period"] == "daily"

    @patch("backend.api.routes.admin.ConversationService")
    def test_admin_conversations(self, mock_cls, client):
        mock_service = MagicMock()
        mock_service.list_sessions.return_value = []
        mock_cls.return_value = mock_service
        response = client.get("/api/admin/conversations")
        assert response.status_code == 200


class TestText2SQLTool:
    def test_sql_validation(self):
        from backend.tools.text2sql import Text2SQLTool
        tool = Text2SQLTool.__new__(Text2SQLTool)
        assert tool._validate_sql("SELECT * FROM table") is True
        assert tool._validate_sql("DROP TABLE users") is False
        assert tool._validate_sql("DELETE FROM users") is False
        assert tool._validate_sql("SELECT * FROM t; DROP TABLE t") is False

    def test_sql_extract(self):
        from backend.tools.text2sql import Text2SQLTool
        tool = Text2SQLTool.__new__(Text2SQLTool)
        sql = tool._extract_sql("```sql\nSELECT * FROM t\n```")
        assert sql == "SELECT * FROM t"

    def test_ensure_limit(self):
        from backend.tools.text2sql import Text2SQLTool
        tool = Text2SQLTool.__new__(Text2SQLTool)
        result = tool._ensure_limit("SELECT * FROM t")
        assert "LIMIT" in result
        result2 = tool._ensure_limit("SELECT * FROM t LIMIT 10")
        assert result2 == "SELECT * FROM t LIMIT 10"


class TestOpenCypherTool:
    def test_cypher_validation(self):
        from backend.tools.opencypher import OpenCypherTool
        tool = OpenCypherTool.__new__(OpenCypherTool)
        assert tool._validate_cypher("MATCH (n) WHERE n.__tenant__ = 'etf' RETURN n", "etf") is True
        assert tool._validate_cypher("CREATE (n:Node {name: 'test'})", "etf") is False
        assert tool._validate_cypher("MATCH (n) RETURN n", "etf") is False  # no tenant filter

    def test_cypher_extract(self):
        from backend.tools.opencypher import OpenCypherTool
        tool = OpenCypherTool.__new__(OpenCypherTool)
        cypher = tool._extract_cypher("```cypher\nMATCH (n) RETURN n\n```")
        assert cypher == "MATCH (n) RETURN n"
