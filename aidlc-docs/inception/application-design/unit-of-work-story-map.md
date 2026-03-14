# Unit of Work - Requirements Map

User Stories 단계를 건너뛰었으므로, 요구사항(FR/NFR)을 유닛에 직접 매핑한다.

## Requirements to Unit Mapping

### Unit 1: Mock Data Pipeline

| Requirement | Description |
|-------------|-------------|
| FR-04-01 | ETF Mock 데이터 생성 (CSV) |
| FR-04-02 | 채권 Mock 데이터 생성 (CSV) |
| FR-04-03 | 펀드 Mock 데이터 생성 (CSV) |
| FR-04-04 | Mock MD 파일 생성 (GraphRAG/RAG용) |
| FR-04-05 | CSV -> Aurora PostgreSQL 적재 |
| FR-04-06 | GraphRAG 인덱싱 (Neptune 멀티테넌시) |
| FR-04-07 | RAG 인덱싱 (OpenSearch 벡터) |

### Unit 2: Agent Backend

| Requirement | Description |
|-------------|-------------|
| FR-01-01 | Intent 분류 (ETF/Bond/Fund) - Orchestrator Agent |
| FR-01-02 | Text2SQL 데이터 접근 (Aurora PG) |
| FR-01-03 | RAG 데이터 접근 (OpenSearch kNN) |
| FR-01-04 | GraphRAG 데이터 접근 (Neptune + OpenSearch) |
| FR-01-05 | OpenCypher 데이터 접근 (Neptune 직접) |
| FR-01-06 | 스트리밍 응답 생성 (WebSocket) |
| FR-01-07 | Agent 실행 과정 투명성 (단계별 시간/토큰/비용) |
| FR-03-01 | POST /api/chat (동기 대화) |
| FR-03-02 | WebSocket /ws/chat (스트리밍 대화) |
| FR-03-03 | GET /api/conversations (목록) |
| FR-03-04 | GET /api/conversations/{id} (상세) |
| FR-03-05 | DELETE /api/conversations/{id} (삭제) |
| FR-03-06 | GET /api/visualize/graph (그래프 시각화) |
| FR-03-07 | GET /api/visualize/chart (차트 데이터) |
| FR-03-08 | GET /api/admin/token-usage (토큰 통계) |
| FR-03-09 | GET /api/admin/conversations (Admin 대화 관리) |
| FR-03-10 | GET /api/examples (예시 쿼리) |
| FR-05-01 | 토큰 사용량 기록 (단계별) |
| FR-05-02 | 비용 계산 (모델별 단가) |
| FR-05-03 | 통계 집계 (일별/누적/모델별) |
| FR-06-01 | 대화 세션 CRUD |
| FR-06-02 | 메시지 저장 (메타데이터 포함) |
| FR-06-03 | 대화 검색 |
| NFR-01 | 응답 시간 < 30초 |
| NFR-05 | 한국어 응답 |

### Unit 3: Frontend

| Requirement | Description |
|-------------|-------------|
| FR-02-01 | 상단 멀티탭 (Chat / Graph Network / Admin) |
| FR-02-02 | 코글 사이드바 (대화 이력 + 예시 쿼리) |
| FR-02-03 | Chat 탭 2분할 (Chat Area + Agent Process) |
| FR-02-04 | Agent Process Panel (단계별 시간/토큰/비용) |
| FR-02-05 | 상세 탭 (OpenCypher/OpenSearch/GraphRAG/SQL/결과) |
| FR-02-06 | 동적 차트 (ECharts/Plotly.js) |
| FR-02-07 | 그래프 네트워크 (Cytoscape.js) |
| FR-02-08 | Graph Network 탭 (테넌트별 서브탭: ETF/채권/펀드) |
| FR-02-09 | Admin 대시보드 (토큰 사용량/비용, 대화 이력) |
| FR-02-10 | 마크다운 렌더링 + 코드 하이라이팅 |
| FR-02-11 | 스트리밍 응답 실시간 렌더링 |
| NFR-02 | EC2 + Nginx 배포 |
| NFR-03 | Nginx Basic Auth (5명 테스터) |

## Coverage Check

| Category | Total | Unit 1 | Unit 2 | Unit 3 | Covered |
|----------|-------|--------|--------|--------|---------|
| FR-01 (Agent) | 7 | 0 | 7 | 0 | 100% |
| FR-02 (UI) | 11 | 0 | 0 | 11 | 100% |
| FR-03 (API) | 10 | 0 | 10 | 0 | 100% |
| FR-04 (Data) | 7 | 7 | 0 | 0 | 100% |
| FR-05 (Token) | 3 | 0 | 3 | 0 | 100% |
| FR-06 (Conv) | 3 | 0 | 3 | 0 | 100% |
| NFR | 5 | 0 | 2 | 2 | 100% |

All requirements are mapped to at least one unit. No orphaned requirements.
