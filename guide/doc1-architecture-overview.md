# Doc 1: Architecture Overview

## 1. 시스템 개요

Strands FIS는 금융 데이터 AI 챗봇 시스템이다. Strands Agents SDK 기반 Orchestrator 패턴으로 다수 도메인(ETF/Bond/Fund) × 4가지 데이터 접근 방식(Text2SQL/RAG/GraphRAG/OpenCypher)을 지원한다.

핵심 흐름:
```
User → React SPA → WebSocket → Nginx → FastAPI → Agent Engine
  → Intent Detection (도메인 분류)
  → Tool Selection (데이터 접근 방식 선택)
  → Tool Execution (DB 쿼리)
  → Response Generation (LLM 응답)
  → Streaming → UI 렌더링
```

## 2. 아키텍처 다이어그램

별도 파일: `strands-fis-architecture.drawio` (draw.io로 열기)

```
+------------------------------------------------------------------+
|                         EC2 Instance (t3.medium)                  |
|                                                                    |
|  +------------------+        +-------------------------------+    |
|  | C1: Nginx        |        | C2: FastAPI                   |    |
|  | - Static files   | -----> | - REST /api/*                 |    |
|  | - /api proxy     |        | - WebSocket /ws/chat          |    |
|  | - /ws proxy      |        +-------------------------------+    |
|  | - Basic Auth     |          |           |           |          |
|  +------------------+   +------+    +------+    +------+          |
|                         v           v           v                 |
|  +------------------+  +-----------+ +--------+ +-----------+     |
|  | C8: React SPA    |  | C3: Agent | | C5:    | | C6:       |     |
|  | - Chat tab       |  | Engine    | | Conv   | | Token     |     |
|  | - Graph tab      |  | (Strands) | | Mgr    | | Tracker   |     |
|  | - Admin tab      |  +-----------+ +--------+ +-----------+     |
|  +------------------+    |                                        |
|                   +------+------+------+                          |
|                   v      v      v      v                          |
|              +------+ +-----+ +------+ +--------+                 |
|              | C4a  | | C4b | | C4c  | | C4d    |                 |
|              | SQL  | | RAG | | Graph| | Cypher |                 |
|              | Tool | | Tool| | RAG  | | Tool   |                 |
|              +------+ +-----+ +------+ +--------+                 |
|                                                                    |
|  +-------------------------------+                                |
|  | C7: Mock Data Pipeline        |                                |
|  +-------------------------------+                                |
+------------------------------------------------------------------+
         |              |              |              |
         v              v              v              v
    Aurora PG       OpenSearch     Neptune DB      Bedrock
    (Serverless v2) (Serverless)   (Serverless)   (Claude+Titan)
```

## 3. 컴포넌트 목록

| ID | 컴포넌트 | 타입 | 역할 |
|----|---------|------|------|
| C1 | Nginx | Infrastructure | 정적 파일 서빙, 리버스 프록시, Basic Auth |
| C2 | FastAPI | Application (Entry) | REST/WebSocket API, 요청 라우팅 |
| C3 | Agent Engine | Application (Core) | Strands Agent Orchestrator — Intent→Tool→Response |
| C4a | Text2SQL Tool | Application (Tool) | 자연어 → SQL → Aurora PG |
| C4b | RAG Tool | Application (Tool) | 벡터 검색 (OpenSearch kNN) |
| C4c | GraphRAG Tool | Application (Tool) | LexicalGraph (Neptune + OpenSearch) |
| C4d | OpenCypher Tool | Application (Tool) | 자연어 → Cypher → Neptune |
| C5 | Conversation Manager | Application (Service) | 대화 세션/메시지 CRUD |
| C6 | Token Tracker | Application (Service) | 토큰 사용량/비용 추적 |
| C7 | Mock Data Pipeline | Application (Pipeline) | 도메인 Mock 데이터 생성/적재 |
| C8 | Frontend (React SPA) | Application (Frontend) | 챗봇 UI, 시각화, Admin |

## 4. 서비스 계층

| ID | 서비스 | 오케스트레이션 |
|----|--------|--------------|
| S1 | Chat Service | WebSocket → Agent → Conv → Token (전체 흐름 조율) |
| S2 | Agent Service | Intent Detection → Tool Selection → Response Generation |
| S3 | Data Access Service | S3a(SQL) + S3b(RAG) + S3c(GraphRAG) + S3d(OpenCypher) |
| S4 | Conversation Service | 세션/메시지 CRUD (DynamoDB) |
| S5 | Token Service | 단계별 토큰/비용 기록 및 통계 |
| S6 | Visualization Service | Neptune 그래프 → Cytoscape.js, SQL 결과 → Chart |
| S7 | Mock Data Service | CSV/MD 생성 → DB/인덱스 적재 파이프라인 |

## 5. 데이터 흐름

### 질의 처리 (런타임)
```
User → React → WebSocket → Nginx → FastAPI
  → S1: ChatService.handle_message()
    → S4: get_context(session_id)
    → S2: AgentEngine.process_message()
      → Bedrock: Intent+Tool 분류 (단일 LLM 호출)
        → IntentDetectedEvent (WebSocket 전송)
        → ToolSelectedEvent (WebSocket 전송)
      → C4x: Tool.execute(question, intent)
        → QueryGeneratedEvent (WebSocket 전송)
        → QueryExecutedEvent (WebSocket 전송)
      → Bedrock: 응답 생성 (스트리밍)
        → TextChunkEvent × N (WebSocket 전송)
      → ResponseCompleteEvent (WebSocket 전송)
    → S4: save_turn()
    → S5: record_usage()
```

### 데이터 적재 (파이프라인)
```
CSV 파일 → pipeline/loaders/db_loader.py → Aurora PostgreSQL INSERT
MD 파일  → pipeline/loaders/graphrag_indexer.py → Neptune (멀티테넌시) + OpenSearch (GraphRAG)
MD 파일  → pipeline/loaders/rag_indexer.py → OpenSearch (RAG 벡터)
```

## 6. 기술 스택

| 레이어 | 기술 |
|--------|------|
| Agent Framework | Strands Agents SDK |
| LLM | Amazon Bedrock Claude Sonnet |
| Embedding | Amazon Bedrock Titan Embed Text v2 (1024-dim) |
| Backend | Python 3.11 + FastAPI + Uvicorn |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| 차트 | ECharts (echarts-for-react) |
| 그래프 시각화 | Cytoscape.js (cose-bilkent layout) |
| 마크다운 | react-markdown + remark-gfm + react-syntax-highlighter |
| GraphRAG | graphrag-toolkit (LexicalGraph) |
| RDB | Aurora PostgreSQL (Serverless v2) |
| Graph DB | Neptune DB (Serverless, OpenCypher) |
| Vector Store | OpenSearch Serverless (AOSS) |
| 대화 이력 | DynamoDB (conversation_turns) |
| Web Server | Nginx (리버스 프록시 + Basic Auth) |
| 컨테이너 | Docker + Docker Compose |
| IaC | AWS CDK (TypeScript) |

## 7. 통신 프로토콜

| 경로 | 프로토콜 | 용도 |
|------|---------|------|
| User ↔ Nginx | HTTP/WS (port 80) | 웹 접근 |
| Nginx → FastAPI | HTTP/WS (port 8000) | 프록시 |
| FastAPI → Aurora PG | TCP/SSL (port 5432) | SQL 쿼리 |
| FastAPI → Neptune | HTTPS (port 8182) | OpenCypher/GraphRAG |
| FastAPI → OpenSearch | HTTPS (port 443) | kNN 벡터 검색 |
| FastAPI → Bedrock | HTTPS | LLM/Embedding API |
| FastAPI → DynamoDB | HTTPS | 대화 이력 CRUD |

## 8. 코드 구조

```
strands-fis/
├── backend/                    # Python 백엔드
│   ├── api/                    # FastAPI 라우터
│   │   ├── main.py             # App 엔트리
│   │   ├── routes/             # chat, conversations, visualize, admin, examples
│   │   └── schemas.py          # Pydantic 모델
│   ├── agent/                  # Strands Agent
│   │   ├── engine.py           # Agent Loop (Intent→Tool→Response)
│   │   ├── events.py           # AgentEvent 생성 함수
│   │   └── prompts.py          # 시스템 프롬프트, 스키마, Few-shot
│   ├── tools/                  # 4개 Tool
│   │   ├── text2sql.py         # NL → SQL → Aurora PG
│   │   ├── rag.py              # 벡터 검색 → OpenSearch
│   │   ├── graphrag.py         # LexicalGraph → Neptune+OpenSearch
│   │   └── opencypher.py       # NL → Cypher → Neptune
│   ├── services/               # 서비스 계층
│   │   ├── chat_service.py     # S1: 전체 흐름 조율
│   │   ├── agent_service.py    # S2: Agent 관리
│   │   ├── data_access.py      # S3: Tool 실행 위임
│   │   ├── conversation.py     # S4: 대화 이력 CRUD
│   │   ├── token_tracker.py    # S5: 토큰/비용 추적
│   │   └── visualization.py    # S6: 시각화 데이터
│   └── config.py               # 환경설정
├── frontend/                   # React SPA
│   └── src/
│       ├── components/         # chat/, visualization/, sidebar/, admin/, common/
│       ├── hooks/              # useWebSocket.ts, useApi.ts
│       ├── types/              # TypeScript 인터페이스
│       ├── App.tsx             # 탭 네비게이션 + 레이아웃
│       └── main.tsx            # 엔트리
├── pipeline/                   # 데이터 파이프라인
│   ├── generators/             # CSV/MD 생성기
│   ├── loaders/                # DB/인덱스 적재기
│   ├── models/                 # ORM 모델 + DDL
│   └── main.py                 # CLI 진입점
├── infra/                      # CDK IaC
│   ├── lib/                    # network-stack, data-stack, compute-stack
│   └── bin/infra.ts            # CDK 앱 엔트리
├── nginx/                      # Nginx 설정
├── Dockerfile                  # Backend 이미지
├── Dockerfile.frontend         # Frontend 이미지
└── docker-compose.yml          # 서비스 오케스트레이션
```

## 9. AWS 서비스 의존성

| 서비스 | 용도 | 접근 방식 |
|--------|------|----------|
| Aurora PostgreSQL (Serverless v2) | RDB 저장소 (도메인 테이블 + 대화/토큰) | SG 규칙, SSL, Secrets Manager |
| Neptune DB (Serverless) | Knowledge Graph (멀티테넌시) | SG 규칙, IAM Auth |
| OpenSearch Serverless (AOSS) | 벡터 검색 (6 인덱스: rag-*/graphrag-*) | IAM, VPC Endpoint |
| Amazon Bedrock | LLM (Claude Sonnet) + Embedding (Titan v2) | IAM Role |
| DynamoDB | 대화 이력 (conversation_turns) | IAM Role |
| Secrets Manager | Aurora PG 자격증명 | IAM Role |
| EC2 (t3.medium) | 애플리케이션 호스팅 | Public Subnet, EIP |
