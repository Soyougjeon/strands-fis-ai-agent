# Unit of Work Plan

## Decomposition Approach
기존 Application Design의 컴포넌트/서비스 구조와 실행 계획의 예비 유닛을 기반으로, 의존성 순서에 따라 3개 유닛으로 분해한다.

## Plan Steps

- [x] Step 1: 유닛 경계 및 책임 정의
- [x] Step 2: 유닛별 컴포넌트/서비스 매핑
- [x] Step 3: 유닛 간 의존성 매트릭스 생성
- [x] Step 4: 요구사항 -> 유닛 매핑 (Story Map 대체)
- [x] Step 5: 개발 순서 및 통합 전략 확정
- [x] Step 6: unit-of-work.md 생성
- [x] Step 7: unit-of-work-dependency.md 생성
- [x] Step 8: unit-of-work-story-map.md 생성
- [x] Step 9: 유닛 경계 및 의존성 검증

## Preliminary Unit Structure

| Unit | Components | Services |
|------|-----------|----------|
| Unit 1: Mock Data Pipeline | C7 | S7 |
| Unit 2: Agent Backend | C2, C3, C4a-d, C5, C6 | S1-S6 |
| Unit 3: Frontend | C1, C8 | - |

## Clarifying Questions

### Q1: 유닛 2(Agent Backend) 분할 여부
Agent Backend는 FastAPI + Agent + 4 Tools + Conv + Token을 포함합니다.
이를 하나의 유닛으로 유지할지, 더 세분화할지 결정이 필요합니다.

- A) 하나의 유닛으로 유지 (모놀리식 백엔드, 단일 Python 패키지) - PoC에 적합
- B) FastAPI/Agent와 Tools를 별도 유닛으로 분리 (2개 유닛)
- C) FastAPI, Agent, Tools, Services를 각각 별도 유닛 (4개 유닛)

[Answer]: A - 하나의 유닛으로 유지 (모놀리식 백엔드)

### Q2: 개발 순서
유닛 간 의존성에 따른 개발 순서를 확인합니다.

- A) Mock Data -> Agent Backend -> Frontend (순차, 의존성 순서)
- B) Mock Data와 Agent Backend 병렬, 이후 Frontend
- C) 다른 순서 제안

[Answer]: A - Mock Data -> Agent Backend -> Frontend (순차)

### Q3: 코드 조직 구조
Workspace root에서의 코드 디렉토리 구조를 확인합니다.

- A) 모노레포 (backend/, frontend/, pipeline/ 디렉토리 분리)
- B) 백엔드 중심 (src/ 하위 모듈, frontend/ 별도)
- C) 다른 구조 제안

[Answer]: A - 모노레포 (backend/, frontend/, pipeline/)
