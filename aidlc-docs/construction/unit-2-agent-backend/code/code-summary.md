# Code Summary - Unit 2: Agent Backend

## Overview
FastAPI 기반 금융 데이터 분석 AI Agent 백엔드. Bedrock Claude Sonnet으로 Intent Detection, Tool Selection, Response Generation을 수행하고, 4가지 데이터 접근 도구(Text2SQL, RAG, GraphRAG, OpenCypher)를 통해 금융 데이터를 조회합니다.

## File Structure (20 files)

```
backend/
├── config.py                          # 환경 설정 (AWS, DB, LLM, Pricing)
├── requirements.txt                   # Python 의존성
├── agent/
│   ├── engine.py                      # AgentEngine - 4단계 오케스트레이션
│   ├── events.py                      # SSE 이벤트 팩토리 (6 types)
│   └── prompts.py                     # System Prompts, Schema/FewShot/Graph 맵
├── tools/
│   ├── text2sql.py                    # Text2SQL (Few-shot SQL + Aurora PG)
│   ├── rag.py                         # RAG (Titan Embed + OpenSearch kNN)
│   ├── graphrag.py                    # GraphRAG (LexicalGraph toolkit)
│   └── opencypher.py                  # OpenCypher (Neptune 그래프 쿼리)
├── services/
│   ├── agent_service.py               # Agent 생명주기 관리
│   ├── chat_service.py                # Chat 흐름 조율 + 턴 저장
│   ├── conversation.py                # DynamoDB 1테이블 CRUD
│   ├── token_tracker.py               # 토큰/비용 계산 + 기간별 집계
│   ├── visualization.py               # Graph/Chart 자동 변환
│   └── data_access.py                 # Tool 레지스트리
├── api/
│   ├── main.py                        # FastAPI app, CORS, 라우터
│   ├── schemas.py                     # Pydantic 모델
│   └── routes/
│       ├── chat.py                    # POST /api/chat + WS /ws/chat
│       ├── conversations.py           # 대화 CRUD API
│       ├── visualize.py               # 그래프/차트 API
│       ├── admin.py                   # Admin 토큰 통계 API
│       └── examples.py               # 예시 쿼리 API
└── tests/
    ├── test_agent.py                  # Agent 코어 테스트
    ├── test_services.py               # 서비스 테스트
    └── test_api.py                    # API 엔드포인트 테스트

## Key Design Decisions

1. **Agent Loop**: Intent Detection → Tool Selection → Tool Execution → Response Generation (4-step sequential)
2. **DynamoDB 1-Table**: conversation_turns (PK=session_id, SK=turn_id), 각 턴에 전체 JSON 저장
3. **SQL/Cypher Safety**: 읽기 전용 검증 (FORBIDDEN pattern regex), 자동 LIMIT 추가
4. **Chart Auto-Detection**: SQL 결과 컬럼 타입 분석으로 bar/line/pie 자동 결정
5. **Context Management**: 요약(LLM, 3턴마다 갱신) + 최근 3턴 원문

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/chat | 동기 채팅 |
| WS | /ws/chat | 스트리밍 채팅 |
| GET | /api/conversations | 대화 목록 |
| GET | /api/conversations/{id} | 대화 상세 |
| DELETE | /api/conversations/{id} | 대화 삭제 |
| GET | /api/visualize/graph/{sid}/{tid} | 그래프 데이터 |
| GET | /api/visualize/chart/{sid}/{tid} | 차트 데이터 |
| GET | /api/admin/token-usage | 토큰 통계 |
| GET | /api/admin/conversations | Admin 대화 |
| GET | /api/examples | 예시 쿼리 |
| GET | /api/health | 헬스체크 |

## Requirements Coverage

| Requirement | Files |
|-------------|-------|
| FR-01 Agent | engine.py, prompts.py, events.py |
| FR-01-04 Tools | text2sql.py, rag.py, graphrag.py, opencypher.py |
| FR-03 API | chat.py, conversations.py, visualize.py, admin.py, examples.py |
| FR-05 Token | token_tracker.py |
| FR-06 History | conversation.py, chat_service.py |
| NFR-01 Performance | SQL timeout, LIMIT, streaming |
| NFR-05 Korean | prompts.py (한국어 System Prompt) |
```
