# Build Instructions

## Prerequisites

### System Requirements
- Python 3.11+
- Node.js 18+ / npm 9+
- AWS CLI configured (us-east-1)
- Nginx (배포 시)

### AWS Services Required
- Amazon Bedrock (Claude Sonnet, Titan Embed v2 모델 접근 권한)
- Aurora PostgreSQL (connection endpoint)
- Amazon Neptune (OpenCypher endpoint)
- OpenSearch Serverless (collection endpoint)
- DynamoDB (conversation_turns 테이블)

---

## Unit 1: Mock Data Pipeline

### 1.1 Python 환경 설정
```bash
cd /path/to/strands-fis

# 가상환경 생성 (프로젝트 루트)
python -m venv .venv
source .venv/bin/activate

# Pipeline 의존성 설치
pip install -r pipeline/requirements.txt
```

### 1.2 환경 변수 설정
```bash
# .env 파일 생성 (프로젝트 루트)
cat > .env << 'EOF'
# Aurora PostgreSQL
DB_HOST=your-aurora-endpoint.rds.amazonaws.com
DB_PORT=5432
DB_NAME=fis
DB_USER=postgres
DB_PASSWORD=your-password

# Neptune
NEPTUNE_ENDPOINT=your-neptune-endpoint.neptune.amazonaws.com
NEPTUNE_PORT=8182

# OpenSearch Serverless
OPENSEARCH_ENDPOINT=your-opensearch-endpoint.aoss.amazonaws.com

# AWS
AWS_REGION=us-east-1

# Bedrock
EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
EOF
```

### 1.3 Pipeline 실행
```bash
# Phase 1-3: 로컬 파일 생성 (AWS 불필요)
python -m pipeline.main generate-csv      # CSV 생성 (~9개 파일)
python -m pipeline.main generate-md       # MD 생성 (~93개 파일)
python -m pipeline.main generate-queries  # 예시 쿼리 JSON

# Phase 4-6: AWS 필요
python -m pipeline.main load-db           # Aurora PG 적재
python -m pipeline.main index-graphrag    # Neptune 인덱싱
python -m pipeline.main index-rag         # OpenSearch 인덱싱

# 또는 전체 실행
python -m pipeline.main run-all
```

### 1.4 생성 파일 확인
```bash
ls -la pipeline/data/mock/etf/     # etf_products.csv 등 4개
ls -la pipeline/data/mock/bond/    # bond_products.csv 등 2개
ls -la pipeline/data/mock/fund/    # fund_products.csv 등 3개
ls -la pipeline/data/mock/md/      # 93개 MD 파일
cat pipeline/data/mock/example_queries.json | python -m json.tool | head -50
```

---

## Unit 2: Agent Backend

### 2.1 Python 의존성 설치
```bash
# 동일 가상환경 사용
pip install -r backend/requirements.txt
```

### 2.2 환경 변수 추가 (.env)
```bash
# .env 파일에 추가
cat >> .env << 'EOF'

# Bedrock LLM
LLM_MODEL_ID=us.anthropic.claude-sonnet-4-6-v1:0

# DynamoDB
DYNAMODB_TABLE=conversation_turns

# Example Queries Path
EXAMPLE_QUERIES_PATH=./pipeline/data/mock/example_queries.json
EOF
```

### 2.3 DynamoDB 테이블 생성
```bash
aws dynamodb create-table \
  --table-name conversation_turns \
  --attribute-definitions \
    AttributeName=session_id,AttributeType=S \
    AttributeName=turn_id,AttributeType=S \
  --key-schema \
    AttributeName=session_id,KeyType=HASH \
    AttributeName=turn_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 2.4 Backend 서버 실행
```bash
# 개발 모드
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/api/health
# Expected: {"status":"ok"}
```

---

## Unit 3: Frontend

### 3.1 Node.js 의존성 설치
```bash
cd frontend
npm install
```

### 3.2 개발 모드 실행
```bash
# Backend가 :8000에서 실행 중이어야 함
npm run dev
# http://localhost:5173 접속
```

### 3.3 프로덕션 빌드
```bash
npm run build
# dist/ 디렉토리에 정적 파일 생성
ls -la dist/
```

---

## Nginx 배포 (EC2)

### 4.1 Nginx 설치
```bash
sudo yum install -y nginx          # Amazon Linux
# 또는
sudo apt install -y nginx           # Ubuntu
```

### 4.2 설정 파일 복사
```bash
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo cp nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
```

### 4.3 Basic Auth 설정
```bash
# htpasswd 유틸리티 설치
sudo yum install -y httpd-tools     # Amazon Linux
# 또는
sudo apt install -y apache2-utils   # Ubuntu

# 사용자 생성 (5명 테스터)
sudo htpasswd -c /etc/nginx/.htpasswd tester1
sudo htpasswd /etc/nginx/.htpasswd tester2
sudo htpasswd /etc/nginx/.htpasswd tester3
sudo htpasswd /etc/nginx/.htpasswd tester4
sudo htpasswd /etc/nginx/.htpasswd tester5
```

### 4.4 프론트엔드 배포
```bash
# 빌드 파일 복사
sudo cp -r frontend/dist/* /usr/share/nginx/html/
```

### 4.5 서비스 시작
```bash
# Backend (systemd 또는 screen)
cd /path/to/strands-fis
source .venv/bin/activate
nohup uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 &

# Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 접속 확인
curl -u tester1:password http://localhost/api/health
```
