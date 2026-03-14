import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Aurora PostgreSQL
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "fis")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_URL = os.getenv(
        "DB_URL",
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )

    # Neptune
    NEPTUNE_ENDPOINT = os.getenv("NEPTUNE_ENDPOINT", "")
    NEPTUNE_PORT = int(os.getenv("NEPTUNE_PORT", "8182"))

    # OpenSearch Serverless
    OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT", "")

    # AWS
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    # Bedrock
    LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "us.anthropic.claude-sonnet-4-6-v1:0")
    EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")
    EMBEDDING_DIMENSION = 1024

    # DynamoDB
    DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "conversation_turns")

    # Agent
    MAX_CONTEXT_TURNS = 3
    SUMMARY_REFRESH_INTERVAL = 3  # 3턴마다 요약 갱신
    MAX_SUMMARY_LENGTH = 500

    # SQL Safety
    SQL_TIMEOUT_SECONDS = 10
    SQL_MAX_ROWS = 1000

    # Example queries path
    EXAMPLE_QUERIES_PATH = os.getenv(
        "EXAMPLE_QUERIES_PATH",
        os.path.join(os.path.dirname(__file__), "..", "pipeline", "data", "mock", "example_queries.json"),
    )

    # Token pricing (USD per token)
    PRICING = {
        "claude-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
        "titan-embed-v2": {"input": 0.02 / 1_000_000, "output": 0},
    }
