# Doc 7: Deployment Guide

## 1. Docker 구성

### 1.1 Backend (Dockerfile)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY pipeline/requirements.txt /tmp/pipeline-req.txt
COPY backend/requirements.txt /tmp/backend-req.txt
RUN pip install --no-cache-dir -r /tmp/pipeline-req.txt -r /tmp/backend-req.txt

# graphrag-toolkit 설치
RUN pip install --no-cache-dir \
    opensearch-py llama-index-vector-stores-opensearch \
    "graphrag-toolkit-lexical-graph @ git+https://github.com/awslabs/graphrag-toolkit.git#subdirectory=lexical-graph" \
    || echo "WARNING: graphrag-toolkit install failed"

COPY pipeline/ ./pipeline/
COPY backend/ ./backend/
EXPOSE 8000
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 Frontend (Dockerfile.frontend)

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
RUN apk add --no-cache apache2-utils && \
    htpasswd -nb tester1 'password1!' > /etc/nginx/.htpasswd
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 1.3 Docker Compose (docker-compose.yml)

```yaml
version: "3.8"
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    env_file: .env
    ports:
      - "8000:8000"
    restart: always
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 30s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: always
```

## 2. Nginx 설정

### 2.1 default.conf (핵심)

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

server {
    listen 80;
    auth_basic "Protected";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # React SPA
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API 프록시
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }

    # WebSocket 프록시
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_read_timeout 86400s;
    }
}
```

## 3. 배포 순서

### 3.1 전체 흐름

```
1. 인프라 배포 (CDK)
2. 데이터 적재 (Pipeline)
3. 애플리케이션 배포 (Docker Compose)
4. 검증
```

### 3.2 Step 1: 인프라 배포

```bash
cd infra
npm install
npx cdk bootstrap   # 최초 1회
npx cdk deploy strands-fis-network
npx cdk deploy strands-fis-data
npx cdk deploy strands-fis-compute
```

출력값 기록:
- AuroraEndpoint, AuroraSecretArn
- NeptuneEndpoint
- OpenSearchEndpoint
- PublicIp, SshCommand

### 3.3 Step 2: EC2 접속 및 데이터 적재

```bash
# EC2 접속
ssh -i strands-fis-key.pem ec2-user@<PublicIp>
cd /opt/strands-fis

# Mock 데이터 생성 (로컬 파일)
docker run --rm --env-file .env -v $(pwd)/pipeline/data:/app/pipeline/data \
  strands-backend python -m pipeline.main generate-csv
docker run --rm --env-file .env -v $(pwd)/pipeline/data:/app/pipeline/data \
  strands-backend python -m pipeline.main generate-md

# DB 적재
docker run --rm --env-file .env \
  strands-backend python -m pipeline.main load-db

# 인덱싱 (시간 소요)
docker run --rm --env-file .env \
  strands-backend python -m pipeline.main index-graphrag
docker run --rm --env-file .env \
  strands-backend python -m pipeline.main index-rag
```

### 3.4 Step 3: 애플리케이션 시작

```bash
docker-compose up -d --build
docker-compose ps
docker-compose logs -f backend
```

### 3.5 Step 4: 검증

```bash
# 헬스체크
curl http://localhost:8000/api/health
# → {"status": "ok"}

# 브라우저 접속
# http://<PublicIp> (Basic Auth 입력)
```

## 4. 헬스체크

| 체크 | 방법 | 기대값 |
|------|------|--------|
| Backend | `GET /api/health` | `{"status": "ok"}` |
| Frontend | 브라우저 접속 | React SPA 로드 |
| WebSocket | 채팅 메시지 전송 | 스트리밍 응답 수신 |
| DB 연결 | 채팅에서 SQL 질의 | 데이터 반환 |
| Neptune | 채팅에서 OpenCypher 질의 | 그래프 데이터 반환 |

## 5. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| Backend 시작 실패 | .env 누락 또는 잘못된 값 | .env 파일 확인, 엔드포인트 검증 |
| DB 연결 실패 | 보안그룹 미설정 | EC2 SG → Aurora SG 5432 인바운드 확인 |
| Neptune 연결 실패 | 보안그룹 또는 IAM | EC2 SG → Neptune SG 8182 + IAM neptune-db:connect |
| OpenSearch 403 | IAM 권한 또는 Data Access Policy | AOSS Data Access Policy에 EC2 Role ARN 추가 |
| WebSocket 끊김 | Nginx timeout | proxy_read_timeout 86400s 확인 |
| CORS 에러 | FastAPI CORS 설정 | allow_origins에 프론트엔드 URL 추가 |
| Bedrock 접근 거부 | 모델 접근 미활성화 | Bedrock 콘솔에서 모델 접근 요청 |
| graphrag-toolkit 설치 실패 | git 미설치 | Dockerfile에 `apt-get install -y git` 확인 |
