"""Conversation service - DynamoDB single-table CRUD for conversation turns."""

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import boto3
from boto3.dynamodb.conditions import Key

from backend.config import Config


def _convert_floats(obj):
    """Recursively convert float values to Decimal for DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: _convert_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_floats(i) for i in obj]
    return obj


class ConversationService:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb", region_name=Config.AWS_REGION)
        self.table = self.dynamodb.Table(Config.DYNAMODB_TABLE)

    def generate_session_id(self) -> str:
        return str(uuid.uuid4())

    def generate_turn_id(self, turn_number: int) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        return f"turn#{turn_number:04d}#{ts}"

    def save_turn(self, session_id: str, turn_data: dict) -> None:
        """Save a complete turn (question + agent_process + response + total)."""
        item = {
            "session_id": session_id,
            "turn_id": turn_data["turn_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "question": turn_data.get("question", ""),
            "response": turn_data.get("response", ""),
            "intent": turn_data.get("intent", ""),
            "agent_process": turn_data.get("agent_process", {}),
            "total": turn_data.get("total", {}),
            "session_title": turn_data.get("session_title", ""),
            "context_summary": turn_data.get("context_summary", ""),
        }
        self.table.put_item(Item=_convert_floats(item))

    def get_context(self, session_id: str) -> dict:
        """Get context for multi-turn: summary + recent 3 turns."""
        response = self.table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=False,
            Limit=Config.MAX_CONTEXT_TURNS,
        )
        items = response.get("Items", [])

        summary = ""
        recent_turns = []

        if items:
            summary = items[0].get("context_summary", "")

        for item in reversed(items):
            recent_turns.append({
                "question": item.get("question", ""),
                "response": item.get("response", ""),
                "intent": item.get("intent", ""),
            })

        return {"summary": summary, "recent_turns": recent_turns}

    def get_turn_count(self, session_id: str) -> int:
        """Get total turn count for a session."""
        response = self.table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            Select="COUNT",
        )
        return response.get("Count", 0)

    def get_session(self, session_id: str) -> dict:
        """Get all turns for a session."""
        response = self.table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ScanIndexForward=True,
        )
        items = response.get("Items", [])
        if not items:
            return {"session_id": session_id, "title": "", "turns": []}

        return {
            "session_id": session_id,
            "title": items[-1].get("session_title", ""),
            "turns": items,
        }

    def list_sessions(self) -> list[dict]:
        """List all sessions with summary info."""
        response = self.table.scan()
        items = response.get("Items", [])

        sessions = {}
        for item in items:
            sid = item["session_id"]
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "title": "",
                    "turn_count": 0,
                    "last_intent": "",
                    "updated_at": "",
                }
            sessions[sid]["turn_count"] += 1
            ts = item.get("timestamp", "")
            if ts > sessions[sid]["updated_at"]:
                sessions[sid]["updated_at"] = ts
                sessions[sid]["title"] = item.get("session_title", "")
                sessions[sid]["last_intent"] = item.get("intent", "")

        result = sorted(sessions.values(), key=lambda x: x["updated_at"], reverse=True)
        return result

    def delete_session(self, session_id: str) -> int:
        """Delete all turns for a session. Returns count deleted."""
        response = self.table.query(
            KeyConditionExpression=Key("session_id").eq(session_id),
            ProjectionExpression="session_id, turn_id",
        )
        items = response.get("Items", [])

        with self.table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={
                    "session_id": item["session_id"],
                    "turn_id": item["turn_id"],
                })

        return len(items)

    def get_all_turns(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> list[dict]:
        """Get all turns, optionally filtered by date range (for admin/stats)."""
        response = self.table.scan()
        items = response.get("Items", [])

        if start_date or end_date:
            filtered = []
            for item in items:
                ts = item.get("timestamp", "")
                if start_date and ts < start_date:
                    continue
                if end_date and ts > end_date:
                    continue
                filtered.append(item)
            return filtered

        return items
