FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pipeline/requirements.txt /tmp/pipeline-req.txt
COPY backend/requirements.txt /tmp/backend-req.txt
RUN pip install --no-cache-dir -r /tmp/pipeline-req.txt -r /tmp/backend-req.txt

# Copy source
COPY pipeline/ ./pipeline/
COPY backend/ ./backend/

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
