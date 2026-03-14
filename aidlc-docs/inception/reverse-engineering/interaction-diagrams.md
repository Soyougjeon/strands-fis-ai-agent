# Interaction Diagrams

## Business Transaction 1: ETF Data Collection (scrape all)

```mermaid
sequenceDiagram
    actor User
    participant CLI as tiger CLI
    participant PLS as ProductListScraper
    participant PDS as ProductDetailScraper
    participant HS as HoldingsScraper
    participant PS as PerformanceScraper
    participant DS as DistributionScraper
    participant DCS as DocumentsScraper
    participant WEB as Mirae Asset Website
    participant PG as Aurora PostgreSQL

    User->>CLI: tiger scrape all --limit N

    Note over CLI,PG: Step 1 - Product List
    CLI->>PLS: scrape()
    PLS->>WEB: GET /getEtfTypeDataAll.ajax
    WEB-->>PLS: Category tree (JSON)
    loop Each category
        PLS->>WEB: POST /getEtfTypeData.ajax
        WEB-->>PLS: Products (JSON)
    end
    PLS->>PG: UPSERT etf_products (221 rows)

    Note over CLI,PG: Step 2 - Product Details
    CLI->>PDS: scrape(limit=N)
    loop Each product
        PDS->>WEB: GET /ko/.../index.do?ksdFund=...
        WEB-->>PDS: Detail page (HTML)
        PDS->>PG: UPDATE etf_products (enrich)
    end

    Note over CLI,PG: Step 3 - Performance
    CLI->>PS: scrape(limit=N)
    PS->>PG: SELECT raw_data FROM etf_products
    PS->>PG: UPSERT etf_performance

    Note over CLI,PG: Step 4 - Holdings
    CLI->>HS: scrape(limit=N)
    HS->>WEB: POST /downloadPdfExcelTotal.do
    WEB-->>HS: AllPDF.xls (Excel)
    HS->>PG: UPSERT etf_holdings

    Note over CLI,PG: Step 5 - Distributions
    CLI->>DS: scrape(limit=N)
    loop Each product
        DS->>WEB: POST /refDivAjax.ajax
        WEB-->>DS: Distribution table (HTML)
        DS->>PG: UPSERT etf_distributions
    end

    Note over CLI,PG: Step 6 - Documents
    CLI->>DCS: scrape(limit=N)
    loop Each product
        DCS->>WEB: GET /ko/.../index.do
        WEB-->>DCS: Detail page with PDF links
        DCS->>WEB: GET {pdf_url}
        WEB-->>DCS: PDF file
        DCS->>PG: UPSERT etf_documents
    end
```

### Text Alternative
```
1. User -> CLI: scrape all
2. ProductListScraper -> Website: GET categories + products -> PG: UPSERT etf_products
3. ProductDetailScraper -> Website: GET detail pages -> PG: UPDATE etf_products
4. PerformanceScraper -> PG: SELECT raw_data -> PG: UPSERT etf_performance
5. HoldingsScraper -> Website: POST download Excel -> PG: UPSERT etf_holdings
6. DistributionScraper -> Website: POST distribution history -> PG: UPSERT etf_distributions
7. DocumentsScraper -> Website: GET PDFs -> PG: UPSERT etf_documents
```

## Business Transaction 2: Knowledge Graph Indexing (graphrag build)

```mermaid
sequenceDiagram
    actor User
    participant CLI as tiger CLI
    participant Loader
    participant PG as Aurora PostgreSQL
    participant PDF as Local PDFs
    participant Splitter as SentenceSplitter
    participant LLM as Bedrock Claude
    participant Embed as Titan Embed v2
    participant Neptune
    participant OpenSearch

    User->>CLI: tiger graphrag build

    Note over CLI,PDF: Document Loading
    CLI->>Loader: load_pdfs() + load_rdb()
    Loader->>PDF: Read *.pdf (PyMuPDFReader)
    PDF-->>Loader: PDF Documents
    Loader->>PG: SELECT products + holdings + distributions + performance
    PG-->>Loader: Structured data
    Loader-->>CLI: LlamaIndex Documents (PDF + RDB)

    Note over CLI,OpenSearch: Indexing Pipeline
    CLI->>Splitter: split(documents, chunk=256, overlap=25)
    Splitter-->>CLI: Chunks

    loop Each chunk batch
        CLI->>LLM: Extract propositions
        LLM-->>CLI: Atomic propositions
        CLI->>LLM: Extract topics + entities + relationships (ETF ontology)
        LLM-->>CLI: Structured extraction
        CLI->>Neptune: Store nodes + edges (OpenCypher)
        CLI->>Embed: Generate embeddings (1024-dim)
        Embed-->>CLI: Vectors
        CLI->>OpenSearch: Store chunk + embedding
    end
```

### Text Alternative
```
1. User -> CLI: graphrag build
2. Loader reads PDFs (PyMuPDFReader) + queries RDB (products, holdings, etc.)
3. SentenceSplitter: 256 char chunks with 25 overlap
4. For each chunk:
   a. Bedrock Claude: proposition extraction
   b. Bedrock Claude: topic/entity/relationship extraction (ETF ontology)
   c. Neptune: store graph nodes and edges
   d. Titan Embed v2: generate 1024-dim embeddings
   e. OpenSearch: store chunks with embeddings
```

## Business Transaction 3: Natural Language Query (graphrag query)

```mermaid
sequenceDiagram
    actor User
    participant CLI as tiger CLI
    participant QE as QueryEngine
    participant Embed as Titan Embed v2
    participant OS as OpenSearch
    participant Neptune
    participant LLM as Bedrock Claude

    User->>CLI: tiger graphrag query "TIGER S&P500 ETF 보유종목은?"
    CLI->>QE: query(question)

    Note over QE,OS: Vector Search
    QE->>Embed: embed(question)
    Embed-->>QE: query_vector [1024-dim]
    QE->>OS: similarity_search(query_vector, top_k)
    OS-->>QE: Relevant chunks + metadata

    Note over QE,Neptune: Graph Traversal
    QE->>Neptune: Identify entities from chunks
    Neptune-->>QE: Entity nodes
    QE->>Neptune: Expand relationships (1-2 hops)
    Neptune-->>QE: Related nodes + edges

    Note over QE,LLM: Response Generation
    QE->>LLM: Generate response (question + context)
    LLM-->>QE: Natural language answer
    QE-->>User: "TIGER 미국S&P500 ETF의 주요 보유종목은 Apple (5.2%), Microsoft (4.8%)..."
```

### Text Alternative
```
1. User -> CLI: graphrag query "question"
2. Embed question with Titan v2 -> 1024-dim vector
3. OpenSearch: similarity search -> top-k relevant chunks
4. Neptune: identify entities from chunks -> expand 1-2 hops
5. Bedrock Claude: generate response from (question + vector chunks + graph context)
6. Return natural language answer to user
```

## Business Transaction 4: Experiment & Evaluation (experiment run)

```mermaid
sequenceDiagram
    actor User
    participant CLI as tiger CLI
    participant EXP as Experiment
    participant IDX as Indexer
    participant QE as QueryEngine
    participant EVAL as Evaluator
    participant LLM as Bedrock Claude

    User->>CLI: tiger experiment run baseline_claude37_cohere
    CLI->>EXP: run(config_name)
    EXP->>EXP: Load config YAML
    EXP->>IDX: Reset + Build (with config overrides)
    IDX-->>EXP: Indexing complete

    EXP->>QE: get_graph_stats()
    QE-->>EXP: Node/edge counts

    loop Each eval question (40+)
        EXP->>QE: query(question)
        QE-->>EXP: response
        EXP->>EVAL: compute_keyword_hit(response, expected_keywords)
        EVAL-->>EXP: hit_rate
        EXP->>LLM: LLM-as-Judge (correctness, faithfulness, completeness)
        LLM-->>EXP: scores (1-5)
    end

    EXP->>EXP: Aggregate metrics by category
    EXP->>EXP: Save results JSON
    EXP-->>User: Evaluation report
```

### Text Alternative
```
1. User -> CLI: experiment run {config_name}
2. Load YAML config, override GraphRAG settings (LLM, embedding, workers)
3. Reset stores + build index
4. Collect graph statistics
5. For each eval question:
   a. Execute query -> response
   b. Compute keyword hit rate
   c. LLM-as-Judge scoring (correctness, faithfulness, completeness)
6. Aggregate by category, save results JSON
7. Display evaluation report
```
