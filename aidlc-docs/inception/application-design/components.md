# Component Definitions

## Component Overview

```
+------------------------------------------------------------------+
|                         EC2 Instance                              |
|                                                                    |
|  +------------------+        +-------------------------------+    |
|  | C1: Web Server   |        | C2: API Server                |    |
|  | (Nginx)          | -----> | (FastAPI)                     |    |
|  +------------------+        +-------------------------------+    |
|                                |           |           |          |
|                         +------+    +------+    +------+          |
|                         v           v           v                 |
|                   +-----------+ +--------+ +-----------+          |
|                   | C3: Agent | | C5:    | | C6:       |          |
|                   | Engine    | | Chat   | | Token     |          |
|                   +-----------+ | Manager| | Tracker   |          |
|                     |           +--------+ +-----------+          |
|              +------+------+                                      |
|              v      v      v                                      |
|         +------+ +-----+ +------+                                 |
|         | C4a  | | C4b | | C4c  |                                 |
|         | SQL  | | RAG | | Graph|                                 |
|         | Tool | | Tool| | Tools|                                 |
|         +------+ +-----+ +------+                                 |
|                                                                    |
|  +-------------------------------+                                |
|  | C7: Mock Data Pipeline        |                                |
|  +-------------------------------+                                |
+------------------------------------------------------------------+
         |              |              |              |
         v              v              v              v
    Aurora PG       OpenSearch     Neptune DB      Bedrock
```

---

## C1: Web Server (Nginx)

- **Purpose**: 정적 파일 서빙, API/WebSocket 리버스 프록시, Basic Auth
- **Responsibilities**:
  - React SPA 정적 파일 서빙 (/)
  - FastAPI API 프록시 (/api/*)
  - WebSocket 프록시 (/ws/*)
  - Basic Auth 접근 제어
- **Type**: Infrastructure

## C2: API Server (FastAPI)

- **Purpose**: REST/WebSocket API 제공, 요청 라우팅, 응답 스트리밍
- **Responsibilities**:
  - HTTP 엔드포인트 관리 (10개 API)
  - WebSocket 연결 관리 (스트리밍 대화)
  - Agent Engine 호출 및 응답 전달
  - CORS, 에러 핸들링
- **Type**: Application (Entry Point)
- **Dependencies**: C3, C5, C6

## C3: Agent Engine (Orchestrator)

- **Purpose**: Strands Agent 기반 Orchestrator - Intent 분류, Tool 라우팅, 응답 생성
- **Responsibilities**:
  - 사용자 질의 수신
  - Intent 분류 (ETF / Bond / Fund)
  - 적절한 Tool 선택 및 실행
  - 멀티턴 대화 컨텍스트 관리
  - 실행 과정 투명성 데이터 수집 (단계별 시간/토큰/비용)
  - 스트리밍 응답 생성
- **Type**: Application (Core)
- **Dependencies**: C4a, C4b, C4c, C4d, Bedrock

## C4a: Text2SQL Tool

- **Purpose**: 자연어 -> SQL 변환 및 Aurora PostgreSQL 쿼리 실행
- **Responsibilities**:
  - 자연어를 SQL로 변환 (LLM 활용)
  - Aurora PG 쿼리 실행 (ETF/채권/펀드 테이블)
  - 결과를 구조화된 형태로 반환
  - 쿼리/결과 메타데이터 수집
- **Type**: Application (Tool)
- **Dependencies**: Aurora PostgreSQL

## C4b: RAG Tool

- **Purpose**: MD 문서 벡터 검색 (OpenSearch만 사용)
- **Responsibilities**:
  - 질의 임베딩 생성 (Titan Embed v2)
  - OpenSearch kNN 검색 (rag-etf/bond/fund 인덱스)
  - Top-K 관련 청크 반환
  - 검색 쿼리/결과 메타데이터 수집
- **Type**: Application (Tool)
- **Dependencies**: OpenSearch Serverless, Bedrock (Titan)

## C4c: GraphRAG Tool

- **Purpose**: LexicalGraph 기반 벡터 검색 + 그래프 탐색
- **Responsibilities**:
  - LexicalGraphQueryEngine 실행
  - 테넌트별 검색 (ETF/Bond/Fund)
  - 벡터 유사도 + 그래프 관계 결합 응답
  - 실행 단계별 함수/중간결과 수집
- **Type**: Application (Tool)
- **Dependencies**: Neptune DB, OpenSearch Serverless, Bedrock

## C4d: OpenCypher Tool

- **Purpose**: Neptune 그래프 직접 쿼리 (OpenCypher)
- **Responsibilities**:
  - 자연어 -> OpenCypher 변환 (LLM 활용)
  - Neptune 직접 쿼리 실행 (테넌트별)
  - 노드/엣지 결과 반환
  - 시각화용 그래프 데이터 구조 반환
  - 쿼리/결과 메타데이터 수집
- **Type**: Application (Tool)
- **Dependencies**: Neptune DB

## C5: Conversation Manager

- **Purpose**: 대화 세션 및 메시지 영구 저장/조회
- **Responsibilities**:
  - 대화 세션 CRUD
  - 메시지 저장 (사용자 입력 + Agent 응답)
  - 메타데이터 저장 (intent, tools_used, latency, 단계별 토큰/비용)
  - 대화 이력 조회 (목록, 상세, 검색)
- **Type**: Application (Service)
- **Dependencies**: Aurora PostgreSQL

## C6: Token Tracker

- **Purpose**: LLM 토큰 사용량 및 비용 추적
- **Responsibilities**:
  - 요청별 토큰 사용량 기록 (input/output 분리)
  - 비용 계산 (모델별 단가 적용)
  - 단계별 추적 (Intent/Tool/Query/Response)
  - 통계 집계 (일별/누적/모델별)
- **Type**: Application (Service)
- **Dependencies**: Aurora PostgreSQL

## C7: Mock Data Pipeline

- **Purpose**: ETF/채권/펀드 Mock 데이터 생성 및 적재
- **Responsibilities**:
  - Mock CSV 파일 생성 (ETF/Bond/Fund)
  - Mock MD 파일 생성 (GraphRAG/RAG 인덱싱용)
  - CSV -> Aurora PostgreSQL INSERT
  - MD -> GraphRAG 인덱싱 (기존 indexer.py, Neptune 멀티테넌시)
  - MD -> RAG 인덱싱 (Chunking -> Titan Embed -> OpenSearch)
- **Type**: Application (Pipeline)
- **Dependencies**: Aurora PostgreSQL, Neptune DB, OpenSearch, Bedrock (Titan)

## C8: Frontend (React SPA)

- **Purpose**: 챗봇 Web UI, 시각화, Admin 대시보드
- **Responsibilities**:
  - 상단 멀티탭 (Chat / Graph Network / Admin)
  - 코글 사이드바 (대화 이력 + 예시 쿼리)
  - Chat 탭: 2분할 (Chat Area + Agent Process)
  - Graph Network 탭: 테넌트별 그래프 시각화 [ETF][채권][펀드]
  - Admin 탭: 대화 이력 관리, 토큰 사용량/비용 대시보드
  - 동적 차트 (ECharts/Plotly.js)
  - 그래프 네트워크 (Cytoscape.js)
  - 스트리밍 응답 렌더링
  - Agent 실행 과정 패널 (상세 탭: OpenCypher/OpenSearch/GraphRAG/SQL/결과)
  - 마크다운 렌더링
- **Type**: Application (Frontend)
- **Dependencies**: C2 (API Server)
