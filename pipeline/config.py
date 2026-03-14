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
    OPENSEARCH_REGION = os.getenv("AWS_REGION", "us-east-1")

    # Bedrock
    BEDROCK_REGION = os.getenv("AWS_REGION", "us-east-1")
    EMBEDDING_MODEL_ID = os.getenv(
        "EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"
    )
    EMBEDDING_DIMENSION = 1024

    # Mock data
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "mock")
    ETF_COUNT = int(os.getenv("ETF_COUNT", "30"))
    BOND_COUNT = int(os.getenv("BOND_COUNT", "30"))
    FUND_COUNT = int(os.getenv("FUND_COUNT", "30"))

    # RAG indexing
    RAG_CHUNK_SIZE = 500
    RAG_CHUNK_OVERLAP = 100
