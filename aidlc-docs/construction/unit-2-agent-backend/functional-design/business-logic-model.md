# Business Logic Model - Unit 2: Agent Backend

## 1. Agent Orchestration Flow

```
WebSocket /ws/chat 수신
  |
  v
S1: Chat Service
  |-- session_id 없으면 → 새 세션 생성 (DynamoDB)
  |-- session_id 있으면 → 기존 세션 조회
  |-- 컨텍스트 구성: 요약 + 최근 3턴 (DynamoDB에서 조회)
  |
  v
S2: Agent Service (Strands Agent Loop)
  |
  |-- Step 1: Intent Detection
  |   |-- System Prompt + 사용자 메시지 → LLM
  |   |-- 결과: intent (ETF/Bond/Fund), confidence
  |   |-- emit IntentDetectedEvent → WebSocket
  |
  |-- Step 2: Tool Selection
  |   |-- System Prompt (4 Tool 특성) + intent + 메시지 → LLM
  |   |-- 결과: tool_name, rationale
  |   |-- emit ToolSelectedEvent → WebSocket
  |
  |-- Step 3: Tool Execution
  |   |-- S3: Data Access Service → 해당 Tool 실행
  |   |-- emit QueryGeneratedEvent → WebSocket
  |   |-- emit QueryExecutedEvent → WebSocket
  |
  |-- Step 4: Response Generation
  |   |-- 컨텍스트 + Tool 결과 → LLM → 스트리밍 응답
  |   |-- emit TextChunkEvent (each chunk) → WebSocket
  |   |-- emit ResponseCompleteEvent → WebSocket
  |
  v
S1: Chat Service (후처리)
  |-- 턴 JSON 조립 (question + agent_process + response + total + session_title + context_summary)
  |-- DynamoDB PUT (conversation_turns) - 1테이블, 세션별 대화별 1아이템
```

## 2. Intent Detection

### System Prompt
```
당신은 금융 데이터 질의를 분류하는 전문가입니다.
사용자의 질문을 다음 3가지 Intent 중 하나로 분류하세요:

- ETF: TIGER ETF, 상장지수펀드, 인덱스 펀드 관련 질문
- Bond: 채권, 국채, 회사채, 금리, 신용등급 관련 질문
- Fund: 공모펀드, 뮤추얼펀드, 운용사, 펀드 수익률 관련 질문

반드시 JSON으로 응답: {"intent": "ETF|Bond|Fund", "confidence": 0.0~1.0}
```

### 로직
1. 사용자 메시지 + System Prompt → Bedrock Claude Sonnet
2. JSON 파싱 → intent, confidence 추출
3. confidence < 0.5 → 사용자에게 재질의 요청
4. latency, tokens 기록

## 3. Tool Selection

### System Prompt
```
사용자의 질문에 가장 적합한 데이터 접근 방식을 선택하세요:

1. text2sql: 정확한 수치 조회, 필터링, 집계, 정렬 (SQL)
   예: "AUM 상위 10개", "수익률 비교", "목록 보여줘"
2. rag: 비정형 문서 검색, 설명, 특성, 전략 (벡터 검색)
   예: "투자 전략은?", "위험 요소 설명", "차이점은?"
3. graphrag: 관계 탐색, 공통점, 연결 관계 (지식 그래프 + 벡터)
   예: "공통으로 보유한 종목", "관련 위험 요소의 관계"
4. opencypher: 그래프 직접 쿼리, 홉 탐색, 네트워크 시각화
   예: "2홉 연결 엔티티", "전체 네트워크 그래프"

JSON 응답: {"tool": "text2sql|rag|graphrag|opencypher", "rationale": "선택 이유"}
```

## 4. Text2SQL Tool

### 로직
1. Intent에 따른 스키마 매핑:
   - ETF → tiger_etf.etf_products, etf_holdings, etf_performance, etf_distributions
   - Bond → bond.bond_products, bond_prices
   - Fund → fund.fund_products, fund_holdings, fund_performance
2. Few-shot 프롬프트 구성:
   ```
   [스키마]
   {intent별 CREATE TABLE DDL}

   [예시]
   Q: {예시 질문1}
   SQL: {예시 SQL1}
   Q: {예시 질문2}
   SQL: {예시 SQL2}

   [질문]
   Q: {사용자 질문}
   SQL:
   ```
3. LLM → SQL 생성
4. SQL 검증 (SELECT만 허용, DROP/DELETE/UPDATE 차단)
5. Aurora PG 실행 → 결과 반환
6. 결과가 숫자 집계이면 chart_data 생성

### Few-shot 예시 (Intent별 3개)
ETF:
- "AUM 상위 5개 ETF" → SELECT name_ko, aum FROM tiger_etf.etf_products ORDER BY aum DESC LIMIT 5
- "반도체 ETF 보유종목" → SELECT p.name_ko, h.holding_name, h.weight_pct FROM tiger_etf.etf_products p JOIN tiger_etf.etf_holdings h ON ...
- "배당 ETF 분배금 이력" → SELECT p.name_ko, d.record_date, d.amount_per_share FROM ...

Bond:
- "AAA 등급 채권 목록" → SELECT name, coupon_rate, credit_rating FROM bond.bond_products WHERE credit_rating = 'AAA'
- "최근 수익률 변동 큰 채권" → SELECT bp.bond_code, ... FROM bond.bond_prices bp ...
- "회사채 발행금액 순위" → SELECT name, issuer, issue_amount FROM bond.bond_products WHERE issuer_type = '회사채' ORDER BY ...

Fund:
- "주식형 펀드 수익률 상위" → SELECT fp.name, perf.return_1y FROM fund.fund_products fp JOIN fund.fund_performance perf ON ...
- "총보수 1% 이하 펀드" → SELECT name, total_expense_ratio FROM fund.fund_products WHERE total_expense_ratio <= 1.0
- "벤치마크 대비 초과수익" → SELECT fp.name, perf.return_1y, perf.bm_return_1y, (perf.return_1y - perf.bm_return_1y) as excess FROM ...

## 5. RAG Tool

### 로직
1. Intent → 인덱스 매핑: ETF→rag-etf, Bond→rag-bond, Fund→rag-fund
2. 사용자 질문 → Bedrock Titan Embed v2 → 1024-dim 벡터
3. OpenSearch kNN 검색 (top_k=5)
4. 결과 청크 + 메타데이터 반환
5. ToolResult에 검색 쿼리, similarity score, 결과 텍스트 포함

## 6. GraphRAG Tool

### 로직
1. Intent → 테넌트 매핑: ETF→etf, Bond→bond, Fund→fund
2. graphrag-toolkit LexicalGraphQueryEngine 초기화 (tenant)
3. 질의 실행 → 중간 단계(함수명, 중간결과) 수집
4. 결과: 텍스트 응답 + graph_data (있으면)
5. ToolResult에 실행 단계별 정보 포함

## 7. OpenCypher Tool

### 로직
1. Intent → 테넌트 매핑
2. Neptune 그래프 스키마 정보 + 질문 → LLM → Cypher 생성
   ```
   MATCH (n)-[r]->(m)
   WHERE n.__tenant__ = '{tenant}'
   RETURN n, r, m LIMIT 50
   ```
3. Cypher 검증 (읽기 전용, MATCH/RETURN만 허용)
4. Neptune 실행 → 노드/엣지 결과
5. graph_data 변환 (GraphNode, GraphEdge 목록)

## 8. Agent Event Streaming

### WebSocket 이벤트 흐름
```
Client <-- WebSocket --> Server

Client sends: { "type": "message", "session_id": "...", "message": "..." }

Server streams:
  → { "type": "intent_detected", "data": {...}, "timestamp": "..." }
  → { "type": "tool_selected", "data": {...}, "timestamp": "..." }
  → { "type": "query_generated", "data": {...}, "timestamp": "..." }
  → { "type": "query_executed", "data": {...}, "timestamp": "..." }
  → { "type": "text_chunk", "data": {"text": "AUM 상위"}, "timestamp": "..." }
  → { "type": "text_chunk", "data": {"text": " 10개 ETF는"}, "timestamp": "..." }
  → ...
  → { "type": "response_complete", "data": {...}, "timestamp": "..." }
```

## 9. Conversation Service (DynamoDB)

### 세션 관리 (1테이블)
- **create_session()**: 첫 턴 저장 시 session_id 자동 생성
- **get_session(session_id)**: Query(PK=session_id) → 전체 턴 목록
- **list_sessions()**: Scan → session_id별 그룹핑, 마지막 턴의 timestamp 기준 정렬
- **delete_session(session_id)**: Query(PK=session_id) → BatchDelete 전체 턴

### 턴 저장 (답변 완료 후)
- **save_turn(session_id, turn_json)**: DynamoDB PUT conversation_turns
- turn_json에 session_title, context_summary 포함 (매 턴마다 최신값)
- 첫 턴: session_title을 질문에서 자동 생성

### 컨텍스트 구성 (멀티턴)
- **get_context(session_id)**:
  1. DynamoDB Query(PK=session_id, ScanIndexForward=False, Limit=3) → 최근 3턴
  2. 마지막 턴의 context_summary 조회
  3. 반환: { summary: "...", recent_turns: [...] }

### 요약 갱신
- **update_summary(session_id, new_turn)**:
  1. 이전 턴의 context_summary + 새 턴 메시지 → LLM → 업데이트된 요약
  2. 새 턴 JSON에 context_summary 포함하여 저장
  3. 3턴마다 또는 요약 길이 초과 시 갱신

## 10. Token Tracker (JSON Embedded)

### 비용 계산 로직
```python
PRICING = {
    "claude-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
    "titan-embed-v2": {"input": 0.02 / 1_000_000, "output": 0},
}

def calculate_cost(model, tokens_in, tokens_out):
    p = PRICING[model]
    return tokens_in * p["input"] + tokens_out * p["output"]
```

### 통계 집계 (Admin)
- DynamoDB Scan conversation_turns → 기간별 집계
- 일별/주별/월별 tokens_in, tokens_out, cost, request_count 합산
- GSI (Global Secondary Index) on timestamp for efficient range queries

## 11. FastAPI Endpoints

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | /api/chat | chat_sync | 동기 대화 (비스트리밍) |
| WS | /ws/chat | chat_stream | 스트리밍 대화 |
| GET | /api/conversations | list_conversations | 대화 목록 |
| GET | /api/conversations/{id} | get_conversation | 대화 상세 |
| DELETE | /api/conversations/{id} | delete_conversation | 대화 삭제 |
| GET | /api/visualize/graph | get_graph | 그래프 데이터 |
| GET | /api/visualize/chart | get_chart | 차트 데이터 |
| GET | /api/admin/token-usage | get_token_usage | 토큰 통계 |
| GET | /api/admin/conversations | admin_conversations | Admin 대화 관리 |
| GET | /api/examples | get_examples | 예시 쿼리 |

## 12. Visualization Service

### Graph → Cytoscape.js
- Neptune OpenCypher 결과 → GraphData (nodes + edges)
- node: { id, label, type, properties }
- edge: { source, target, label, properties }

### SQL Result → Chart
- 쿼리 결과가 2+ 컬럼이면 자동 차트 생성 시도
- 숫자 컬럼 → y_axis, 문자 컬럼 → x_axis
- chart_type 자동 결정:
  - 카테고리 비교 → bar
  - 시계열 → line
  - 비율 → pie
