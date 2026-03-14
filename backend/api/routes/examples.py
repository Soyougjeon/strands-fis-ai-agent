"""Example queries API route."""

import json
from functools import lru_cache

from fastapi import APIRouter

from backend.config import Config

router = APIRouter(tags=["examples"])

_examples_cache = None


def _load_examples() -> dict:
    global _examples_cache
    if _examples_cache is not None:
        return _examples_cache
    try:
        with open(Config.EXAMPLE_QUERIES_PATH, "r", encoding="utf-8") as f:
            _examples_cache = json.load(f)
    except FileNotFoundError:
        _examples_cache = {"domains": {}}
    return _examples_cache


@router.get("/api/examples")
async def get_examples():
    """Get example queries grouped by domain and tool."""
    return _load_examples()
