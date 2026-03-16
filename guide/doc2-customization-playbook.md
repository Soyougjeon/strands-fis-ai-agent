# Doc 2: Customization Playbook

## 개요

Strands FIS를 자신의 도메인으로 전환하기 위한 10단계 체크리스트.
각 단계에서 수정할 파일과 구체적인 변경 내용을 명시한다.

---

## Step 1: 도메인 정의

자신의 도메인에서 Intent(분류 카테고리)를 결정한다.

참조 구현: ETF, Bond, Fund (3개)

예시:
- 보험: Insurance, Claim, Policy
- 은행: Deposit, Loan, Card
- 증권: Stock, Derivative, REIT

**결정 사항:**
- [ ] Intent 목록 (2~5개 권장)
- [ ] 각 Intent의 설명 키워드
- [ ] 각 Intent에 대응하는 DB 스키마명

---

## Step 2: DB 스키마 설계

각 도메인의 Aurora PostgreSQL 테이블을 설계한다.

**수정 파일:**
- `pipeline/models/{domain}.py` — SQLAlchemy ORM 모델 작성
- `pipeline/models/schema_ddl.py` — SCHEMAS 리스트에 스키마명 추가

**규칙:**
- 도메인별 별도 스키마 (`{domain}.{table}`)
- 상품 마스터 테이블에 PK 필수
- 영문 컬럼명 사용
- FK 관계 명시

**체크리스트:**
- [ ] ORM 모델 파일 작성 (도메인당 1개)
- [ ] schema_ddl.py의 SCHEMAS 리스트 업데이트
- [ ] `pipeline/models/base.py`에서 import 확인

---

## Step 3: Mock 데이터 생성기

CSV와 MD 파일 생성기를 작성한다.

**수정 파일:**
- `pipeline/generators/{domain}_generator.py` — CSV 생성기 (도메인당 1개)
- `pipeline/generators/md_generator.py` — MD 생성기 (도메인 추가)

**CSV 생성기 패턴:**
```python
def generate_{domain}_csv(output_dir: str, count: int = 50):
    # 1. 랜덤 데이터 생성 (faker 또는 직접)
    # 2. pandas DataFrame 생성
    # 3. CSV 저장 (output_dir/{domain}/ 하위)
```

**MD 생성기 패턴:**
- 상품별 1개 MD 파일
- 엔티티 이름과 관계를 자연어로 서술
- GraphRAG가 LLM으로 엔티티/관계 자동 추출

**체크리스트:**
- [ ] CSV 생성기 작성
- [ ] MD 생성기에 도메인 추가
- [ ] `pipeline/main.py`에 CLI 명령 등록

---

## Step 4: 데이터 적재기

CSV→Aurora, MD→Neptune/OpenSearch 적재기를 설정한다.

**수정 파일:**
- `pipeline/loaders/db_loader.py` — 도메인 테이블 매핑 추가
- `pipeline/loaders/graphrag_indexer.py` — tenant명 추가
- `pipeline/loaders/rag_indexer.py` — 인덱스명 추가

**체크리스트:**
- [ ] db_loader에 도메인 테이블 매핑
- [ ] graphrag_indexer에 tenant명 (소문자)
- [ ] rag_indexer에 인덱스명 (`rag-{domain}`)

---

## Step 5: Agent 프롬프트 수정

Intent 분류와 Tool 선택 프롬프트를 도메인에 맞게 수정한다.

**수정 파일:**
- `backend/agent/prompts.py`

**변경 항목:**

### 5.1 INTENT_AND_TOOL_PROMPT
```python
# [Step 1: Intent 분류] 섹션의 Intent 목록 교체
- Insurance: 보험상품, 보장내용, 보험료 관련 질문
- Claim: 보험금 청구, 사고접수 관련 질문
- Policy: 약관, 특약, 면책조항 관련 질문
```

### 5.2 SCHEMA_MAP
```python
SCHEMA_MAP = {
    "Insurance": """
    insurance.products (product_id PK, name, type, premium NUMERIC, ...)
    """,
    ...
}
```

### 5.3 FEW_SHOT_MAP
```python
FEW_SHOT_MAP = {
    "Insurance": """Q: 보험료 상위 10개 상품
SQL: SELECT name, premium FROM insurance.products ORDER BY premium DESC LIMIT 10
""",
    ...
}
```

### 5.4 OPENCYPHER_PROMPT_TEMPLATE
- 그래프 구조 (엔티티 class, 관계 종류) 교체
- 관계 방향 예시 교체
- 예시 쿼리 교체

### 5.5 GRAPH_SCHEMA
```python
GRAPH_SCHEMA = {
    "Insurance": {"tenant": "insurance"},
    "Claim": {"tenant": "claim"},
    "Policy": {"tenant": "policy"},
}
```

**체크리스트:**
- [ ] Intent 목록 교체
- [ ] SCHEMA_MAP 교체
- [ ] FEW_SHOT_MAP 교체 (도메인당 3~5개 SQL 예시)
- [ ] OPENCYPHER_PROMPT_TEMPLATE 교체
- [ ] GRAPH_SCHEMA 교체

---

## Step 6: Tool 스키마 매핑

각 Tool이 Intent에 따라 올바른 DB/인덱스를 참조하도록 설정한다.

**수정 파일:**
- `backend/tools/text2sql.py` — Intent → 스키마 매핑
- `backend/tools/rag.py` — Intent → OpenSearch 인덱스명 매핑
- `backend/tools/graphrag.py` — Intent → Neptune tenant 매핑
- `backend/tools/opencypher.py` — Intent → Neptune tenant 매핑

**매핑 패턴:**
```python
INDEX_MAP = {
    "Insurance": "rag-insurance",
    "Claim": "rag-claim",
    "Policy": "rag-policy",
}
```

**체크리스트:**
- [ ] text2sql: Intent → 스키마 매핑
- [ ] rag: Intent → 인덱스명 매핑
- [ ] graphrag: Intent → tenant 매핑
- [ ] opencypher: Intent → tenant 매핑

---

## Step 7: Config 업데이트

환경설정을 자신의 인프라에 맞게 수정한다.

**수정 파일:**
- `backend/config.py`
- `.env`

**체크리스트:**
- [ ] DB_HOST, NEPTUNE_ENDPOINT, OPENSEARCH_ENDPOINT
- [ ] LLM_MODEL_ID (필요시 변경)
- [ ] PRICING (모델 변경 시 단가 수정)
- [ ] DYNAMODB_TABLE

---

## Step 8: Frontend 도메인 탭 변경

UI의 도메인 관련 표시를 변경한다.

**수정 파일:**
- `frontend/src/components/visualization/GraphNetworkPage.tsx` — 서브탭 변경
- `frontend/src/components/sidebar/Sidebar.tsx` — 예시 쿼리 도메인 그룹
- `frontend/src/App.tsx` — 앱 타이틀
- `frontend/src/types/index.ts` — Intent 타입 (선택)

**체크리스트:**
- [ ] Graph Network 서브탭: [ETF][채권][펀드] → 자신의 도메인
- [ ] Sidebar 예시 쿼리 아코디언 그룹명
- [ ] 앱 타이틀 변경

---

## Step 9: 예시 쿼리 작성

도메인별 예시 질의를 작성한다.

**수정 파일:**
- `pipeline/data/mock/example_queries.json`

**형식:**
```json
{
  "domains": {
    "Insurance": {
      "text2sql": [
        { "question": "보험료 상위 10개 상품은?", "description": "보험료 기준 정렬" }
      ],
      "rag": [
        { "question": "암보험의 보장 범위는?", "description": "문서 검색" }
      ],
      "graphrag": [
        { "question": "삼성생명 상품 간 관계는?", "description": "관계 탐색" }
      ],
      "opencypher": [
        { "question": "보험상품 네트워크 보여줘", "description": "그래프 시각화" }
      ]
    }
  }
}
```

**체크리스트:**
- [ ] 도메인당 Tool별 2~3개 예시 (총 8~12개/도메인)

---

## Step 10: 빌드 및 배포

```bash
# 1. 인프라 배포 (Step 변경 시)
cd infra && npx cdk deploy --all

# 2. 데이터 생성 및 적재
python -m pipeline.main generate-csv
python -m pipeline.main generate-md
python -m pipeline.main load-db
python -m pipeline.main index-graphrag
python -m pipeline.main index-rag
python -m pipeline.main generate-queries

# 3. 애플리케이션 배포
docker-compose up -d --build

# 4. 검증
curl http://localhost:8000/api/health
# 브라우저에서 각 도메인 질의 테스트
```

**체크리스트:**
- [ ] .env 파일 생성 (인프라 출력값 반영)
- [ ] Docker 빌드 성공
- [ ] 헬스체크 통과
- [ ] 각 도메인 × 각 Tool 질의 테스트

---

## 전체 체크리스트 요약

| Step | 작업 | 핵심 파일 |
|------|------|----------|
| 1 | 도메인/Intent 정의 | (설계) |
| 2 | DB 스키마 | `pipeline/models/*.py` |
| 3 | 데이터 생성기 | `pipeline/generators/*.py` |
| 4 | 데이터 적재기 | `pipeline/loaders/*.py` |
| 5 | Agent 프롬프트 | `backend/agent/prompts.py` |
| 6 | Tool 매핑 | `backend/tools/*.py` |
| 7 | Config | `backend/config.py`, `.env` |
| 8 | Frontend 탭 | `GraphNetworkPage.tsx`, `Sidebar.tsx`, `App.tsx` |
| 9 | 예시 쿼리 | `example_queries.json` |
| 10 | 빌드/배포 | `docker-compose.yml` |
