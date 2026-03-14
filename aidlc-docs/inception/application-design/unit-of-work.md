# Unit of Work Definitions

## Overview
시스템을 3개 유닛으로 분해하여 의존성 순서대로 순차 개발한다.
코드 조직: 모노레포 (backend/, frontend/, pipeline/ 최상위 분리)

---

## Unit 1: Mock Data Pipeline

### Summary
| 항목 | 내용 |
|------|------|
| **목적** | ETF/채권/펀드 Mock 데이터 생성 및 DB/인덱스 적재 |
| **Components** | C7: Mock Data Pipeline |
| **Services** | S7: Mock Data Service |
| **개발 순서** | 1st (선행 의존성 없음) |

### Responsibilities
- ETF/채권/펀드 Mock CSV 파일 생성
- ETF/채권/펀드 Mock MD 파일 생성 (GraphRAG/RAG 인덱싱용)
- CSV -> Aurora PostgreSQL INSERT (기존 ETF 테이블 + 신규 채권/펀드 테이블)
- MD -> Neptune GraphRAG 인덱싱 (멀티테넌시: ETF/Bond/Fund)
- MD -> OpenSearch RAG 인덱싱 (벡터 검색: rag-etf/bond/fund)

### Code Structure
```
pipeline/
  ├── generators/
  │   ├── etf_generator.py      # ETF Mock CSV/MD 생성
  │   ├── bond_generator.py     # 채권 Mock CSV/MD 생성
  │   └── fund_generator.py     # 펀드 Mock CSV/MD 생성
  ├── loaders/
  │   ├── db_loader.py          # CSV -> Aurora PG INSERT
  │   ├── graphrag_indexer.py   # MD -> Neptune 인덱싱 (기존 indexer.py 참조)
  │   └── rag_indexer.py        # MD -> OpenSearch 벡터 인덱싱
  ├── data/
  │   └── mock/                 # 생성된 CSV/MD 파일
  ├── main.py                   # CLI 진입점 (run_all)
  └── requirements.txt
```

### External Dependencies
- Aurora PostgreSQL (CSV INSERT)
- Neptune DB (GraphRAG 인덱싱, 멀티테넌시)
- OpenSearch Serverless (RAG 벡터 인덱싱)
- Amazon Bedrock Titan Embed v2 (임베딩 생성)

### Deliverables
- Mock CSV 파일 (ETF/채권/펀드)
- Mock MD 파일 (GraphRAG/RAG용)
- DB 적재 완료 (Aurora PG 테이블)
- GraphRAG 인덱스 완료 (Neptune 3개 테넌트)
- RAG 인덱스 완료 (OpenSearch 3개 인덱스)

---

## Unit 2: Agent Backend

### Summary
| 항목 | 내용 |
|------|------|
| **목적** | Strands Agent + FastAPI 백엔드 (모놀리식) |
| **Components** | C2(FastAPI), C3(Agent Engine), C4a-d(4 Tools), C5(Conv Manager), C6(Token Tracker) |
| **Services** | S1(Chat), S2(Agent), S3(Data Access), S4(Conv), S5(Token), S6(Visualization) |
| **개발 순서** | 2nd (Unit 1 데이터 필요) |

### Responsibilities
- FastAPI REST/WebSocket API 서버 (10개 엔드포인트)
- Strands Agent Orchestrator (Intent Detection -> Tool Selection -> Response)
- Text2SQL Tool (자연어 -> SQL -> Aurora PG)
- RAG Tool (벡터 검색 -> OpenSearch kNN)
- GraphRAG Tool (LexicalGraph -> Neptune + OpenSearch)
- OpenCypher Tool (자연어 -> Cypher -> Neptune)
- 대화 세션/메시지 CRUD (Aurora PG)
- 토큰 사용량/비용 추적 (Aurora PG)
- 시각화 데이터 변환 (Graph -> Cytoscape.js, SQL -> Chart)
- WebSocket 스트리밍 (AgentEvent 실시간 전달)

### Code Structure
```
backend/
  ├── api/
  │   ├── main.py               # FastAPI app, CORS, 라우터 등록
  │   ├── routes/
  │   │   ├── chat.py           # POST /api/chat, WS /ws/chat
  │   │   ├── conversations.py  # GET/DELETE /api/conversations
  │   │   ├── visualize.py      # GET /api/visualize/graph, /chart
  │   │   ├── admin.py          # GET /api/admin/*
  │   │   └── examples.py       # GET /api/examples
  │   └── schemas.py            # Pydantic 요청/응답 모델
  ├── agent/
  │   ├── engine.py             # C3: Strands Agent 생성/실행
  │   ├── events.py             # AgentEvent 타입 정의
  │   └── prompts.py            # System prompt, Intent/Tool 프롬프트
  ├── tools/
  │   ├── text2sql.py           # C4a: Text2SQL Tool
  │   ├── rag.py                # C4b: RAG Tool
  │   ├── graphrag.py           # C4c: GraphRAG Tool
  │   └── opencypher.py         # C4d: OpenCypher Tool
  ├── services/
  │   ├── chat_service.py       # S1: Chat 흐름 조율
  │   ├── agent_service.py      # S2: Agent 관리
  │   ├── data_access.py        # S3: Tool 실행 위임
  │   ├── conversation.py       # S4: 대화 이력 CRUD
  │   ├── token_tracker.py      # S5: 토큰/비용 추적
  │   └── visualization.py      # S6: 시각화 데이터
  ├── models/
  │   ├── database.py           # SQLAlchemy 엔진/세션
  │   ├── etf.py                # ETF ORM (기존 참조)
  │   ├── bond.py               # 채권 ORM (신규)
  │   ├── fund.py               # 펀드 ORM (신규)
  │   ├── conversation.py       # 대화 ORM
  │   └── token_usage.py        # 토큰 사용량 ORM
  ├── config.py                 # 환경설정
  └── requirements.txt
```

### External Dependencies
- Aurora PostgreSQL (SQL 쿼리, 대화 이력, 토큰 기록)
- Neptune DB (GraphRAG, OpenCypher 쿼리)
- OpenSearch Serverless (RAG, GraphRAG 벡터 검색)
- Amazon Bedrock (Claude Sonnet - LLM, Titan Embed v2 - 임베딩)

### Deliverables
- FastAPI 서버 (REST + WebSocket)
- Strands Agent (3 Intent x 4 Tool)
- 스트리밍 응답 (6종 AgentEvent)
- 대화 이력 관리 API
- 토큰 사용량/비용 통계 API
- 시각화 데이터 API

---

## Unit 3: Frontend

### Summary
| 항목 | 내용 |
|------|------|
| **목적** | React + TypeScript 챗봇 Web UI |
| **Components** | C1(Nginx), C8(Frontend React SPA) |
| **Services** | - |
| **개발 순서** | 3rd (Unit 2 API 필요) |

### Responsibilities
- React SPA (Chat / Graph Network / Admin 탭)
- 코글 사이드바 (대화 이력 + 예시 쿼리)
- Chat 탭: 2분할 (Chat Area + Agent Process Panel)
- Agent Process Panel: 단계별 시간/토큰/비용 + 상세 탭 (OpenCypher/OpenSearch/GraphRAG/SQL/결과)
- Graph Network 탭: 테넌트별 서브탭 [ETF][채권][펀드] + Cytoscape.js
- Admin 탭: 토큰 사용량/비용 대시보드 + 대화 이력 관리
- 동적 차트 (ECharts/Plotly.js)
- 마크다운 렌더링 + 코드 하이라이팅
- WebSocket 스트리밍 수신/렌더링
- Nginx 설정 (정적 파일 서빙, API/WS 프록시, Basic Auth)

### Code Structure
```
frontend/
  ├── src/
  │   ├── components/
  │   │   ├── App.tsx                # 상단 탭 네비게이션
  │   │   ├── sidebar/
  │   │   │   └── CoggleSidebar.tsx  # 접기/펼치기 사이드바
  │   │   ├── chat/
  │   │   │   ├── ChatPanel.tsx      # 대화 메시지 + 입력
  │   │   │   ├── AgentProcessPanel.tsx  # 실행 과정 패널
  │   │   │   └── DetailTabs.tsx     # 상세 탭 (쿼리/결과)
  │   │   ├── visualization/
  │   │   │   ├── DynamicChart.tsx   # ECharts/Plotly 차트
  │   │   │   ├── GraphNetwork.tsx   # Cytoscape.js 그래프
  │   │   │   └── GraphNetworkPage.tsx  # 테넌트별 서브탭
  │   │   ├── admin/
  │   │   │   └── AdminDashboard.tsx # 토큰/대화 관리
  │   │   └── common/
  │   │       └── MarkdownRenderer.tsx  # 마크다운 렌더링
  │   ├── hooks/
  │   │   ├── useWebSocket.ts       # WebSocket 연결 관리
  │   │   └── useApi.ts             # REST API 호출
  │   ├── types/
  │   │   └── index.ts              # TypeScript 타입 정의
  │   ├── App.tsx
  │   └── main.tsx
  ├── public/
  ├── package.json
  └── vite.config.ts

nginx/
  ├── nginx.conf                    # 메인 설정
  ├── .htpasswd                     # Basic Auth 사용자
  └── conf.d/
      └── default.conf              # 사이트 설정
```

### External Dependencies
- Unit 2 API (REST + WebSocket)

### Deliverables
- React SPA 빌드 (정적 파일)
- Nginx 설정 (프록시 + Basic Auth)
- 3개 탭 UI (Chat, Graph Network, Admin)
- 실시간 스트리밍 대화
- 동적 차트/그래프 시각화
