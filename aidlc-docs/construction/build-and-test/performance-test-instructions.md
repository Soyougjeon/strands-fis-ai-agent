# Performance Test Instructions

## 개요
PoC 단계의 성능 기준선 측정. 5명 내부 테스터 동시 사용 시나리오.

---

## PT-01: API 응답 시간

### 측정 도구
```bash
# Apache Bench 또는 curl 사용
sudo yum install -y httpd-tools  # ab 설치
```

### 테스트

#### PT-01-01: Health Check
```bash
ab -n 100 -c 10 http://localhost:8000/api/health
# 기준: p95 < 50ms
```

#### PT-01-02: 대화 목록
```bash
ab -n 50 -c 5 http://localhost:8000/api/conversations
# 기준: p95 < 500ms (DynamoDB Scan)
```

#### PT-01-03: 예시 쿼리
```bash
ab -n 50 -c 5 http://localhost:8000/api/examples
# 기준: p95 < 100ms (파일 캐싱)
```

---

## PT-02: Agent End-to-End 응답 시간

### 측정 방법
```bash
# curl로 전체 응답 시간 측정
time curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "AUM 상위 5개 ETF"}' > /dev/null
```

### 성능 기준 (PoC)

| 단계 | 기대 시간 | 비고 |
|------|----------|------|
| Intent Detection | < 2s | Bedrock LLM 호출 |
| Tool Selection | < 2s | Bedrock LLM 호출 |
| SQL Generation | < 2s | Bedrock LLM 호출 (Text2SQL) |
| SQL Execution | < 1s | Aurora PG (10초 타임아웃) |
| Response Generation | < 5s | Bedrock 스트리밍 |
| **Total E2E** | **< 12s** | 전체 파이프라인 |

### RAG/GraphRAG/OpenCypher 추가 측정
```bash
# RAG
time curl -s -X POST http://localhost:8000/api/chat \
  -d '{"message": "TIGER S&P500 투자 전략 설명해줘"}' > /dev/null
# 기준: Total < 15s (임베딩 + kNN + LLM)

# OpenCypher
time curl -s -X POST http://localhost:8000/api/chat \
  -d '{"message": "TIGER 반도체 ETF 2홉 연결 노드"}' > /dev/null
# 기준: Total < 15s (LLM Cypher 생성 + Neptune)
```

---

## PT-03: 동시 사용자

### 5명 동시 요청
```bash
# 5개 동시 요청 (서로 다른 질문)
for i in 1 2 3 4 5; do
  curl -s -X POST http://localhost:8000/api/chat \
    -d "{\"message\": \"ETF 질문 $i\"}" > /dev/null &
done
wait
echo "All done"

# 검증: 모든 요청 성공, 개별 응답 시간 < 15s
```

---

## PT-04: Token 비용 추정

### 단일 대화 예상 비용

| 단계 | 입력 토큰 | 출력 토큰 | 비용 |
|------|----------|----------|------|
| Intent Detection | ~200 | ~20 | $0.0009 |
| Tool Selection | ~300 | ~30 | $0.0014 |
| SQL Generation | ~500 | ~100 | $0.0030 |
| Response Generation | ~800 | ~300 | $0.0069 |
| **Total** | **~1,800** | **~450** | **~$0.012** |

### 일일 예상 (5명 x 20회 = 100 대화/일)
- 토큰: ~180K input + ~45K output
- 비용: ~$1.20/일
- 월간: ~$36/월

---

## 결과 기록 템플릿

| 테스트 | 결과 | 비고 |
|--------|------|------|
| PT-01-01 Health p95 | _ms | < 50ms |
| PT-01-02 Conversations p95 | _ms | < 500ms |
| PT-02 Text2SQL E2E | _s | < 12s |
| PT-02 RAG E2E | _s | < 15s |
| PT-02 OpenCypher E2E | _s | < 15s |
| PT-03 5명 동시 | Pass/Fail | 모두 < 15s |
| PT-04 단일 대화 비용 | $_ | ~$0.012 |
