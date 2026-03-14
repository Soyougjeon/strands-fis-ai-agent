# Code Quality Assessment

## Test Coverage
- **Overall**: Poor (2 test files only)
- **Unit Tests**: `tests/test_config.py` (config 설정), `tests/test_evaluator.py` (평가기)
- **Integration Tests**: None (별도 통합 테스트 없음)
- **Coverage Notes**: 스크래퍼, GraphRAG 인덱서/로더/쿼리, 모델, DB 레이어에 대한 테스트 부재

## Code Quality Indicators
- **Linting**: Not configured (pyproject.toml에 linting 도구 없음)
- **Code Style**: Consistent - Python 표준 스타일 준수, 모듈별 명확한 책임 분리
- **Documentation**: Fair - README.md가 포괄적이나, 코드 내 docstring은 제한적
- **Type Hints**: Partial - 일부 함수에만 적용

## Strengths (Good Patterns)

### 1. 명확한 모듈 분리
- scrapers, parsers, graphrag, utils로 관심사 분리가 잘 되어 있음
- 각 스크래퍼가 단일 데이터 소스에 집중

### 2. BaseScraper 추상화
- 공통 로직(HTTP, 쓰로틀링, 재시도, 실행 추적)을 Base 클래스로 추출
- Template Method 패턴으로 확장성 확보

### 3. Idempotent UPSERT
- 모든 스크래퍼가 ON CONFLICT DO UPDATE 사용
- 중복 실행에 안전한 데이터 적재

### 4. Writer/Reader Separation
- Aurora PostgreSQL의 Writer/Reader 엔드포인트 분리
- 읽기 부하 분산 가능한 구조

### 5. Multi-Source Configuration
- Pydantic Settings로 env > .env > config.yaml 우선순위
- 환경별 유연한 설정 관리

### 6. Domain-Specific Ontology
- ETF 도메인에 특화된 17 Entity + 17 Relationship 타입 정의
- LLM 추출 품질 향상을 위한 커스텀 프롬프트

### 7. Comprehensive Evaluation Framework
- 7개 카테고리의 평가 질문 세트
- Keyword hit + LLM-as-Judge 이중 평가
- 실험 설정 기반 모델 비교

## Technical Debt

### 1. 테스트 부족
- 스크래퍼, 파서, GraphRAG 핵심 로직에 대한 테스트 없음
- 리팩토링이나 변경 시 회귀 테스트 불가

### 2. CLI 전용 인터페이스
- Web API 없이 CLI만 제공
- 외부 서비스 통합이나 챗봇 연동 불가

### 3. 동기식 스크래핑
- httpx를 동기 모드로 사용 (AsyncClient 미사용)
- 대량 데이터 수집 시 성능 제한

### 4. 하드코딩된 로컬 파일 경로
- PDF/Excel 다운로드 경로가 data/ 디렉토리에 의존
- 클라우드 스토리지(S3) 미지원

### 5. Error Handling 제한
- 스크래퍼별 에러 처리는 있으나, 전역 에러 핸들러 없음
- 실패 시 부분 재실행 메커니즘 제한적

## Anti-patterns

### 1. 로컬 Docker 자격증명 하드코딩
- `docker-compose.yml`에 default password (`mirae123`) 포함
- 개발 환경 전용이지만, 실수로 프로덕션에 사용 가능성

### 2. SQL Schema 이중 관리
- `models.py` (ORM) + `sql/schema.sql` (DDL) 이중 정의
- Alembic 마이그레이션이 있으나 schema.sql과의 동기화 불확실
