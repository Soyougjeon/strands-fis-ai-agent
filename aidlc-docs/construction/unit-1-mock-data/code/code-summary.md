# Code Summary - Unit 1: Mock Data Pipeline

## Generated Files

| # | File | Purpose |
|---|------|---------|
| 1 | `pipeline/config.py` | AWS 연결 설정 (Aurora PG, Neptune, OpenSearch, Bedrock) |
| 2 | `pipeline/models/base.py` | SQLAlchemy Base, 엔진/세션 팩토리 |
| 3 | `pipeline/models/etf.py` | ETF ORM (tiger_etf 스키마, 4 모델) |
| 4 | `pipeline/models/bond.py` | Bond ORM (bond 스키마, 2 모델) |
| 5 | `pipeline/models/fund.py` | Fund ORM (fund 스키마, 3 모델) |
| 6 | `pipeline/models/schema_ddl.py` | 스키마/테이블 DDL 생성 및 TRUNCATE |
| 7 | `pipeline/generators/etf_generator.py` | ETF Mock CSV 생성 (30건, 4 CSV) |
| 8 | `pipeline/generators/bond_generator.py` | Bond Mock CSV 생성 (30건, 2 CSV) |
| 9 | `pipeline/generators/fund_generator.py` | Fund Mock CSV 생성 (30건, 3 CSV) |
| 10 | `pipeline/generators/md_generator.py` | MD 파일 생성 (90 상품 + 3 개요) |
| 11 | `pipeline/generators/example_queries.py` | 예시 질문 JSON (3 도메인 x 4 방식) |
| 12 | `pipeline/loaders/db_loader.py` | CSV -> Aurora PG 적재 |
| 13 | `pipeline/loaders/graphrag_indexer.py` | MD -> Neptune GraphRAG 인덱싱 |
| 14 | `pipeline/loaders/rag_indexer.py` | MD -> OpenSearch RAG 벡터 인덱싱 |
| 15 | `pipeline/main.py` | CLI 진입점 (Click) |
| 16 | `pipeline/tests/test_generators.py` | Generator 단위 테스트 |
| 17 | `pipeline/tests/test_loaders.py` | Loader 단위 테스트 |

## Requirements Coverage

| Requirement | Covered By |
|-------------|-----------|
| FR-04-01 (ETF CSV) | etf_generator.py |
| FR-04-02 (Bond CSV) | bond_generator.py |
| FR-04-03 (Fund CSV) | fund_generator.py |
| FR-04-04 (DB 적재) | db_loader.py |
| FR-04-05 (GraphRAG 인덱싱) | graphrag_indexer.py |
| FR-04-06 (RAG 인덱싱) | rag_indexer.py |
| FR-04-07 (Neptune 멀티테넌시) | graphrag_indexer.py (tenant_id 파라미터) |
| 추가 (예시 질문) | example_queries.py |

## CLI Usage
```bash
python -m pipeline.main run-all          # 전체 파이프라인
python -m pipeline.main generate-csv     # CSV 생성만
python -m pipeline.main generate-md      # MD 생성만
python -m pipeline.main generate-queries # 예시 질문 생성만
python -m pipeline.main load-db          # DB 적재만
python -m pipeline.main index-graphrag   # GraphRAG 인덱싱만
python -m pipeline.main index-rag        # RAG 인덱싱만
```
