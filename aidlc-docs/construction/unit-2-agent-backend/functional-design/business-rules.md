# Business Rules - Unit 2: Agent Backend

## BR-01: Agent Orchestration Rules

### BR-01-01: Intent Detection
- Intent는 반드시 ETF/Bond/Fund 중 하나
- confidence < 0.5 → 사용자에게 "어떤 도메인을 질의하시나요?" 재질의
- Intent Detection 실패 시 기본값 없음 (재질의 필수)

### BR-01-02: Tool Selection
- LLM이 4가지 Tool 중 자동 선택 (System Prompt 기반)
- 선택 결과와 이유를 UI에 표시
- Tool 실행 실패 시 에러 메시지 반환 (다른 Tool 자동 fallback 없음)

### BR-01-03: Response Generation
- Tool 결과 + 원본 질문 + 컨텍스트로 최종 응답 생성
- 한국어로 응답 (NFR-05)
- 스트리밍: 토큰 단위로 WebSocket 전송

## BR-02: SQL Safety Rules

### BR-02-01: SQL 허용 목록
- SELECT만 허용
- INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE → 차단
- UNION은 허용 (서브쿼리 포함)

### BR-02-02: SQL 제한
- LIMIT 없으면 자동 추가 (LIMIT 100)
- 실행 타임아웃: 10초
- 결과 최대 1000 rows

## BR-03: Cypher Safety Rules

### BR-03-01: Cypher 허용 목록
- MATCH, RETURN, WHERE, ORDER BY, LIMIT만 허용
- CREATE, DELETE, SET, REMOVE, MERGE → 차단

### BR-03-02: Cypher 제한
- LIMIT 없으면 자동 추가 (LIMIT 50)
- 반드시 tenant 필터 포함: WHERE n.__tenant__ = '{tenant}'

## BR-04: DynamoDB Rules

### BR-04-01: 턴 저장 (1테이블)
- 답변 완료 후 한번에 JSON 저장 (부분 저장 없음)
- session_id(PK) + turn_id(SK)로 고유 식별
- 각 턴에 session_title, context_summary 포함 (최신값)
- agent_process에 모든 단계 정보 포함 (빈 단계는 null)

### BR-04-02: 세션 관리
- 세션은 첫 턴 저장 시 자동 생성 (별도 세션 테이블 없음)
- session_title은 첫 질문에서 자동 생성 (최대 50자)
- 삭제 시 해당 session_id의 모든 턴 BatchDelete

### BR-04-03: 컨텍스트 요약
- 3턴마다 context_summary 갱신 (LLM 요약)
- 요약 길이: 최대 500자
- 최신 요약은 마지막 턴의 context_summary에 저장
- Agent 호출 시: summary + 최근 3턴 원문 전달

## BR-05: Token Cost Rules

### BR-05-01: 비용 계산
| Model | Input | Output |
|-------|-------|--------|
| Claude Sonnet | $3.00 / 1M tokens | $15.00 / 1M tokens |
| Titan Embed v2 | $0.02 / 1M tokens | $0 |

### BR-05-02: 단계별 추적
- 각 LLM 호출마다 tokens_in, tokens_out, cost 기록
- Intent Detection, Tool Selection, Query Generation, Response Generation 각각 별도
- Query Execution은 LLM 호출 아님 → tokens 없고 latency만 기록

### BR-05-03: 통계 집계
- DynamoDB Scan으로 기간별 집계
- period: daily, weekly, monthly
- 집계 항목: tokens_in, tokens_out, cost, request_count

## BR-06: WebSocket Rules

### BR-06-01: 연결 관리
- 클라이언트당 1개 WebSocket 연결
- Heartbeat: 30초 ping/pong
- 연결 끊김 시 자동 재연결은 클라이언트 책임

### BR-06-02: 이벤트 순서
```
intent_detected → tool_selected → query_generated → query_executed
→ text_chunk (N개) → response_complete
```
- 각 이벤트에 timestamp 포함
- response_complete는 항상 마지막

## BR-07: Visualization Rules

### BR-07-01: Graph Data
- OpenCypher/GraphRAG 결과 → Cytoscape.js 호환 형식
- 노드: id, label, type, properties
- 엣지: source, target, label

### BR-07-02: Chart Data
- Text2SQL 결과 → 자동 차트 유형 결정
- 2컬럼 (문자+숫자) → bar chart
- 날짜+숫자 → line chart
- 비율 데이터 → pie chart
- 차트 불가 → chart_data = null (테이블만 표시)

## BR-08: API Rules

### BR-08-01: CORS
- 개발: localhost:3000, localhost:5173 허용
- 배포: EC2 도메인만 허용

### BR-08-02: Error Response
```json
{
  "error": {
    "code": "INTENT_DETECTION_FAILED",
    "message": "질의 의도를 파악할 수 없습니다. 다시 질문해주세요.",
    "detail": "confidence: 0.3"
  }
}
```

### BR-08-03: Example Queries
- pipeline/data/mock/example_queries.json 파일 읽기
- GET /api/examples → JSON 응답 (캐싱)
