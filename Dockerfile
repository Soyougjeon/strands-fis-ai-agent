FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (git needed for pip install from GitHub)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pipeline/requirements.txt /tmp/pipeline-req.txt
COPY backend/requirements.txt /tmp/backend-req.txt
RUN pip install --no-cache-dir -r /tmp/pipeline-req.txt -r /tmp/backend-req.txt

# Install graphrag-toolkit (lexical-graph) with OpenSearch dependencies
RUN pip install --no-cache-dir \
    opensearch-py \
    llama-index-vector-stores-opensearch \
    "graphrag-toolkit-lexical-graph @ git+https://github.com/awslabs/graphrag-toolkit.git#subdirectory=lexical-graph" \
    || echo "WARNING: graphrag-toolkit install failed, continuing without it"

# Copy source
COPY pipeline/ ./pipeline/
COPY backend/ ./backend/

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
