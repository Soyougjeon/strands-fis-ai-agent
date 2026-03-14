# Functional Design Plan - Unit 2: Agent Backend

## Plan Steps

- [x] Step 1: Strands Agent 오케스트레이션 로직 (Intent -> Tool -> Response)
- [x] Step 2: Intent Detection 비즈니스 로직 (ETF/Bond/Fund 분류)
- [x] Step 3: Tool Selection 비즈니스 로직 (LLM 자동 선택)
- [x] Step 4: Text2SQL Tool 비즈니스 로직 (스키마 매핑 + Few-shot SQL)
- [x] Step 5: RAG Tool 비즈니스 로직 (임베딩, kNN 검색, 결과 처리)
- [x] Step 6: GraphRAG Tool 비즈니스 로직 (LexicalGraph 질의)
- [x] Step 7: OpenCypher Tool 비즈니스 로직 (Cypher 생성, Neptune 실행)
- [x] Step 8: Agent Event 스트리밍 모델 (WebSocket 이벤트 흐름)
- [x] Step 9: Conversation Service 비즈니스 로직 (DynamoDB JSON 저장)
- [x] Step 10: Token Tracker 비즈니스 로직 (JSON 내 embedded)
- [x] Step 11: FastAPI 엔드포인트 상세 (요청/응답 스키마)
- [x] Step 12: Visualization Service 비즈니스 로직 (그래프/차트 변환)

## Clarifying Questions

### Q1: Strands Agent Tool 선택 전략
[Answer]: A - LLM 자동 선택 (System Prompt에 Tool 특성 명시). UI에서 선택된 Tool과 해당 쿼리 표시.

### Q2: Text2SQL 스키마 제공 방식
[Answer]: C - Intent별 관련 테이블 스키마 + 예시 SQL (Few-shot)

### Q3: 멀티턴 대화 컨텍스트 관리
[Answer]: C - 요약된 컨텍스트 + 최근 3턴

### 아키텍처 변경: 대화 저장소
- 변경: Aurora PG → DynamoDB
- 형태: 턴별 하나의 JSON (질문 + 실행 과정 + 쿼리 + 답변 통합)
- 저장 시점: 답변 완료 후 한번에 저장
- 토큰 사용량: JSON 내 embedded (별도 테이블 X)
