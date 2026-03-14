# Unit Test Instructions

## Prerequisites
```bash
source .venv/bin/activate
pip install pytest pytest-asyncio httpx
```

---

## Unit 1: Pipeline Tests

### 실행 방법
```bash
python -m pytest pipeline/tests/ -v
```

### 테스트 범위
| 파일 | 테스트 항목 |
|------|-----------|
| `test_generators.py` | ETF/Bond/Fund CSV 생성 검증 (행수, 컬럼, 데이터 타입, 값 범위) |
| `test_loaders.py` | DB Loader mock 테스트, GraphRAG/RAG indexer mock 테스트 |

### 예상 결과
- Phase 1-3 (CSV/MD/Query 생성): AWS 없이 로컬 실행 가능
- Phase 4-6 (DB/인덱싱): Mock AWS 클라이언트로 테스트

---

## Unit 2: Backend Tests

### 실행 방법
```bash
python -m pytest backend/tests/ -v
```

### 테스트 파일별 상세

#### `test_agent.py`
| 테스트 | 검증 내용 |
|--------|----------|
| `TestEvents::test_intent_detected_event` | intent_detected 이벤트 JSON 구조 |
| `TestEvents::test_tool_selected_event` | tool_selected 이벤트 JSON 구조 |
| `TestEvents::test_query_generated_event` | query_generated 이벤트 JSON 구조 |
| `TestEvents::test_query_executed_event` | query_executed 이벤트 (raw_data 포함) |
| `TestEvents::test_text_chunk_event` | text_chunk 한글 텍스트 |
| `TestEvents::test_response_complete_event` | 총합 메트릭 |
| `TestPrompts::test_schema_map_has_all_intents` | ETF/Bond/Fund 스키마 존재 |
| `TestPrompts::test_few_shot_map_has_all_intents` | Few-shot 예시 존재 |
| `TestPrompts::test_graph_schema_has_all_intents` | Neptune 그래프 스키마 존재 |
| `TestPrompts::test_schema_map_contains_table_names` | 테이블명 정확성 |
| `TestTokenTracker::test_calculate_cost_claude_sonnet` | Claude 비용 계산 정확성 |
| `TestTokenTracker::test_calculate_cost_titan_embed` | Titan 비용 계산 |
| `TestTokenTracker::test_calculate_cost_unknown_model` | 미등록 모델 = 0 |

#### `test_services.py`
| 테스트 | 검증 내용 |
|--------|----------|
| `TestTokenAggregation::test_daily_aggregation` | 일별 버킷 집계 정확성 |
| `TestTokenAggregation::test_monthly_aggregation` | 월별 버킷 |
| `TestTokenAggregation::test_empty_turns` | 빈 데이터 |
| `TestVisualization::test_bar_chart_detection` | 문자+숫자 → bar |
| `TestVisualization::test_pie_chart_detection` | 비율 합 100 → pie |
| `TestVisualization::test_no_chart_*` | 차트 불가 케이스 |
| `TestConversationService::test_generate_session_id` | UUID 형식 |
| `TestConversationService::test_generate_turn_id` | turn# 형식 |

#### `test_api.py`
| 테스트 | 검증 내용 |
|--------|----------|
| `TestHealthEndpoint::test_health` | GET /api/health → 200 |
| `TestExamplesEndpoint::test_get_examples` | GET /api/examples → 200 |
| `TestConversationsEndpoint::test_list_conversations` | GET /api/conversations → [] |
| `TestConversationsEndpoint::test_get_conversation_not_found` | 404 |
| `TestConversationsEndpoint::test_delete_conversation_not_found` | 404 |
| `TestAdminEndpoint::test_token_usage` | period=daily 집계 |
| `TestAdminEndpoint::test_admin_conversations` | Admin 목록 |
| `TestText2SQLTool::test_sql_validation` | SELECT 허용, DROP/DELETE 차단 |
| `TestText2SQLTool::test_sql_extract` | ```sql 블록 추출 |
| `TestText2SQLTool::test_ensure_limit` | LIMIT 자동 추가 |
| `TestOpenCypherTool::test_cypher_validation` | tenant 필터 + 읽기 전용 |
| `TestOpenCypherTool::test_cypher_extract` | ```cypher 블록 추출 |

### 예상 결과
```
backend/tests/test_agent.py .......... PASSED
backend/tests/test_services.py ........ PASSED
backend/tests/test_api.py ............. PASSED
```

모든 테스트는 AWS 연결 없이 mock으로 실행 가능합니다.

---

## 전체 실행
```bash
# Pipeline + Backend 전체
python -m pytest pipeline/tests/ backend/tests/ -v --tb=short
```
