# Requirements Document

## Intent Analysis

| 항목 | 분석 |
|------|------|
| **User Request** | 기존 TIGER ETF 데이터 파이프라인(finance-graphrag-demo)을 기반으로 Strands Agents를 구축하고, 챗봇 Web UI 서비스를 추가. ETF/채권/펀드 3가지 도메인 지원. |
| **Request Type** | New Feature (Agent 백엔드 + Web UI 프론트엔드 + Mock 데이터 파이프라인) |
| **Scope** | Multiple Components - Agent, API, Frontend, Mock Data, Admin |
| **Complexity** | Complex - 다수 AWS 서비스 통합, 4가지 데이터 접근 방식, 동적 시각화 |
| **Depth Level** | Comprehensive |

---

## 1. Functional Requirements

### FR-01: Strands Agent 코어

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-01-01 | Strands Agents SDK 기반 Agent 구현 | 필수 |
| FR-01-02 | Orchestrator Agent: Intent 분류 + Tool 라우팅 + 하위 Agent 조율 | 필수 |
| FR-01-03 | 3가지 Intent 분류: ETF, 채권(Bond), 펀드(Fund) | 필수 |
| FR-01-04 | 4가지 데이터 접근 Tool 지원 | 필수 |
| FR-01-05 | 멀티턴 대화 지원 (대화 컨텍스트 유지) | 필수 |
| FR-01-06 | 스트리밍 응답 지원 (토큰 단위 실시간 출력) | 필수 |
| FR-01-07 | Agent 실행 과정 투명성 (Observability) | 필수 |

#### FR-01-04 상세: 4가지 데이터 접근 Tool

```
+----------------------------------------------------------+
|                  Orchestrator Agent                        |
|                                                            |
|  Intent Detection: ETF / Bond / Fund                       |
|                                                            |
|  +------------+ +--------+ +----------+ +-------------+    |
|  | Text2SQL   | | RAG    | | GraphRAG | | OpenCypher  |    |
|  | Tool       | | Tool   | | Tool     | | Tool        |    |
|  +-----+------+ +---+----+ +----+-----+ +------+------+   |
|        |             |          |               |           |
+----------------------------------------------------------+
         |             |          |               |
         v             v          v               v
   Aurora PG      OpenSearch   Neptune +      Neptune
   (SQL Query)    (Vector)     OpenSearch     (Cypher)
                               (LexicalGraph)
```

| Tool | 대상 DB | 용도 | 예시 질의 |
|------|---------|------|----------|
| **Text2SQL** | Aurora PostgreSQL | 정확한 수치/필터 조회 | "AUM 상위 10개 ETF 목록" |
| **RAG** | OpenSearch (벡터) | MD 문서 비정형 검색 | "투자설명서에서 환헤지 전략 설명" |
| **GraphRAG** | Neptune + OpenSearch | LLM 기반 관계 탐색 | "반도체 섹터 ETF의 투자 위험은?" |
| **OpenCypher** | Neptune | 그래프 직접 쿼리 | "TIGER S&P500에서 2홉 연결 엔티티" |

#### FR-01-07 상세: Agent 실행 과정 투명성

UI에 각 단계별 실시간 표시:

| 단계 | 표시 정보 |
|------|----------|
| Intent Detection | 분류 결과 (ETF/채권/펀드), 소요시간, 토큰, 비용 |
| Tool Selection | 선택된 Tool명, 선택 근거, 소요시간, 토큰, 비용 |
| Query Generation | 생성된 쿼리 (SQL/Cypher/검색어), 소요시간, 토큰, 비용 |
| Query Execution | 실행 결과 요약 (row 수, 노드 수 등), 소요시간 |
| Response Generation | 최종 응답 생성, 소요시간, 토큰, 비용 |
| **Total** | **총 소요시간, 총 토큰(input/output), 총 비용** |

상세 정보는 탭으로 분리 표시:

| 탭 | 내용 |
|----|------|
| OpenCypher | 실행 쿼리, 소요시간, 결과 데이터 테이블 |
| OpenSearch | 벡터 검색 쿼리, top_k, similarity score, 결과 |
| GraphRAG | 실행 단계별 함수명, 중간 결과, 각 쿼리 데이터 |
| Text2SQL | 생성된 SQL, 소요시간, 결과 데이터 테이블 |
| 결과 | 최종 응답에 사용된 컨텍스트 요약 |

토큰 비용 계산:

| 모델 | Input | Output |
|------|-------|--------|
| Claude Sonnet | $3.00 / 1M tokens | $15.00 / 1M tokens |
| Titan Embed v2 | $0.02 / 1M tokens | - |

### FR-02: 챗봇 Web UI

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-02-01 | React + TypeScript SPA 챗봇 인터페이스 | 필수 |
| FR-02-02 | 실시간 스트리밍 응답 표시 | 필수 |
| FR-02-03 | 동적 차트 시각화 (ECharts/Plotly.js) | 필수 |
| FR-02-04 | 그래프 네트워크 시각화 (Cytoscape.js/vis.js) | 필수 |
| FR-02-05 | Python 실행 결과를 백엔드 API로 받아 프론트엔드 렌더링 | 필수 |
| FR-02-06 | 코글(Coggle) 사이드바: 대화 이력 + 예시 쿼리 | 필수 |
| FR-02-07 | 마크다운 응답 렌더링 | 필수 |
| FR-02-08 | Agent 실행 과정 패널 (FR-01-07 연동) | 필수 |
| FR-02-09 | 상세 탭 UI (OpenCypher/OpenSearch/GraphRAG/Text2SQL/결과) | 필수 |

#### FR-02 UI 구성: 상단 멀티탭 + 코글 사이드바

상단 탭:

| 탭 | 내용 |
|----|------|
| **Chat** | 기본 대화 (2분할: Chat Area + Agent Process) |
| **Graph Network** | Cytoscape.js 그래프 전체 화면, 서브탭 [ETF] [채권] [펀드] |
| **Admin** | 대화 이력, 토큰 사용량/비용, 시스템 상태 |

코글(Coggle) 사이드바 (접기/펼치기):

| 섹션 | 내용 |
|------|------|
| 대화 이력 | 이전 대화 목록, 클릭 시 조회 |
| 예시 쿼리 | ETF/채권/펀드별 예시 질의 + [실행] 버튼 |

Chat 탭 레이아웃 (2분할):

```
+------------------------------------------------------------------+
| [Chat] [Graph Network] [Admin]                                    |
+------------------------------------------------------------------+
| [=]      |                                |                        |
| 코글     | Chat Area                      | Agent Process          |
| Sidebar  |                                |                        |
|          | +----------------------------+ | Step1: Intent           |
| 대화     | | Agent 응답 (마크다운)       | |  0.3s 120tok $0.0004  |
| 이력     | |                            | |  > ETF                 |
|          | | +----------------------+   | |                        |
| ------   | | | 동적 차트 (ECharts)  |   | | Step2: Tool             |
|          | | +----------------------+   | |  0.2s 85tok $0.0003   |
| 예시     | |                            | |                        |
| 쿼리     | | +----------------------+   | | [OpenCypher][Search]   |
|          | | | 테이블 (SQL 결과)    |   | | [GraphRAG][SQL][결과]  |
| [ETF]    | | +----------------------+   | | +------------------+   |
| [채권]   | +----------------------------+ | | 탭 상세 내용       |   |
| [펀드]   |                                | +------------------+   |
|          | +----------------------------+ |                        |
| [=]접기  | | [메시지 입력]        [전송] | | Total: 3.2s $0.0034   |
|          | +----------------------------+ |                        |
+----------+--------------------------------+------------------------+
             ~55%                              ~45%
```

Graph Network 탭:

```
+------------------------------------------------------------------+
| [Chat] [Graph Network] [Admin]                                    |
+------------------------------------------------------------------+
| [=]      |  [ETF] [채권] [펀드]                    [필터] [검색]   |
| 코글     |                                                        |
| Sidebar  |       O --- TIGER S&P500                                |
|          |      /|\                                                |
|          |     / | \                                               |
|          |    O  O  O                                              |
|          |  S&P  환율 미래에셋                                      |
|          |  500  위험 자산운용                                      |
|          |                                                         |
|          |  [줌] [팬] [노드 검색] [관계 필터]                        |
+----------+---------------------------------------------------------+
```

### FR-03: 백엔드 API (FastAPI)

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-03-01 | FastAPI 기반 REST/WebSocket API | 필수 |
| FR-03-02 | POST /api/chat - Agent 대화 엔드포인트 | 필수 |
| FR-03-03 | WebSocket /ws/chat - 스트리밍 대화 (Agent 실행 과정 포함) | 필수 |
| FR-03-04 | GET /api/conversations - 대화 이력 목록 | 필수 |
| FR-03-05 | GET /api/conversations/{id} - 대화 상세 조회 | 필수 |
| FR-03-06 | GET /api/visualize/graph - 그래프 시각화 데이터 (Neptune) | 필수 |
| FR-03-07 | GET /api/visualize/chart - 차트 데이터 | 필수 |
| FR-03-08 | GET /api/admin/token-usage - 토큰 사용량/비용 통계 | 필수 |
| FR-03-09 | GET /api/admin/conversations - Admin 대화 이력 관리 | 필수 |
| FR-03-10 | GET /api/examples - 예시 쿼리 목록 (ETF/채권/펀드) | 필수 |

### FR-04: Mock 데이터

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-04-01 | ETF Mock CSV 파일 생성 (기존 스키마 기반) | 필수 |
| FR-04-02 | 채권(Bond) Mock CSV 파일 생성 (신규 스키마) | 필수 |
| FR-04-03 | 펀드(Fund) Mock CSV 파일 생성 (신규 스키마) | 필수 |
| FR-04-04 | CSV -> Aurora PostgreSQL 입력 파이프라인 | 필수 |
| FR-04-05 | Mock 데이터 GraphRAG 인덱싱 (MD 파일 기반, 기존 indexer.py 재사용) | 필수 |
| FR-04-06 | RAG 인덱싱: MD 파일 -> Chunking -> Titan Embed -> OpenSearch (벡터만) | 필수 |
| FR-04-07 | Neptune 멀티테넌시: ETF/채권/펀드 3개 테넌트로 분리 구성 | 필수 |

#### Mock 데이터 파일 구조

```
data/mock/
  +-- etf/
  |   +-- etf_products.csv
  |   +-- etf_holdings.csv
  |   +-- etf_performance.csv
  |   +-- etf_distributions.csv
  +-- bond/
  |   +-- bond_products.csv
  |   +-- bond_prices.csv
  +-- fund/
  |   +-- fund_products.csv
  |   +-- fund_holdings.csv
  |   +-- fund_performance.csv
  +-- graphrag/
      +-- etf_*.md
      +-- bond_*.md
      +-- fund_*.md
```

#### Mock 데이터 스키마

**ETF** (기존 tiger_etf 스키마 재사용):
- etf_products, etf_holdings, etf_performance, etf_distributions

**채권 (Bond)** - 신규:
- bond_products: 채권명, 발행사, 금리, 만기일, 신용등급, 발행금액, 통화
- bond_prices: 채권코드, 거래일, 수익률, 가격

**펀드 (Fund)** - 신규:
- fund_products: 펀드명, 운용사, 유형, 설정일, 총보수, 순자산, 벤치마크
- fund_holdings: 펀드코드, 기준일, 종목명, 비중
- fund_performance: 펀드코드, 기준일, 기간별 수익률

#### 입력 흐름

```
CSV 파일 -> Python 스크립트 -> Aurora PostgreSQL INSERT
MD 파일  -> 기존 indexer.py -> Neptune (멀티테넌시) + OpenSearch (GraphRAG)
MD 파일  -> Chunking -> Titan Embed -> OpenSearch (일반 RAG 벡터)
```

#### Neptune 멀티테넌시 구조

```
Neptune Database (단일 클러스터)
    +-- Tenant: ETF   (ETF Entity/Relationship 그래프)
    +-- Tenant: Bond   (채권 Entity/Relationship 그래프)
    +-- Tenant: Fund   (펀드 Entity/Relationship 그래프)
```

#### OpenSearch 인덱스 구조

```
OpenSearch Serverless
    +-- index: rag-etf        (ETF MD 벡터, 일반 RAG용)
    +-- index: rag-bond       (채권 MD 벡터, 일반 RAG용)
    +-- index: rag-fund       (펀드 MD 벡터, 일반 RAG용)
    +-- index: graphrag-etf   (ETF GraphRAG 벡터)
    +-- index: graphrag-bond  (채권 GraphRAG 벡터)
    +-- index: graphrag-fund  (펀드 GraphRAG 벡터)
```

### FR-05: Admin 화면

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-05-01 | 대화 이력 관리 (목록, 상세, 검색) | 필수 |
| FR-05-02 | LLM 토큰 사용량 대시보드 (요청별/일별/누적/비용) | 필수 |
| FR-05-03 | 사용 통계 (질의 수, 응답 시간, 인텐트 분포) | 필수 |
| FR-05-04 | 시스템 상태 모니터링 (DB 연결, Agent 상태) | 선택 |

### FR-06: 대화 이력 관리

| ID | 요구사항 | 우선순위 |
|----|---------|---------|
| FR-06-01 | 대화 세션 생성/조회/삭제 | 필수 |
| FR-06-02 | 메시지 영구 저장 (사용자 입력 + Agent 응답) | 필수 |
| FR-06-03 | 재방문 시 이전 대화 조회 가능 | 필수 |
| FR-06-04 | 토큰 사용량 메시지별 기록 (input/output/비용) | 필수 |
| FR-06-05 | 메타데이터 저장 (intent, tools_used, latency, 각 단계별 토큰/비용) | 필수 |

---

## 2. Non-Functional Requirements

### NFR-01: 성능

| ID | 요구사항 | 목표 |
|----|---------|------|
| NFR-01-01 | Agent 첫 응답 시간 (TTFB) | 3초 이내 |
| NFR-01-02 | 스트리밍 토큰 지연 | 100ms 이내 |
| NFR-01-03 | Text2SQL 쿼리 응답 | 2초 이내 |
| NFR-01-04 | 그래프 시각화 렌더링 | 1초 이내 |

### NFR-02: 배포 환경

| ID | 요구사항 | 설정 |
|----|---------|------|
| NFR-02-01 | EC2 인스턴스 | 동일 VPC 내 배포 |
| NFR-02-02 | Python 백엔드 | EC2에서 FastAPI 실행 |
| NFR-02-03 | React 프론트엔드 | Nginx 리버스 프록시 (정적 파일 + API + WebSocket) |
| NFR-02-04 | 동시 사용자 | 1-5명 (Basic Auth로 접근 제어) |
| NFR-02-05 | 단일 포트 | 포트 80 (Nginx), EC2 보안그룹 인바운드 허용 |

### NFR-03: 인프라 전제조건

이미 구성된 AWS 리소스를 사용:

| 서비스 | 구성 | 연결 방식 |
|--------|------|----------|
| Aurora PostgreSQL | Writer/Reader endpoint, SSL verify-full | EC2 SG -> RDS SG, port 5432 |
| Neptune Database | Writer/Reader endpoint, 멀티테넌시 3개 | EC2 SG -> Neptune SG, port 8182 |
| OpenSearch Serverless | VPC Endpoint, 6개 인덱스 | EC2 SG -> AOSS VPC EP SG, port 443 |
| Amazon Bedrock | Claude Sonnet + Titan Embed v2 | IAM 역할 |
| Secrets Manager | Aurora PG 비밀번호 | IAM 역할 |

#### 보안그룹 체크리스트

| Source | Destination | Port | 용도 |
|--------|-------------|------|------|
| EC2 SG (outbound) | RDS SG | 5432 | Aurora PG 접속 |
| EC2 SG (outbound) | Neptune SG | 8182 | Neptune 접속 |
| EC2 SG (outbound) | AOSS VPC Endpoint SG | 443 | OpenSearch Serverless 접속 |
| RDS SG (inbound) | EC2 SG | 5432 | Aurora PG 허용 |
| Neptune SG (inbound) | EC2 SG | 8182 | Neptune 허용 |
| AOSS VPC Endpoint SG (inbound) | EC2 SG | 443 | OpenSearch Serverless 허용 |
| EC2 SG (inbound) | 0.0.0.0/0 | 80 | Nginx (Basic Auth 보호) |

### NFR-04: 기술 스택

| 레이어 | 기술 | 버전 |
|--------|------|------|
| Agent Framework | Strands Agents SDK | latest |
| LLM | Amazon Bedrock Claude Sonnet | claude-sonnet-4-6-v1:0 |
| Embedding | Amazon Bedrock Titan Embed Text v2 | 1024-dim |
| Backend API | Python FastAPI | latest |
| Frontend | React + TypeScript | latest |
| 차트 시각화 | ECharts / Plotly.js | latest |
| 그래프 시각화 | Cytoscape.js / vis.js | latest |
| GraphRAG | graphrag-toolkit (LexicalGraph) | v3.16.1 |
| RDB ORM | SQLAlchemy 2.0 | 기존 모델 재사용 |
| 대화 이력 DB | Aurora PostgreSQL | 기존 클러스터 |
| Web Server | Nginx | latest |

### NFR-05: 응답 언어

- 사용자 입력 언어에 맞춰 자동 감지/응답 (한국어/영어)

---

## 3. Architecture Overview

```
+------------------------------------------------------------------+
|                         EC2 Instance                              |
|                                                                    |
|  +-------------------+          +-----------------------------+   |
|  | Nginx             |          | FastAPI Backend              |   |
|  | - React SPA       | -------> | - Orchestrator Agent        |   |
|  | - /api/* proxy    |  API     | - WebSocket Handler         |   |
|  | - /ws/* proxy     |          | - Conversation Manager      |   |
|  | - Basic Auth      |          | - Token Usage Tracker       |   |
|  +-------------------+          +-----------------------------+   |
|                                          |                        |
+------------------------------------------------------------------+
                                           |
              +----------------------------+-------------------+
              |              |             |                    |
              v              v             v                    v
        Aurora PG       Neptune DB    OpenSearch          Bedrock
        (Text2SQL +     (OpenCypher   Serverless         (Claude +
         Chat History    + GraphRAG    (RAG +              Titan)
         + Token Usage)  멀티테넌시)   GraphRAG)
```

### Text Alternative
```
EC2 Instance:
  Nginx (React SPA + Basic Auth) -> FastAPI Backend
    -> Orchestrator Agent (Intent: ETF/Bond/Fund)
      -> Tool: Text2SQL -> Aurora PG
      -> Tool: RAG -> OpenSearch (rag-etf/bond/fund 인덱스)
      -> Tool: GraphRAG -> Neptune (테넌트별) + OpenSearch (graphrag-etf/bond/fund)
      -> Tool: OpenCypher -> Neptune (테넌트별 직접 쿼리)
    -> Conversation Manager -> Aurora PG (chat history)
    -> Token Tracker -> Aurora PG (usage logs + cost)
  -> Bedrock (Claude Sonnet + Titan Embed v2)
```

---

## 4. Data Flow Summary

### 질의 처리 흐름
```
User Input -> React UI -> WebSocket -> FastAPI
  -> Orchestrator Agent
    -> Intent Detection (ETF/Bond/Fund)
    -> Tool Selection (Text2SQL/RAG/GraphRAG/OpenCypher)
    -> Query Generation + Execution
    -> Each step: latency, tokens(in/out), cost tracked
  -> Streaming Response -> WebSocket -> React UI
    -> Text Rendering + Chart/Graph Visualization
    -> Agent Process Panel (단계별 실시간 표시)
```

### Mock 데이터 흐름
```
CSV 파일 -> Python 스크립트 -> Aurora PostgreSQL INSERT
MD 파일  -> 기존 indexer.py -> Neptune (멀티테넌시: ETF/Bond/Fund) + OpenSearch (GraphRAG)
MD 파일  -> Chunking -> Titan Embed -> OpenSearch (일반 RAG: rag-etf/bond/fund)
```

---

## 5. Out of Scope

| 항목 | 사유 |
|------|------|
| 사용자 인증/인가 | PoC 단계 (Basic Auth만), 향후 Cognito 추가 가능 |
| 기존 스크래핑 파이프라인 수정 | 별도 유지, Mock 데이터로 대체 |
| 실시간 시세/뉴스 외부 API | 1차 범위 외, 향후 Tool 추가 가능 |
| 모바일 UI | 데스크톱 웹 우선 |
| CI/CD 파이프라인 | 수동 배포 (PoC) |
| AIDLC SECURITY 확장 규칙 | PoC 단계, 프로덕션 전환 시 적용 |
| Mock PDF 문서 생성 | 불필요, RAG는 MD 파일 기반 |
| Graph Network 전체 통합 뷰 | 테넌트 간 관계 없음, ETF/채권/펀드 개별 탭만 |

---

## 6. Assumptions

1. AWS 인프라(Aurora PG, Neptune, OpenSearch, Bedrock)가 이미 구성되어 있음
2. EC2 인스턴스가 동일 VPC 내에 있으며 보안그룹 규칙이 적용됨
3. Bedrock Claude Sonnet 최신버전 및 Titan Embed v2 접근 권한 있음
4. 기존 finance-graphrag-demo의 ORM 모델(models.py)과 GraphRAG indexer(indexer.py)를 참조/재사용
5. Mock 데이터로 개발 및 데모 진행, 실제 스크래핑 데이터는 기존 파이프라인에서 별도 관리
6. Neptune 멀티테넌시는 graphrag-toolkit의 네임스페이스 분리 방식 활용
7. 데이터 구성도/정의서는 Construction Phase의 Functional Design에서 상세 정의
