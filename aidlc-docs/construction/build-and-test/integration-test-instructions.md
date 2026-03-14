# Integration Test Instructions

## 개요
Unit 간 통합 테스트. 실제 AWS 서비스 연결이 필요합니다.

---

## IT-01: Pipeline → Backend 연동

### 목적
Pipeline에서 생성한 데이터를 Backend가 정상 조회하는지 검증

### 사전 조건
- Pipeline Phase 1-6 완료 (데이터 적재됨)
- Backend 서버 실행 중

### 테스트 절차

#### IT-01-01: Text2SQL 연동
```bash
# ETF 쿼리 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "AUM 상위 5개 ETF 목록 보여줘"}'

# 검증: response에 ETF 이름과 AUM 수치 포함
# 검증: agent_process.query_generation.query에 유효한 SQL 포함
# 검증: agent_process.query_execution.raw_data에 5건 이내 결과
```

#### IT-01-02: Bond Text2SQL
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "AAA 등급 채권 목록"}'

# 검증: bond.bond_products 테이블 조회 확인
```

#### IT-01-03: Fund Text2SQL
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "주식형 펀드 수익률 상위 10개"}'

# 검증: fund.fund_products JOIN fund.fund_performance 확인
```

#### IT-01-04: RAG 연동
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "TIGER S&P500 ETF의 투자 전략은?"}'

# 검증: tool = rag 선택
# 검증: OpenSearch kNN 검색 결과 (chunks) 포함
```

#### IT-01-05: OpenCypher 연동
```bash
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "TIGER 반도체 ETF의 2홉 연결 엔티티 그래프 보여줘"}'

# 검증: tool = opencypher 선택
# 검증: graph_data에 nodes + edges 포함
```

---

## IT-02: Backend → DynamoDB 연동

### IT-02-01: 대화 저장 → 조회
```bash
# 1. 대화 실행 (session_id 없음 → 새 세션)
RESPONSE=$(curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "AUM 상위 ETF는?"}')

SESSION_ID=$(echo $RESPONSE | python -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

# 2. 대화 목록 확인
curl http://localhost:8000/api/conversations
# 검증: session_id가 목록에 존재

# 3. 대화 상세 조회
curl http://localhost:8000/api/conversations/$SESSION_ID
# 검증: turns 배열에 1건, question/response/agent_process/total 포함

# 4. 멀티턴 테스트
curl -X POST http://localhost:8000/api/chat \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"그 중 수익률 1위는?\"}"
# 검증: 이전 대화 컨텍스트 참조한 응답

# 5. 삭제
curl -X DELETE http://localhost:8000/api/conversations/$SESSION_ID
# 검증: {"deleted": 2}
```

### IT-02-02: 토큰 통계
```bash
curl "http://localhost:8000/api/admin/token-usage?period=daily"
# 검증: data 배열에 오늘 날짜 버킷 존재
# 검증: totals.request_count >= 1
```

---

## IT-03: Backend → Frontend WebSocket 연동

### 목적
WebSocket 스트리밍이 정상 작동하는지 검증

### 테스트 절차
```bash
# websocat 설치 (brew install websocat)
# 또는 wscat (npm install -g wscat)

wscat -c ws://localhost:8000/ws/chat

# 연결 후 메시지 전송:
> {"message": "AUM 상위 3개 ETF"}

# 예상 수신 이벤트 순서:
# 1. {"type": "intent_detected", "data": {"intent": "ETF", ...}}
# 2. {"type": "tool_selected", "data": {"tool": "text2sql", ...}}
# 3. {"type": "query_generated", "data": {"query_type": "sql", ...}}
# 4. {"type": "query_executed", "data": {"result_summary": "...", ...}}
# 5. {"type": "text_chunk", "data": {"text": "..."}} (N개)
# 6. {"type": "response_complete", "data": {"total_latency": ...}}
# 7. {"type": "session_info", "data": {"session_id": "..."}}
```

---

## IT-04: Frontend → Backend 전체 연동

### 사전 조건
- Backend 실행 중 (:8000)
- Frontend 실행 중 (:5173)

### 테스트 항목

| ID | 시나리오 | 검증 |
|----|---------|------|
| IT-04-01 | Chat 탭에서 질문 입력 + 전송 | 스트리밍 응답 + Agent Process 패널 업데이트 |
| IT-04-02 | Agent Process 패널 확인 | 5단계 순서대로 표시, 메트릭 수치 |
| IT-04-03 | Detail Tabs 확인 | 선택된 Tool의 탭 자동 활성화, SQL/결과 표시 |
| IT-04-04 | 차트 렌더링 | 숫자+문자 결과 → bar chart 자동 표시 |
| IT-04-05 | 사이드바 대화 이력 | 대화 후 목록 갱신, 클릭 시 로드 |
| IT-04-06 | 예시 쿼리 클릭 | 자동 전송 + 응답 |
| IT-04-07 | 새 대화 버튼 | 메시지 초기화, 새 session_id |
| IT-04-08 | Admin 탭 | 토큰 통계 차트 + 대화 관리 테이블 |
| IT-04-09 | Admin 대화 삭제 | 확인 다이얼로그 → 목록 갱신 |
| IT-04-10 | WebSocket 재연결 | 서버 재시작 후 3초 내 자동 재연결 |

---

## 체크리스트

- [ ] IT-01: Pipeline 데이터로 Text2SQL 쿼리 성공 (ETF/Bond/Fund)
- [ ] IT-01: RAG 벡터 검색 결과 반환
- [ ] IT-01: OpenCypher 그래프 쿼리 결과 반환
- [ ] IT-02: DynamoDB 턴 저장 + 조회 + 삭제
- [ ] IT-02: 멀티턴 대화 컨텍스트 유지
- [ ] IT-02: 토큰 통계 집계
- [ ] IT-03: WebSocket 6종 이벤트 순서 정확
- [ ] IT-04: 전체 UI 시나리오 10개 통과
