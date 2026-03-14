# Build and Test Summary

## 프로젝트 구조

```
strands-fis/
├── pipeline/            # Unit 1: Mock Data Pipeline
│   ├── generators/      # CSV/MD/Query 생성 (4 files)
│   ├── loaders/         # DB/GraphRAG/RAG 적재 (3 files)
│   ├── models/          # ORM 모델 (5 files)
│   ├── tests/           # Unit tests (2 files)
│   ├── main.py          # CLI entry point
│   └── requirements.txt
├── backend/             # Unit 2: Agent Backend
│   ├── agent/           # Agent core (3 files)
│   ├── tools/           # 4 Tools (4 files)
│   ├── services/        # 6 Services (6 files)
│   ├── api/             # FastAPI + routes (7 files)
│   ├── tests/           # Unit tests (3 files)
│   ├── config.py
│   └── requirements.txt
├── frontend/            # Unit 3: Frontend
│   ├── src/
│   │   ├── components/  # React components (10 files)
│   │   ├── hooks/       # Custom hooks (2 files)
│   │   └── types/       # TypeScript types (1 file)
│   ├── package.json
│   └── vite.config.ts
├── nginx/               # Nginx 설정
│   ├── nginx.conf
│   ├── conf.d/default.conf
│   └── .htpasswd
└── .env                 # 환경 변수 (생성 필요)
```

## 빌드 순서

```
1. 환경 설정
   └── .env 생성, Python venv, Node.js

2. Unit 1: Pipeline
   ├── pip install -r pipeline/requirements.txt
   ├── python -m pipeline.main generate-csv     (로컬)
   ├── python -m pipeline.main generate-md      (로컬)
   ├── python -m pipeline.main generate-queries (로컬)
   ├── python -m pipeline.main load-db          (AWS)
   ├── python -m pipeline.main index-graphrag   (AWS)
   └── python -m pipeline.main index-rag        (AWS)

3. Unit 2: Backend
   ├── pip install -r backend/requirements.txt
   ├── DynamoDB 테이블 생성
   └── uvicorn backend.api.main:app --port 8000

4. Unit 3: Frontend
   ├── cd frontend && npm install
   ├── npm run dev                              (개발)
   └── npm run build                            (프로덕션)

5. Nginx (EC2 배포)
   ├── Nginx 설정 복사
   ├── htpasswd 생성
   ├── frontend/dist → /usr/share/nginx/html
   └── systemctl start nginx
```

## 테스트 계획

| 테스트 유형 | 파일 | AWS 필요 | 실행 명령 |
|------------|------|---------|----------|
| **Unit Test** | pipeline/tests/, backend/tests/ | No | `pytest pipeline/tests/ backend/tests/ -v` |
| **Integration Test** | 수동 (curl/wscat) | Yes | build-and-test/integration-test-instructions.md |
| **Performance Test** | 수동 (ab/curl) | Yes | build-and-test/performance-test-instructions.md |

## Unit Test 요약

| Unit | 테스트 수 | 범위 |
|------|----------|------|
| Pipeline | ~10 | CSV 생성 검증, Loader mock |
| Backend - Agent | ~13 | Events, Prompts, TokenTracker |
| Backend - Services | ~8 | TokenAggregation, Visualization, Conversation |
| Backend - API | ~12 | Health, Conversations, Admin, SQL/Cypher validation |
| **Total** | **~43** | |

## Integration Test 요약

| 카테고리 | 테스트 수 | 범위 |
|---------|----------|------|
| Pipeline → Backend | 5 | Text2SQL, RAG, OpenCypher (ETF/Bond/Fund) |
| Backend → DynamoDB | 4 | 저장/조회/멀티턴/삭제 |
| WebSocket | 1 | 6종 이벤트 스트리밍 |
| E2E UI | 10 | Chat/Admin/Sidebar 전체 시나리오 |
| **Total** | **20** | |

## 성능 기준 (PoC)

| 항목 | 기준 |
|------|------|
| Health API p95 | < 50ms |
| Agent E2E (Text2SQL) | < 12s |
| Agent E2E (RAG/GraphRAG/Cypher) | < 15s |
| 5명 동시 요청 | 모두 < 15s |
| 단일 대화 비용 | ~$0.012 |
| 월간 예상 비용 (100 대화/일) | ~$36 |

## 알려진 제약/주의사항

1. **Bedrock 리전**: us-east-1에서 Claude Sonnet + Titan Embed v2 모델 접근 권한 필요
2. **Neptune OpenCypher**: Neptune 엔진 1.2.0+ 필요 (OpenCypher 지원)
3. **OpenSearch Serverless**: aoss 서비스 데이터 접근 정책 설정 필요
4. **DynamoDB**: PAY_PER_REQUEST (PoC), 프로덕션 시 프로비저닝 고려
5. **Nginx Basic Auth**: .htpasswd 파일은 실제 비밀번호로 재생성 필요
6. **GraphRAG toolkit**: graphrag-toolkit 버전 호환성 확인 (>=3.16)
7. **strands-agents**: SDK 버전에 따라 import 경로 변경 가능
