# Application Design - Strands FIS Chatbot

## Overview

금융 데이터 AI 챗봇 시스템의 Application Design 문서. Strands Agents SDK 기반 Orchestrator 패턴으로 3개 Intent(ETF/Bond/Fund) x 4가지 데이터 접근 방식(Text2SQL/RAG/GraphRAG/OpenCypher)을 지원한다.

## Design Summary

### Component Architecture (9 Components)

| ID | Component | Type | Purpose |
|----|-----------|------|---------|
| C1 | Nginx | Infrastructure | 정적 파일 서빙, 리버스 프록시, Basic Auth |
| C2 | FastAPI | Application (Entry) | REST/WebSocket API, 요청 라우팅 |
| C3 | Agent Engine | Application (Core) | Strands Agent Orchestrator - Intent/Tool/Response |
| C4a | Text2SQL Tool | Application (Tool) | 자연어 -> SQL -> Aurora PG |
| C4b | RAG Tool | Application (Tool) | 벡터 검색 (OpenSearch kNN) |
| C4c | GraphRAG Tool | Application (Tool) | LexicalGraph (Neptune + OpenSearch) |
| C4d | OpenCypher Tool | Application (Tool) | 자연어 -> Cypher -> Neptune |
| C5 | Conversation Manager | Application (Service) | 대화 세션/메시지 CRUD |
| C6 | Token Tracker | Application (Service) | 토큰 사용량/비용 추적 |
| C7 | Mock Data Pipeline | Application (Pipeline) | ETF/Bond/Fund Mock 데이터 생성/적재 |
| C8 | Frontend (React SPA) | Application (Frontend) | 챗봇 UI, 시각화, Admin 대시보드 |

### Service Layer (7 Services)

| ID | Service | Orchestrates |
|----|---------|-------------|
| S1 | Chat Service | WebSocket -> Agent -> Conv -> Token (전체 흐름 조율) |
| S2 | Agent Service | Intent Detection -> Tool Selection -> Response Generation |
| S3 | Data Access Service | S3a(SQL) + S3b(RAG) + S3c(GraphRAG) + S3d(OpenCypher) |
| S4 | Conversation Service | 세션/메시지 CRUD (Aurora PG) |
| S5 | Token Service | 단계별 토큰/비용 기록 및 통계 (Aurora PG) |
| S6 | Visualization Service | Neptune 그래프 -> Cytoscape.js, SQL 결과 -> Chart |
| S7 | Mock Data Service | CSV/MD 생성 -> DB/인덱스 적재 파이프라인 |

### External Dependencies

| Service | Protocol | Purpose |
|---------|----------|---------|
| Aurora PostgreSQL | TCP/SSL (5432) | RDB 저장소 (ETF/Bond/Fund 테이블, 대화 이력, 토큰) |
| Neptune DB | HTTPS (8182) | 그래프 DB (멀티테넌시 3개: ETF/Bond/Fund) |
| OpenSearch Serverless | HTTPS (443) | 벡터 검색 (6 인덱스: rag-*/graphrag-*) |
| Amazon Bedrock | HTTPS | LLM (Claude Sonnet), 임베딩 (Titan Embed v2) |

### Key Design Decisions

1. **Agent Pattern**: Strands SDK Agent Loop - Intent Detection -> Tool Selection -> Execution -> Response
2. **Streaming**: WebSocket + AsyncGenerator로 Agent 실행 과정 실시간 전달
3. **Observability**: 모든 Agent 단계에서 AgentEvent 생성 (시간/토큰/비용 포함)
4. **Multi-tenancy**: Neptune에서 tenant 속성으로 ETF/Bond/Fund 분리
5. **Tool Result 표준화**: ToolResult 공통 타입으로 4가지 Tool 결과 통합

## Detailed Design Documents

- [Component Definitions](components.md) - 컴포넌트 정의 및 책임
- [Component Methods](component-methods.md) - 메서드 시그니처 및 데이터 타입
- [Service Definitions](services.md) - 서비스 계층 설계 및 오케스트레이션
- [Component Dependencies](component-dependency.md) - 의존성 매트릭스, 통신 프로토콜, 데이터 흐름

## Communication Flow Summary

```
User -> C8(React) -> WebSocket -> C1(Nginx) -> C2(FastAPI)
  -> S1: Chat Service
    -> S4: get_context(session_id)
    -> S2: process_message() -> AsyncGenerator[AgentEvent]
      -> detect_intent() -> IntentDetectedEvent
      -> select_tool() -> ToolSelectedEvent
      -> S3: execute_tool()
        -> S3a/b/c/d -> QueryGeneratedEvent + QueryExecutedEvent
      -> generate_response() -> TextChunkEvents
      -> ResponseCompleteEvent
    -> S4: add_message()
    -> S5: record_usage()
```
