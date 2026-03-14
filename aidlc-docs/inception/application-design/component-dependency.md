# Component Dependencies

## Dependency Matrix

| Component | Depends On | Depended By |
|-----------|-----------|-------------|
| C1: Nginx | C2 (proxy target) | External users |
| C2: FastAPI | C3, C5, C6, S6 | C1, C8 |
| C3: Agent Engine | C4a-d, Bedrock | C2 |
| C4a: Text2SQL | Aurora PG, Bedrock | C3 |
| C4b: RAG | OpenSearch, Bedrock (Titan) | C3 |
| C4c: GraphRAG | Neptune, OpenSearch, Bedrock | C3 |
| C4d: OpenCypher | Neptune, Bedrock | C3 |
| C5: Conv Manager | Aurora PG | C2 |
| C6: Token Tracker | Aurora PG | C2, C3 |
| C7: Mock Pipeline | Aurora PG, Neptune, OpenSearch, Bedrock | 없음 (독립 실행) |
| C8: Frontend | C2 (API) | C1 (서빙) |

## Communication Patterns

```
+----------+     HTTP/WS      +----------+
| C8:React | <------------->  | C2:Fast  |
| Frontend |   port 80/Nginx  | API      |
+----------+                  +----------+
                                   |
                    +--------------+--------------+
                    |              |              |
               +----v----+   +----v----+   +----v----+
               | C3:Agent|   | C5:Conv |   | C6:Token|
               | Engine  |   | Manager |   | Tracker |
               +---------+   +---------+   +---------+
                    |              |              |
         +----+----+----+         |              |
         |    |    |    |         |              |
        C4a  C4b  C4c  C4d       |              |
         |    |    |    |         |              |
         v    v    v    v         v              v
     +------+-+--+-+------+  +--------+    +--------+
     |Aurora| |OS | |Nept |  |Aurora  |    |Aurora  |
     |PG    | |   | |une  |  |PG     |    |PG     |
     +------+ +---+ +-----+  +--------+    +--------+
                                (conv)       (tokens)
```

### Communication Protocols

| From | To | Protocol | Pattern |
|------|----|----------|---------|
| C8 -> C2 | HTTP REST | Request/Response | 동기 API 호출 |
| C8 -> C2 | WebSocket | Bidirectional Stream | 실시간 대화 스트리밍 |
| C2 -> C3 | Python async | AsyncGenerator | Agent 이벤트 스트리밍 |
| C3 -> C4* | Python function | Sync/Async call | Tool 실행 |
| C4a -> Aurora PG | TCP/SSL | SQLAlchemy | SQL 쿼리 (port 5432) |
| C4b -> OpenSearch | HTTPS | opensearch-py | kNN 검색 (port 443) |
| C4c -> Neptune | HTTPS | graphrag-toolkit | LexicalGraph 질의 (port 8182) |
| C4c -> OpenSearch | HTTPS | graphrag-toolkit | GraphRAG 벡터 검색 (port 443) |
| C4d -> Neptune | HTTPS | boto3/neptune | OpenCypher 쿼리 (port 8182) |
| C3 -> Bedrock | HTTPS | boto3/strands | LLM 호출 (Claude Sonnet) |
| C4b -> Bedrock | HTTPS | boto3 | 임베딩 생성 (Titan v2) |
| C5 -> Aurora PG | TCP/SSL | SQLAlchemy | 대화 이력 CRUD (port 5432) |
| C6 -> Aurora PG | TCP/SSL | SQLAlchemy | 토큰 사용량 기록 (port 5432) |

## Data Flow

### 1. 대화 요청 흐름

```
User -> C8(React) -> WebSocket -> C2(FastAPI)
  -> C5.get_context(session_id)
  -> C3.process_message(session_id, message)
    -> C3.detect_intent() -> IntentDetectedEvent -> C8
    -> C3.select_tool() -> ToolSelectedEvent -> C8
    -> C4x.execute() -> QueryGeneratedEvent + QueryExecutedEvent -> C8
    -> C3.generate_response() -> TextChunkEvents -> C8
    -> ResponseCompleteEvent -> C8
  -> C5.add_message(message + response + metadata)
  -> C6.record_usage(steps)
```

### 2. Graph Network 조회 흐름

```
User -> C8(React /graph) -> GET /api/visualize/graph?tenant=etf
  -> C2(FastAPI) -> S6.get_graph(tenant)
    -> Neptune: MATCH (n)-[r]->(m) WHERE tenant='etf' RETURN n,r,m
  -> C8: Cytoscape.js 렌더링
```

### 3. Admin 조회 흐름

```
User -> C8(React /admin) -> GET /api/admin/token-usage?period=daily
  -> C2(FastAPI) -> C6.get_usage_stats('daily')
    -> Aurora PG: SELECT SUM(tokens), SUM(cost) GROUP BY date
  -> C8: ECharts 대시보드 렌더링
```

### 4. Mock 데이터 적재 흐름 (독립 실행)

```
CLI -> C7.run_all()
  -> generate_etf_mock() -> data/mock/etf/*.csv
  -> generate_bond_mock() -> data/mock/bond/*.csv
  -> generate_fund_mock() -> data/mock/fund/*.csv
  -> generate_md_files() -> data/mock/graphrag/*.md
  -> load_csv_to_db() -> Aurora PG (INSERT)
  -> index_graphrag() -> Neptune (멀티테넌시) + OpenSearch (graphrag-*)
  -> index_rag() -> OpenSearch (rag-*)
```
