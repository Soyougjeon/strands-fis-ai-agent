# Code Generation Plan - Unit 1: Mock Data Pipeline

## Unit Context
- **Unit**: Unit 1 - Mock Data Pipeline
- **Code Location**: `pipeline/` (workspace root)
- **Requirements**: FR-04-01~07
- **Dependencies**: AWS Services (Aurora PG, Neptune, OpenSearch, Bedrock)
- **Depended By**: Unit 2 (Agent Backend - 데이터 존재 전제)

## Generation Steps

### Project Structure Setup
- [x] Step 1: `pipeline/` 디렉토리 구조 생성 및 `requirements.txt`
- [x] Step 2: `pipeline/config.py` - AWS 연결 설정 (Aurora PG, Neptune, OpenSearch, Bedrock)

### Domain Models & DB Schema
- [x] Step 3: `pipeline/models/base.py` - SQLAlchemy Base, 공통 설정
- [x] Step 4: `pipeline/models/etf.py` - ETF ORM 모델 (기존 tiger_etf 스키마 참조)
- [x] Step 5: `pipeline/models/bond.py` - Bond ORM 모델 (신규 bond 스키마)
- [x] Step 6: `pipeline/models/fund.py` - Fund ORM 모델 (신규 fund 스키마)
- [x] Step 7: `pipeline/models/schema_ddl.py` - 스키마/테이블 DDL 생성 헬퍼

### CSV Generators (Phase 1)
- [x] Step 8: `pipeline/generators/etf_generator.py` - ETF Mock CSV 생성 (30건, 4 CSV)
- [x] Step 9: `pipeline/generators/bond_generator.py` - Bond Mock CSV 생성 (30건, 2 CSV)
- [x] Step 10: `pipeline/generators/fund_generator.py` - Fund Mock CSV 생성 (30건, 3 CSV)

### MD Generators (Phase 2)
- [x] Step 11: `pipeline/generators/md_generator.py` - MD 파일 생성 (90 상품 + 3 개요)

### Example Query Generator (Phase 3)
- [x] Step 12: `pipeline/generators/example_queries.py` - 예시 질문 JSON 생성 (3 도메인 x 4 방식)

### Data Loaders (Phase 4)
- [x] Step 13: `pipeline/loaders/db_loader.py` - CSV -> Aurora PG 적재 (스키마 생성 + TRUNCATE + INSERT)

### Indexers (Phase 5-6)
- [x] Step 14: `pipeline/loaders/graphrag_indexer.py` - MD -> Neptune GraphRAG 인덱싱 (멀티테넌시)
- [x] Step 15: `pipeline/loaders/rag_indexer.py` - MD -> OpenSearch RAG 벡터 인덱싱

### CLI Entry Point
- [x] Step 16: `pipeline/main.py` - CLI 진입점 (run_all, 개별 Phase 실행)

### Tests
- [x] Step 17: `pipeline/tests/test_generators.py` - Generator 단위 테스트
- [x] Step 18: `pipeline/tests/test_loaders.py` - Loader 단위 테스트 (mock AWS)

### Documentation
- [x] Step 19: `aidlc-docs/construction/unit-1-mock-data/code/code-summary.md` - 코드 요약

## Story Traceability

| Step | Requirements |
|------|-------------|
| Step 3-7 | FR-04-01, FR-04-02, FR-04-03 (스키마 정의) |
| Step 8 | FR-04-01 (ETF Mock CSV) |
| Step 9 | FR-04-02 (Bond Mock CSV) |
| Step 10 | FR-04-03 (Fund Mock CSV) |
| Step 11 | FR-04-05, FR-04-06 (MD 파일 - GraphRAG/RAG용) |
| Step 12 | 추가 요구사항 (예시 질문 생성) |
| Step 13 | FR-04-04 (CSV -> Aurora PG) |
| Step 14 | FR-04-05, FR-04-07 (GraphRAG 인덱싱, Neptune 멀티테넌시) |
| Step 15 | FR-04-06 (RAG 인덱싱 - OpenSearch 벡터) |
