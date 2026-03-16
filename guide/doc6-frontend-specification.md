# Doc 6: Frontend Specification

## 1. 화면 구성

### 1.1 전체 레이아웃

```
+------------------------------------------------------------------+
| [Chat] [Graph Network] [Admin]                        Strands FIS |
+------------------------------------------------------------------+
| [=]      |                                                        |
| Sidebar  |            Main Content Area                           |
| (250px)  |         (activeTab에 따라 변경)                         |
+----------+--------------------------------------------------------+
```

### 1.2 Chat 탭 (2분할)

```
+--------------------------------+------------------------+
| Chat Area (~55%)               | Agent Process (~45%)   |
|                                |                        |
| [User] 질문 메시지              | Intent Detection       |
| [Assistant] 마크다운 응답       |  ETF (0.95) 0.3s      |
|   + ECharts 차트               | Tool Selection          |
|   + 데이터 테이블               |  text2sql 0.2s        |
|                                | Query Generated         |
| [메시지 입력]          [전송]   | Query Executed          |
|                                | [SQL][Search][GraphRAG] |
|                                |  [OpenCypher][결과]     |
|                                | Total: 1.2s $0.0015   |
+--------------------------------+------------------------+
```

### 1.3 Graph Network 탭

```
+------------------------------------------------------------------+
| [ETF] [채권] [펀드]                             [필터] [검색]      |
|                                                                    |
|       Cytoscape.js 그래프 네트워크                                  |
|       (노드: type별 색상, 엣지: 관계 라벨)                          |
|       (레이아웃: cose-bilkent)                                     |
|                                                                    |
|  [확대] [축소] [전체보기] [노드 검색]                                 |
+------------------------------------------------------------------+
```

### 1.4 Admin 탭

```
+------------------------------------------------------------------+
| 토큰 사용량 (ECharts Line Chart)                                   |
| tokens_in / tokens_out / cost 트렌드                               |
| 총합: 입력 12,345 tok | 출력 5,678 tok | 비용 $0.1234             |
|                                                                    |
| 대화 이력 관리 (테이블)                                              |
| 제목 | 턴수 | Intent | 시간 | [삭제]                                |
+------------------------------------------------------------------+
```

### 1.5 Sidebar (코글)

```
+----------+
| [=] 접기  |
| 대화 이력 |  ← GET /api/conversations
| > 대화1  |
| > 대화2  |
| -------- |
| 예시 쿼리 |  ← GET /api/examples
| [ETF]    |
| [채권]   |
| [펀드]   |
| [새 대화] |
+----------+
```

## 2. 컴포넌트 트리

```
App.tsx
├── Sidebar.tsx                    # 접기/펼치기 사이드바
├── ChatPanel.tsx                  # 대화 메시지 + 입력
│   ├── MarkdownRenderer.tsx       # 마크다운 렌더링
│   ├── DynamicChart.tsx           # ECharts 차트
│   └── DataTable.tsx              # 데이터 테이블
├── AgentProcessPanel.tsx          # Agent 실행 과정
│   └── DetailTabs.tsx             # 상세 탭 (SQL/Search/GraphRAG/Cypher/결과)
├── GraphNetworkPage.tsx           # 테넌트별 서브탭
│   └── GraphNetwork.tsx           # Cytoscape.js 그래프
└── AdminDashboard.tsx             # 토큰/대화 관리
```

## 3. TypeScript 타입 (핵심)

```typescript
// WebSocket 이벤트
type EventType = "intent_detected" | "tool_selected" | "query_generated"
  | "query_executed" | "text_chunk" | "response_complete" | "session_info" | "error";

interface AgentEvent { type: EventType; data: Record<string, unknown>; timestamp: string; }

// 시각화
interface GraphData { nodes: GraphNode[]; edges: GraphEdge[]; }
interface GraphNode { id: string; label: string; type: string; properties: Record<string, unknown>; }
interface GraphEdge { source: string; target: string; label: string; }
interface ChartData { chart_type: "bar"|"line"|"pie"; title: string; data: Record<string,unknown>[]; x_axis: string; y_axis: string; }

// 대화
interface ChatMessage { id: string; role: "user"|"assistant"; content: string;
  agentProcess?: AgentProcess; chartData?: ChartData; graphData?: GraphData; rawData?: unknown; }

// Agent Process
interface AgentProcess {
  intent_detection: StepMetrics | null;
  tool_selection: StepMetrics | null;
  query_generation: QueryStepMetrics | null;
  query_execution: ExecutionResult | null;
  response_generation: StepMetrics | null;
}
interface StepMetrics { latency: number; tokens_in: number; tokens_out: number; cost: number; }
```

전체 타입 정의: `frontend/src/types/index.ts` 참조

## 4. Hooks

### useWebSocket
- 앱 시작 시 `ws://host/ws/chat` 자동 연결
- 끊김 시 3초 후 재연결 (최대 5회)
- `send(session_id, message)` / `onMessage(handler)`

### useApi
- REST API 호출 래퍼 (fetch 기반)
- `getConversations()`, `getExamples()`, `getTokenUsage(period)`, `deleteConversation(id)`

## 5. Business Rules (핵심)

| 규칙 | 내용 |
|------|------|
| BR-01 | 사용자 메시지 우측/파란, Assistant 좌측/마크다운 |
| BR-02 | text_chunk 즉시 렌더링, 스트리밍 중 전송 비활성화 |
| BR-03 | chart_data 있으면 ECharts 자동 렌더링 (bar/line/pie) |
| BR-04 | 그래프 노드 색상: ETF=파랑, Holding=주황, Index=초록, Risk=빨강 |
| BR-05 | 사이드바 접기/펼치기 (250px ↔ 40px, 300ms 애니메이션) |
| BR-06 | Admin 토큰 통계: daily/weekly/monthly, 3선 차트 |
| BR-07 | WebSocket 재연결 5회 초과 시 "연결 실패" 알림 |
| BR-08 | 최소 지원 너비 1024px (데스크톱만) |
| BR-09 | Nginx Basic Auth, /api /ws 프록시, WebSocket timeout 24h |

## 6. 커스터마이징 포인트

| 항목 | 파일 | 변경 내용 |
|------|------|----------|
| 도메인 서브탭 | `GraphNetworkPage.tsx` | ETF/채권/펀드 → 자신의 도메인 탭 |
| 그래프 노드 색상 | `GraphNetwork.tsx` | type별 색상 매핑 |
| 상세 탭 | `DetailTabs.tsx` | 탭 이름/내용 |
| 예시 쿼리 도메인 | `Sidebar.tsx` | 아코디언 그룹명 |
| 앱 타이틀 | `App.tsx` | "Strands FIS" → 자신의 앱명 |
| Basic Auth 계정 | `Dockerfile.frontend` | htpasswd 명령 |
