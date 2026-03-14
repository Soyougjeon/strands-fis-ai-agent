# Business Overview

## Business Context Diagram

```
+------------------------------------------------------------------+
|                    TIGER ETF Knowledge System                     |
+------------------------------------------------------------------+
|                                                                    |
|  +---------------------+     +--------------------------------+   |
|  | Data Collection      |     | Knowledge Graph (GraphRAG)     |   |
|  |                     |     |                                |   |
|  | Mirae Asset Website  | --> | Entity Extraction (LLM)       |   |
|  | (TIGER ETF Portal)  |     | Relationship Inference         |   |
|  |                     |     | Semantic Search                |   |
|  +---------------------+     +--------------------------------+   |
|           |                            |                          |
|           v                            v                          |
|  +---------------------+     +--------------------------------+   |
|  | Aurora PostgreSQL    |     | Neptune DB + OpenSearch        |   |
|  | (Structured Data)   |     | (Graph + Vector Store)         |   |
|  +---------------------+     +--------------------------------+   |
|                                        |                          |
|                                        v                          |
|                               +---------------------+             |
|                               | Query Engine         |             |
|                               | (NL Question -> NL   |             |
|                               |  Answer via Graph)   |             |
|                               +---------------------+             |
+------------------------------------------------------------------+
```

### Text Alternative
- Phase 1: Data Collection -> Aurora PostgreSQL
- Phase 2: Knowledge Graph Indexing -> Neptune DB + OpenSearch
- Phase 3: Query & Retrieval -> Natural Language Answers

## Business Description
- **Business Description**: TIGER ETF(미래에셋자산운용) 상품 정보를 수집하여 Knowledge Graph를 구축하고, 자연어 질의를 통해 ETF 상품 정보를 조회할 수 있는 금융 데이터 파이프라인 시스템
- **Business Transactions**:
  1. **ETF 상품 목록 수집**: 미래에셋 웹사이트에서 221개 TIGER ETF 상품 카테고리별 목록 수집
  2. **ETF 상세 정보 수집**: 각 ETF 상품의 상세 페이지(영문명, 벤치마크, 총보수, 상장일 등) 스크래핑
  3. **보유종목 수집**: 전체 ETF의 포트폴리오 보유종목(Excel) 다운로드 및 파싱
  4. **수익률 수집**: 기간별 수익률(1W, 1M, 3M, 6M, 1Y, 3Y, YTD) 추출
  5. **분배금 수집**: 각 ETF의 분배금 지급 이력(기준일, 지급일, 금액, 분배율) 수집
  6. **투자설명서 수집**: PDF 문서(간이/정식 투자설명서, 팩트시트, 규약 등) 다운로드
  7. **Knowledge Graph 인덱싱**: RDB + PDF 데이터를 LLM 기반 Entity/Relationship 추출하여 그래프 구축
  8. **자연어 질의 응답**: 사용자 질문 -> 벡터 검색 + 그래프 탐색 -> LLM 응답 생성
  9. **실험/평가**: 다양한 LLM/임베딩 모델 조합의 GraphRAG 성능 비교 평가
- **Business Dictionary**:
  | Term | Meaning |
  |------|---------|
  | TIGER ETF | 미래에셋자산운용의 ETF 브랜드 |
  | KSD Fund Code | 한국예탁결제원 펀드 고유코드 (예: KR7xxx) |
  | NAV | 순자산가치 (Net Asset Value) |
  | AUM | 순자산총액 (Assets Under Management) |
  | TER | 총보수비율 (Total Expense Ratio) |
  | GraphRAG | Graph-based Retrieval Augmented Generation |
  | LexicalGraph | AWS GraphRAG Toolkit의 지식 그래프 구축 프레임워크 |
  | Neptune | AWS의 관리형 그래프 데이터베이스 |
  | OpenSearch Serverless | AWS의 벡터 검색 서비스 (AOSS) |
  | Bedrock | AWS의 관리형 LLM 서비스 |

## Component Level Business Descriptions

### Scrapers (데이터 수집기)
- **Purpose**: 미래에셋 TIGER ETF 웹사이트에서 금융 데이터를 자동으로 수집
- **Responsibilities**: HTTP 요청, HTML/JSON/Excel 파싱, PDF 다운로드, 데이터 정규화, RDB 적재

### Parsers (데이터 파서)
- **Purpose**: 웹에서 수집한 원시 데이터(HTML, Excel)를 구조화된 형태로 변환
- **Responsibilities**: DOM 파싱, 필드 추출, 데이터 타입 변환, 유효성 검증

### GraphRAG Indexer (지식 그래프 인덱서)
- **Purpose**: 수집된 데이터를 LLM 기반 Entity/Relationship 추출을 통해 Knowledge Graph로 변환
- **Responsibilities**: 문서 로딩, 청크 분할, LLM 기반 추출, Neptune/OpenSearch 적재

### GraphRAG Query Engine (질의 엔진)
- **Purpose**: 사용자의 자연어 질문에 대해 그래프 탐색과 벡터 검색을 결합하여 응답 생성
- **Responsibilities**: 질의 임베딩, 벡터 유사도 검색, 그래프 탐색, LLM 응답 합성

### Experiment Framework (실험 프레임워크)
- **Purpose**: 다양한 LLM/임베딩 모델 조합의 GraphRAG 성능을 체계적으로 비교 평가
- **Responsibilities**: 실험 설정 관리, 인덱싱 실행, 평가 질의 수행, 메트릭 수집, 결과 비교
