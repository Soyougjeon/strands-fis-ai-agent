# Code Generation Plan - Unit 2: Agent Backend

## Unit Context
- **Unit**: Unit 2 - Agent Backend (모놀리식)
- **Code Location**: `backend/` (workspace root)
- **Requirements**: FR-01, FR-03, FR-05, FR-06 + NFR-01, NFR-05
- **Dependencies**: Unit 1 (데이터), AWS Services (Bedrock, Aurora PG, Neptune, OpenSearch, DynamoDB)

## Generation Steps

### Project Structure Setup
- [x] Step 1: `backend/` 디렉토리 구조 + `requirements.txt`
- [x] Step 2: `backend/config.py` - 환경 설정

### Pydantic Schemas
- [x] Step 3: `backend/api/schemas.py` - 요청/응답/이벤트 모델

### Agent Core
- [x] Step 4: `backend/agent/prompts.py` - System Prompt (Intent/Tool/SQL/Cypher)
- [x] Step 5: `backend/agent/events.py` - AgentEvent 타입 정의
- [x] Step 6: `backend/agent/engine.py` - Strands Agent 생성/실행/스트리밍

### Tools
- [x] Step 7: `backend/tools/text2sql.py` - Text2SQL Tool (Few-shot + Aurora PG)
- [x] Step 8: `backend/tools/rag.py` - RAG Tool (Titan Embed + OpenSearch kNN)
- [x] Step 9: `backend/tools/graphrag.py` - GraphRAG Tool (LexicalGraph)
- [x] Step 10: `backend/tools/opencypher.py` - OpenCypher Tool (Neptune)

### Services
- [x] Step 11: `backend/services/agent_service.py` - Agent 관리/실행
- [x] Step 12: `backend/services/chat_service.py` - Chat 흐름 조율
- [x] Step 13: `backend/services/conversation.py` - DynamoDB 대화 CRUD (1테이블)
- [x] Step 14: `backend/services/token_tracker.py` - 토큰/비용 계산 + 통계
- [x] Step 15: `backend/services/visualization.py` - Graph/Chart 변환
- [x] Step 16: `backend/services/data_access.py` - Tool 실행 위임 + DB 연결

### API Layer
- [x] Step 17: `backend/api/routes/chat.py` - POST /api/chat + WS /ws/chat
- [x] Step 18: `backend/api/routes/conversations.py` - 대화 CRUD
- [x] Step 19: `backend/api/routes/visualize.py` - 그래프/차트 API
- [x] Step 20: `backend/api/routes/admin.py` - Admin API
- [x] Step 21: `backend/api/routes/examples.py` - 예시 쿼리 API
- [x] Step 22: `backend/api/main.py` - FastAPI app, CORS, 라우터 등록

### Tests
- [x] Step 23: `backend/tests/test_agent.py` - Agent 단위 테스트
- [x] Step 24: `backend/tests/test_services.py` - Service 단위 테스트
- [x] Step 25: `backend/tests/test_api.py` - API 엔드포인트 테스트

### Documentation
- [x] Step 26: `aidlc-docs/construction/unit-2-agent-backend/code/code-summary.md`

## Story Traceability
| Step | Requirements |
|------|-------------|
| Step 4-6 | FR-01-01, FR-01-02, FR-01-03 (Agent, Intent, Orchestration) |
| Step 7 | FR-01-04 Text2SQL |
| Step 8 | FR-01-04 RAG |
| Step 9 | FR-01-04 GraphRAG |
| Step 10 | FR-01-04 OpenCypher |
| Step 5,6 | FR-01-06, FR-01-07 (스트리밍, 투명성) |
| Step 13 | FR-06-01~05 (대화 이력) |
| Step 14 | FR-05-01~03 (토큰/비용) |
| Step 17 | FR-03-02, FR-03-03 (Chat API) |
| Step 18 | FR-03-04~06 (Conversations API) |
| Step 19 | FR-03-07~08 (Visualization API) |
| Step 20 | FR-03-09~10 (Admin API) |
