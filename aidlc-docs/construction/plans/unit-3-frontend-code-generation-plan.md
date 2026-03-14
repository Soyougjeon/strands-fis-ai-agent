# Code Generation Plan - Unit 3: Frontend

## Unit Context
- **Unit**: Unit 3 - Frontend (React + TypeScript SPA + Nginx)
- **Code Location**: `frontend/`, `nginx/` (workspace root)
- **Requirements**: FR-02, FR-03 (UI부분) + NFR-05
- **Dependencies**: Unit 2 (Backend API)

## Generation Steps

### Project Setup
- [x] Step 1: `frontend/` 프로젝트 초기화 (package.json, vite.config.ts, tsconfig.json, index.html)
- [x] Step 2: `frontend/src/types/index.ts` - TypeScript 타입 정의

### Hooks
- [x] Step 3: `frontend/src/hooks/useWebSocket.ts` - WebSocket 연결 관리
- [x] Step 4: `frontend/src/hooks/useApi.ts` - REST API 호출

### Common Components
- [x] Step 5: `frontend/src/components/common/MarkdownRenderer.tsx` - 마크다운 렌더링
- [x] Step 6: `frontend/src/components/common/DataTable.tsx` - 데이터 테이블

### Chat Components
- [x] Step 7: `frontend/src/components/chat/ChatPanel.tsx` - 대화 메시지 + 입력
- [x] Step 8: `frontend/src/components/chat/AgentProcessPanel.tsx` - Agent 실행 과정
- [x] Step 9: `frontend/src/components/chat/DetailTabs.tsx` - 상세 탭 (SQL/Search/GraphRAG/Cypher/결과)

### Visualization Components
- [x] Step 10: `frontend/src/components/visualization/DynamicChart.tsx` - ECharts 차트
- [x] Step 11: `frontend/src/components/visualization/GraphNetwork.tsx` - Cytoscape.js 그래프
- [x] Step 12: `frontend/src/components/visualization/GraphNetworkPage.tsx` - 테넌트별 서브탭

### Sidebar & Admin
- [x] Step 13: `frontend/src/components/sidebar/Sidebar.tsx` - 코글 사이드바
- [x] Step 14: `frontend/src/components/admin/AdminDashboard.tsx` - Admin 대시보드

### App Shell
- [x] Step 15: `frontend/src/App.tsx` - 탭 네비게이션 + 레이아웃
- [x] Step 16: `frontend/src/main.tsx` + `frontend/src/index.css` - 엔트리 + Tailwind

### Nginx
- [x] Step 17: `nginx/nginx.conf` + `nginx/conf.d/default.conf` + `nginx/.htpasswd`

## Story Traceability
| Step | Requirements |
|------|-------------|
| Step 3 | FR-02-02 (스트리밍), FR-03-03 (WebSocket) |
| Step 5,7 | FR-02-01, FR-02-07 (마크다운, Chat UI) |
| Step 8,9 | FR-02-08, FR-02-09 (Agent Process, 상세 탭) |
| Step 10 | FR-02-03 (차트 시각화) |
| Step 11,12 | FR-02-04 (그래프 시각화) |
| Step 13 | FR-02-06 (사이드바) |
| Step 14 | FR-03-08~10 (Admin) |
