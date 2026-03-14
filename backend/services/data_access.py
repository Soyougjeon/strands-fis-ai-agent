"""Data Access service - Tool registry and execution delegation."""

from backend.tools.text2sql import Text2SQLTool
from backend.tools.rag import RAGTool
from backend.tools.graphrag import GraphRAGTool
from backend.tools.opencypher import OpenCypherTool


def get_tools() -> dict:
    """Create and return all tool instances."""
    return {
        "text2sql": Text2SQLTool(),
        "rag": RAGTool(),
        "graphrag": GraphRAGTool(),
        "opencypher": OpenCypherTool(),
    }
