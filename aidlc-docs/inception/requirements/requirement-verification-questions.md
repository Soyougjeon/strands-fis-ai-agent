# Requirements Verification Questions

Please answer the following questions to help clarify the requirements for the Strands Agents + Chatbot Web UI project.

---

## Question 1
Strands Agent가 기존 데이터 소스 중 어떤 것을 활용해야 하나요?

A) Aurora PostgreSQL만 (구조화된 ETF 데이터 직접 조회)
B) Neptune + OpenSearch만 (GraphRAG 질의만 사용)
C) 모두 활용 - RDB 직접 조회 + GraphRAG 질의 + PDF 문서 검색 (권장)
D) RDB + GraphRAG (PDF 직접 검색은 제외)
X) Other (please describe after [Answer]: tag below)

[Answer]: C - RDB, GraphRAG, RAG 모두 활용

---

## Question 2
챗봇 Web UI의 배포 환경은 어디인가요?

A) AWS 서버리스 (Lambda + API Gateway + S3/CloudFront)
B) AWS 컨테이너 (ECS/Fargate)
C) AWS EC2 인스턴스
D) 로컬 개발 환경 전용 (PoC/데모)
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 3
챗봇 Web UI 프론트엔드 기술 스택 선호도가 있나요?

A) React + TypeScript (SPA)
B) Next.js (SSR/SSG)
C) Streamlit (Python 기반 빠른 프로토타이핑)
D) 기술 스택 무관 - AI가 최적 선택 (권장)
X) Other (please describe after [Answer]: tag below)

[Answer]: A - React + TypeScript. 동적 차트/그래프 시각화가 매우 중요. Python 실행 결과를 백엔드 API 통해 프론트엔드에 렌더링.

---

## Question 4
Strands Agent에게 부여할 Tool(도구) 범위는 어디까지인가요?

A) 읽기 전용 - 데이터 조회만 (ETF 정보 검색, GraphRAG 질의)
B) 읽기 + 비교/분석 - 데이터 조회 + ETF 비교, 포트폴리오 분석 등 계산 로직
C) 읽기 + 분석 + 외부 연동 - 실시간 시세 조회, 뉴스 검색 등 외부 API 포함
D) 전체 - 위 모두 + 스크래핑 실행/인덱싱 트리거 등 파이프라인 관리 포함
X) Other (please describe after [Answer]: tag below)

[Answer]: X - 3 Intent(ETF/채권/펀드) x 4 Method(Text2SQL/RAG/GraphRAG/OpenCypher). 읽기 방식 4가지: Text2SQL(Aurora PG SQL), RAG(PDF 벡터 검색), GraphRAG(LexicalGraph 자동 탐색), OpenCypher(Neptune 직접 그래프 쿼리).

---

## Question 5
사용자 인증/인가가 필요한가요?

A) 불필요 - 공개 데모/PoC 용도
B) 간단한 인증 - API Key 또는 간단한 로그인
C) AWS Cognito 기반 사용자 인증
D) 기업 SSO 연동 (SAML/OIDC)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 6
대화 이력(conversation history) 관리가 필요한가요?

A) 불필요 - 단발성 질의만 지원
B) 세션 내 유지 - 브라우저 세션 동안만 대화 이력 유지
C) 영구 저장 - 사용자별 대화 이력을 DB에 저장하고 재방문 시 조회 가능
D) 영구 저장 + 공유 - 대화 이력 저장 + 다른 사용자와 공유 가능
X) Other (please describe after [Answer]: tag below)

[Answer]: C - 영구 저장 + Admin 화면 구성(대화 이력 관리, 사용 통계) + LLM 토큰 사용량 표시. 향후 활용 방안 마련.

---

## Question 7
챗봇의 응답 언어는 무엇인가요?

A) 한국어 전용
B) 영어 전용
C) 한국어/영어 자동 감지 (사용자 입력 언어에 맞춤)
D) 다국어 지원 (한/영/일/중 등)
X) Other (please describe after [Answer]: tag below)

[Answer]: C

---

## Question 8
동시 사용자 규모는 어느 정도인가요?

A) 1-5명 (개인/소규모 팀 데모)
B) 5-50명 (부서/팀 내부 사용)
C) 50-500명 (사내 서비스)
D) 500명 이상 (대규모 서비스)
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 9
기존 스크래핑 파이프라인(데이터 수집)도 이번 프로젝트에 포함하나요?

A) 포함 - 기존 파이프라인 코드를 이 프로젝트로 통합
B) 참조만 - 기존 파이프라인은 별도 유지, Agent가 결과 데이터만 사용
C) 확장 - 기존 파이프라인 통합 + 새로운 데이터 소스 추가
X) Other (please describe after [Answer]: tag below)

[Answer]: B - 기존 파이프라인은 별도 유지. Mock 데이터 생성 및 입력 파이프라인을 신규 구축. GraphRAG 인덱싱은 기존 indexer.py 재사용.

---

## Question 10
Strands Agent의 LLM 모델 선택은?

A) Amazon Bedrock Claude (Sonnet/Opus) - 기존 파이프라인과 동일
B) Amazon Bedrock Claude + 다른 모델 fallback (비용 최적화)
C) 모델 선택을 설정으로 변경 가능하게 (유연한 구조)
D) 기존 파이프라인 설정 그대로 사용
X) Other (please describe after [Answer]: tag below)

[Answer]: X - Amazon Bedrock Claude Sonnet 최신버전(claude-sonnet-4-6-v1:0), Embedding은 Amazon Bedrock Titan Embed Text v2

---

## Question 11: Security Extensions
Should security extension rules be enforced for this project?

A) Yes - enforce all SECURITY rules as blocking constraints (recommended for production-grade applications)
B) No - skip all SECURITY rules (suitable for PoCs, prototypes, and experimental projects)
X) Other (please describe after [Answer]: tag below)

[Answer]: B - AIDLC SECURITY 규칙 건너뜀. 실제 인프라 보안(VPC, SG, SSL, IAM)은 이미 적용됨.

---
