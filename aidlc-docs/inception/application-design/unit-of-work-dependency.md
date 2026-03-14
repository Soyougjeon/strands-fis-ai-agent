# Unit of Work Dependencies

## Dependency Matrix

| Unit | Depends On | Depended By | Integration Point |
|------|-----------|-------------|-------------------|
| Unit 1: Mock Data Pipeline | External AWS Services only | Unit 2 (데이터 존재 전제) | Aurora PG 테이블, Neptune 인덱스, OpenSearch 인덱스 |
| Unit 2: Agent Backend | Unit 1 (적재된 데이터) | Unit 3 (API 호출) | REST API (port 8000), WebSocket (/ws/chat) |
| Unit 3: Frontend | Unit 2 (API 서버) | External users | HTTP (port 80/Nginx) |

## Dependency Flow

```
Unit 1: Mock Data Pipeline
  |
  | (Aurora PG 테이블, Neptune 인덱스, OpenSearch 인덱스)
  v
Unit 2: Agent Backend
  |
  | (REST API port 8000, WebSocket /ws/chat)
  v
Unit 3: Frontend + Nginx
  |
  | (HTTP port 80)
  v
External Users (5명 내부 테스터)
```

## Development Order

| Phase | Unit | Prerequisite | 완료 조건 |
|-------|------|-------------|-----------|
| 1 | Mock Data Pipeline | AWS 서비스 접근 가능 | DB/인덱스에 Mock 데이터 적재 완료 |
| 2 | Agent Backend | Unit 1 완료 (데이터 존재) | 10개 API 엔드포인트 동작, Agent 4 Tool 정상 |
| 3 | Frontend | Unit 2 완료 (API 동작) | 3개 탭 UI 렌더링, 스트리밍 대화 동작 |

## Integration Strategy

### Unit 1 -> Unit 2 Integration
- **Type**: Data dependency (간접)
- **Interface**: Aurora PG 테이블 스키마, Neptune 그래프 스키마, OpenSearch 인덱스 매핑
- **Validation**: Unit 2 개발 시 Unit 1이 적재한 데이터로 Tool 테스트

### Unit 2 -> Unit 3 Integration
- **Type**: API dependency (직접)
- **Interface**: REST endpoints (10개) + WebSocket (/ws/chat)
- **Contract**: Pydantic 스키마 (ChatRequest/Response, AgentEvent 등)
- **Validation**: Frontend에서 실제 API 호출로 통합 테스트

## Shared Resources

| Resource | Unit 1 | Unit 2 | Unit 3 |
|----------|--------|--------|--------|
| Aurora PostgreSQL | Write (INSERT) | Read/Write (Query + Conv + Token) | - |
| Neptune DB | Write (GraphRAG 인덱싱) | Read (GraphRAG + OpenCypher 쿼리) | - |
| OpenSearch | Write (RAG + GraphRAG 인덱싱) | Read (RAG + GraphRAG 검색) | - |
| Bedrock Titan | Embed (인덱싱용) | Embed (쿼리용) | - |
| Bedrock Claude | - | LLM (Agent) | - |
| config.py | AWS 연결 설정 | AWS 연결 설정 | - |
