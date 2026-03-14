# Component Inventory

## Application Packages

| Package | Purpose |
|---------|---------|
| `src/tiger_etf` | 메인 애플리케이션 패키지 (CLI 진입점, 설정, DB) |
| `src/tiger_etf/scrapers` | 6개 웹 스크래퍼 (ETF 데이터 수집) |
| `src/tiger_etf/parsers` | HTML/Excel 파서 (데이터 변환) |
| `src/tiger_etf/graphrag` | GraphRAG 인덱싱, 질의, 실험, 평가 |
| `src/tiger_etf/utils` | 로깅 설정 유틸리티 |

## Infrastructure Packages

| Package | Type | Purpose |
|---------|------|---------|
| `docker/graphrag` | Docker Compose | 로컬 개발용 PostgreSQL 16 |
| `alembic` | Database Migration | Aurora PostgreSQL 스키마 마이그레이션 |
| `certs` | SSL Certificates | RDS SSL 인증서 (global-bundle.pem) |

## Shared Packages

| Package | Type | Purpose |
|---------|------|---------|
| `src/tiger_etf/models.py` | ORM Models | 8개 테이블 SQLAlchemy 모델 |
| `src/tiger_etf/config.py` | Configuration | Pydantic Settings (다중 소스 설정) |
| `src/tiger_etf/db.py` | Database Client | SQLAlchemy 엔진/세션 팩토리 |

## Test Packages

| Package | Type | Purpose |
|---------|------|---------|
| `tests` | Unit Tests | config, evaluator 테스트 |
| `experiments` | Evaluation | GraphRAG 실험 설정 + 평가 질문 세트 |

## Documentation Packages

| Package | Purpose |
|---------|---------|
| `docs/guide` | GraphRAG 개요, 구현 예제, 쿼리 라우팅 가이드 |
| `docs/lexical-graph` | AWS GraphRAG Toolkit(LexicalGraph) 상세 문서 |
| `experiments/*.md` | 실험 방법론, Entity Resolution 가이드, 작업 분류 |

## Total Count
- **Total Packages**: 12
- **Application**: 5 (tiger_etf, scrapers, parsers, graphrag, utils)
- **Infrastructure**: 3 (docker, alembic, certs)
- **Shared**: 3 (models, config, db)
- **Test**: 2 (tests, experiments)
