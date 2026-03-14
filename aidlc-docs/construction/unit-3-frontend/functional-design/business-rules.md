# Business Rules - Unit 3: Frontend

## BR-01: Chat UI Rules

### BR-01-01: 메시지 표시
- 사용자 메시지: 우측 정렬, 파란 배경
- Assistant 응답: 좌측 정렬, 마크다운 렌더링
- 스트리밍 중: 커서 애니메이션 표시
- 빈 메시지 전송 불가 (버튼 비활성화)

### BR-01-02: 스트리밍 동작
- text_chunk 이벤트 수신 시 즉시 렌더링 (debounce 없음)
- 스트리밍 중 메시지 입력 가능하나 전송 비활성화
- response_complete 수신 시 전송 버튼 재활성화

### BR-01-03: 데이터 테이블
- SQL 결과가 배열이면 자동 테이블 렌더링
- 최대 100행 표시, 초과 시 "더보기" 표시
- 숫자 컬럼: 천단위 구분자 + 소수점 2자리
- 긴 텍스트: 200자 이상 시 말줄임 처리

## BR-02: Agent Process Panel Rules

### BR-02-01: 단계별 표시
- 각 단계는 이벤트 수신 시 순서대로 나타남 (애니메이션)
- 미완료 단계: 회색, 진행 중: 파란 스피너, 완료: 체크마크
- latency: 소수점 3자리 (초)
- tokens: 정수 (천단위 구분)
- cost: $ + 소수점 6자리

### BR-02-02: 상세 탭
- 탭은 항상 5개 표시 (OpenCypher, Search, GraphRAG, SQL, 결과)
- 활성 Tool에 해당하는 탭 자동 선택
  - text2sql → SQL 탭
  - rag → Search 탭
  - graphrag → GraphRAG 탭
  - opencypher → OpenCypher 탭
- SQL/Cypher: 코드 하이라이팅 적용
- 데이터 없는 탭: "해당 데이터가 없습니다" 표시

## BR-03: Chart Visualization Rules

### BR-03-01: ECharts 차트
- chart_type에 따라 자동 렌더링
  - "bar" → 가로 바 차트 (값 내림차순)
  - "line" → 시계열 라인 차트
  - "pie" → 파이 차트 (비율 표시)
- 차트 높이: 300px 고정
- 반응형 너비 (컨테이너 100%)
- 마우스 호버 시 tooltip 표시
- chart_data가 null이면 차트 미표시

### BR-03-02: 차트 스타일
- 색상 팔레트: Tailwind 기본 색상 사용
- 폰트: 시스템 기본
- 한글 레이블 지원

## BR-04: Graph Network Rules

### BR-04-01: Cytoscape.js 그래프
- 노드 색상 (type별):
  - ETF/Fund/Bond: #3B82F6 (파랑)
  - Index/Benchmark: #10B981 (초록)
  - Holding/Sector: #F59E0B (주황)
  - RiskFactor: #EF4444 (빨강)
  - 기타: #6B7280 (회색)
- 노드 크기: 기본 30px, 연결 수에 비례 (최대 60px)
- 엣지 색상: #94A3B8 (slate-400)
- 레이아웃: cose-bilkent
- 초기 fit: 전체 그래프가 화면에 맞도록

### BR-04-02: 인터랙션
- 노드 클릭: 선택 하이라이트 + properties 패널 표시
- 노드 더블클릭: 확장 쿼리 (연결된 노드 추가 로드)
- 줌: 마우스 휠 (min 0.3x, max 3x)
- 팬: 마우스 드래그 (빈 공간)
- 노드 검색: 이름 일치 시 해당 노드 줌/하이라이트

## BR-05: Sidebar Rules

### BR-05-01: 대화 이력
- 최근순 정렬 (updated_at 내림차순)
- 제목 최대 30자 (말줄임)
- 현재 세션: 볼드 + 배경 하이라이트
- 대화 이력 수신: 앱 시작 시 + 새 대화 저장 후 갱신

### BR-05-02: 예시 쿼리
- 도메인별 아코디언 (ETF/채권/펀드)
- 클릭 시 자동 전송 (확인 없이)
- Tool별 하위 그룹 (text2sql/rag/graphrag/opencypher)

### BR-05-03: 접기/펼치기
- 토글 버튼으로 사이드바 숨김/표시
- 접힌 상태: 아이콘만 표시 (40px 너비)
- 펼친 상태: 250px 너비
- 전환 시 애니메이션 (300ms)

## BR-06: Admin Rules

### BR-06-01: 토큰 통계
- 기본 기간: daily
- 기간 변경 시 API 재호출
- 차트: tokens_in (파랑) + tokens_out (주황) + cost (초록) 3선
- 총합: 카드 4개 (tokens_in, tokens_out, cost, request_count)

### BR-06-02: 대화 관리
- 삭제 시 확인 다이얼로그 필수 ("삭제하시겠습니까?")
- 삭제 성공 → 목록 갱신
- 대화 클릭 → Chat 탭으로 이동 + 해당 대화 로드

## BR-07: WebSocket Rules

### BR-07-01: 연결
- 앱 시작 시 자동 연결
- 연결 실패/끊김 → 3초 후 자동 재연결
- 최대 재연결 시도: 5회
- 5회 초과 → "연결 실패" 알림 표시
- 재연결 성공 → 카운터 리셋

### BR-07-02: 에러 처리
- error 이벤트 수신 → 에러 메시지 표시 (토스트)
- JSON 파싱 실패 → 무시 (콘솔 로그)

## BR-08: 반응형 & 접근성

### BR-08-01: 반응형
- 최소 지원 너비: 1024px (데스크톱만)
- 1024px 이하: 사이드바 자동 접힘
- Agent Process Panel: 1280px 이하 시 하단으로 이동 (세로 분할)

### BR-08-02: 스타일
- Tailwind CSS 사용
- 다크 모드: 미지원 (밝은 테마만)
- 한글 폰트: 시스템 기본 (Pretendard 권장)

## BR-09: Nginx Rules

### BR-09-01: Basic Auth
- 5명 내부 테스터 계정
- .htpasswd 파일로 관리
- API/WS 경로도 인증 필요

### BR-09-02: 프록시
- /api/* → FastAPI :8000
- /ws/* → FastAPI :8000 (WebSocket Upgrade)
- / → React SPA (try_files → index.html)
- WebSocket timeout: 86400초 (24시간)
