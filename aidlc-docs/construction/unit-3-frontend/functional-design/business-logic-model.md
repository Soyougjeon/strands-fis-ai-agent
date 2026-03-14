# Business Logic Model - Unit 3: Frontend

## 1. 전체 UI 구조

```
+------------------------------------------------------------------+
| [Chat] [Graph Network] [Admin]                        Strands FIS |
+------------------------------------------------------------------+
| [=]      |                                                        |
| Sidebar  |            Main Content Area                           |
| (250px)  |         (activeTab에 따라 변경)                         |
|          |                                                        |
| 대화이력  |                                                        |
| ------   |                                                        |
| 예시쿼리  |                                                        |
|          |                                                        |
+----------+--------------------------------------------------------+
```

## 2. Chat 탭 - 2분할 레이아웃

```
+--------------------------------+------------------------+
| Chat Area (~55%)               | Agent Process (~45%)   |
|                                |                        |
| [User] AUM 상위 ETF는?         | Intent Detection       |
|                                |  ETF (0.95) 0.3s      |
| [Assistant]                    |  120 tok  $0.0004     |
| AUM 상위 5개 TIGER ETF입니다:   |                        |
|                                | Tool Selection          |
| +--ECharts Bar Chart---------+ |  text2sql 0.2s        |
| |  TIGER S&P500  ████ 5.2조   | |  85 tok  $0.0003     |
| |  TIGER MSCI    ███  3.1조   | |                        |
| +----------------------------+ | Query Generated         |
|                                |  SQL 0.4s              |
| | name_ko    | aum      |     |  SELECT name_ko, aum.. |
| |------------|----------|     |                        |
| | S&P500 ETF | 5,200억  |     | Query Executed          |
| | MSCI ETF   | 3,100억  |     |  5건 0.05s             |
|                                |                        |
| +----------------------------+ | [OpenCypher][Search]   |
| | [메시지 입력]        [전송] | | [GraphRAG][SQL][결과]  |
| +----------------------------+ | +--------------------+ |
|                                | | SELECT name_ko,    | |
|                                | |   aum FROM         | |
|                                | |   tiger_etf...     | |
|                                | +--------------------+ |
|                                |                        |
|                                | Total: 1.2s $0.0015   |
+--------------------------------+------------------------+
```

### 2.1 Chat Area 로직

1. **메시지 입력 → 전송**
   - Enter 또는 전송 버튼 클릭
   - 사용자 메시지를 ChatMessage로 추가 (role: "user")
   - WebSocket으로 `{ session_id, message }` 전송
   - isStreaming = true

2. **WebSocket 이벤트 수신 처리**
   ```
   intent_detected → currentAgentProcess.intent_detection 업데이트
   tool_selected   → currentAgentProcess.tool_selection 업데이트
   query_generated → currentAgentProcess.query_generation 업데이트
   query_executed  → currentAgentProcess.query_execution 업데이트
                     → raw_data 저장, chart_data/graph_data 저장
   text_chunk      → assistant 메시지에 텍스트 append (실시간)
   response_complete → isStreaming = false, total 업데이트
   session_info    → currentSessionId 업데이트
   ```

3. **응답 렌더링**
   - 마크다운 렌더링 (react-markdown + remark-gfm)
   - 코드 블록 하이라이팅 (react-syntax-highlighter)
   - 숫자 천단위 구분자 자동 적용
   - chart_data 있으면 → ECharts 차트 렌더링
   - raw_data가 배열이면 → 데이터 테이블 렌더링

### 2.2 Agent Process Panel 로직

1. **단계별 표시** (위→아래 순서)
   - Intent Detection: intent 뱃지 + confidence + 시간/토큰/비용
   - Tool Selection: tool명 뱃지 + rationale + 시간/토큰/비용
   - Query Generated: query_type + 시간/토큰/비용
   - Query Executed: result_summary + 시간
   - Response Generation: 시간/토큰/비용
   - Total: 총합

2. **상세 탭 (DetailTabs)**
   - 선택된 Tool에 따라 활성 탭 자동 결정
   - **SQL 탭**: 생성된 SQL + 실행 결과 테이블
   - **OpenCypher 탭**: Cypher 쿼리 + 그래프 미니뷰
   - **OpenSearch 탭**: 검색 쿼리 + 결과 청크 목록
   - **GraphRAG 탭**: 실행 단계 + 결과
   - **결과 탭**: raw_data 전체 JSON 뷰

## 3. Graph Network 탭

```
+------------------------------------------------------------------+
| [ETF] [채권] [펀드]                             [필터] [검색]      |
|                                                                    |
|       O --- TIGER S&P500 ETF                                       |
|      /|\                                                           |
|     / | \                                                          |
|    O  O  O  --- S&P500 인덱스                                       |
|   환율 보유  미래에셋                                                |
|   위험 종목  자산운용                                                |
|                                                                    |
|  [확대] [축소] [전체보기] [노드 검색]                                 |
+------------------------------------------------------------------+
```

### 3.1 로직

1. **테넌트 서브탭**: ETF/Bond/Fund 클릭 시 해당 그래프 로드
2. **초기 로드**: 각 테넌트의 OpenCypher로 초기 그래프 요청
   - API: GET /api/visualize/graph/{session_id}/{turn_id} (대화에서 생성된 그래프)
   - 또는 직접 쿼리 수행 (POST /api/chat + graph intent)
3. **Cytoscape.js 렌더링**:
   - 노드: type별 색상 구분 (ETF=파랑, Index=초록, Holding=주황, Risk=빨강)
   - 엣지: label 표시
   - 레이아웃: cose-bilkent (force-directed)
4. **인터랙션**:
   - 노드 클릭 → properties 패널 표시
   - 노드 더블클릭 → 확장 (2홉 쿼리)
   - 줌/팬 컨트롤
   - 노드 검색 (이름 필터)
   - 관계 타입 필터

## 4. Admin 탭

```
+------------------------------------------------------------------+
| 토큰 사용량                              기간: [일별 v] [검색]      |
|                                                                    |
| +----ECharts Line Chart-------------------------------------+     |
| | tokens_in / tokens_out / cost  트렌드                       |     |
| +------------------------------------------------------------+     |
|                                                                    |
| 총합: 입력 12,345 tok | 출력 5,678 tok | 비용 $0.1234 | 42 요청   |
|                                                                    |
| 대화 이력 관리                                                      |
| +------------------------------------------------------------+     |
| | 제목            | 턴수 | 최근 Intent | 시간      | 삭제    |     |
| |-----------------|------|-------------|-----------|---------|     |
| | AUM 상위 ETF는? |   3  | ETF         | 3시간 전  | [삭제]  |     |
| | AAA 채권 목록   |   1  | Bond        | 어제      | [삭제]  |     |
| +------------------------------------------------------------+     |
+------------------------------------------------------------------+
```

### 4.1 로직

1. **토큰 통계**: GET /api/admin/token-usage?period=daily
   - 기간 선택 (daily/weekly/monthly)
   - ECharts line chart로 트렌드 표시
   - tokens_in, tokens_out, cost 3축
   - 하단에 totals 표시

2. **대화 관리**: GET /api/admin/conversations
   - 테이블로 대화 목록 표시
   - 삭제 버튼 → DELETE /api/conversations/{id} (확인 다이얼로그)

## 5. Sidebar (코글 사이드바)

### 5.1 구성

```
+----------+
| [=] 접기  |
|          |
| 대화 이력 |
| > AUM..  |
| > AAA..  |
| > 펀드.. |
|          |
| -------- |
|          |
| 예시 쿼리 |
| [ETF]    |
|  > AUM.. |
|  > 반도체 |
| [채권]   |
|  > AAA.. |
| [펀드]   |
|  > 수익률 |
|          |
| [새 대화] |
+----------+
```

### 5.2 로직

1. **대화 이력**: GET /api/conversations → 목록 표시
   - 클릭 → 해당 세션 로드 → 채팅 영역에 이전 대화 표시
   - 현재 세션 하이라이트
2. **예시 쿼리**: GET /api/examples → 도메인별 아코디언
   - 클릭 → 자동으로 메시지 입력 + 전송
3. **새 대화**: session_id = null로 초기화
4. **접기/펼치기**: sidebarOpen 토글

## 6. WebSocket 연결 관리 (useWebSocket Hook)

```
1. 컴포넌트 마운트 → WebSocket 연결 (ws://host/ws/chat)
2. 연결 성공 → readyState 업데이트
3. 메시지 전송: ws.send(JSON.stringify({ session_id, message }))
4. 이벤트 수신: onmessage → JSON.parse → 이벤트 타입별 핸들러 호출
5. 연결 끊김 → 3초 후 자동 재연결 (최대 5회)
6. 컴포넌트 언마운트 → WebSocket 정리
```

## 7. REST API 호출 (useApi Hook)

| API | 용도 | 호출 시점 |
|-----|------|----------|
| GET /api/conversations | 대화 목록 | 앱 시작, 새 대화 후 |
| GET /api/conversations/{id} | 대화 로드 | 사이드바 클릭 |
| DELETE /api/conversations/{id} | 대화 삭제 | Admin 삭제 버튼 |
| GET /api/examples | 예시 쿼리 | 앱 시작 |
| GET /api/admin/token-usage | 토큰 통계 | Admin 탭 진입 |
| GET /api/admin/conversations | Admin 대화 | Admin 탭 진입 |
| GET /api/health | 헬스체크 | 앱 시작 |

## 8. Nginx 설정

```
server {
    listen 80;

    # Basic Auth
    auth_basic "Strands FIS";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # React SPA
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API 프록시
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket 프록시
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```
