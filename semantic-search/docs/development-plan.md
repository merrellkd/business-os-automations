# Development Plan: Semantic Search System

## Project Structure

```
semantic_search/
├── main.py
├── nodes.py
├── flow.py
├── utils/
│   ├── __init__.py
│   ├── fs_utils.py
│   ├── embedding_utils.py
│   ├── vector_store.py
│   ├── llm_utils.py
│   └── query_utils.py
├── storage/
│   ├── __init__.py
│   ├── faiss_manager.py
│   └── metadata_db.py
├── interfaces/
│   ├── __init__.py
│   ├── cli.py
│   └── api.py
├── config/
│   └── default_config.yaml
├── requirements.txt
├── tests/
│   └── (test files)
└── docs/
    ├── design.md
    └── setup.md
```

## Development Tracks

### Track A: Storage Layer (2-3 days)

**Dependencies**: None - can start immediately

#### A1: Metadata Database (`storage/metadata_db.py`)

```python
# Key functions to implement:
# - init_db(): Create SQLite schema
# - add_file_metadata(): Store file info
# - add_chunk_metadata(): Store chunk boundaries
# - query_by_date_range(): For temporal queries
# - get_chunk_by_id(): Retrieve original text
```

#### A2: FAISS Manager (`storage/faiss_manager.py`)

```python
# Key functions to implement:
# - init_index(): Create FAISS index
# - add_vectors(): Batch add embeddings
# - search(): k-NN search with filtering
# - save_index(): Persist to disk
# - load_index(): Load from disk
```

**Deliverables**:

- Working SQLite schema and CRUD operations
- FAISS index initialization and search
- Unit tests for both storage systems

---

### Track B: File Processing Utilities (2-3 days)

**Dependencies**: None - can start immediately

#### B1: File System Utilities (`utils/fs_utils.py`)

```python
# Key functions to implement:
# - scan_directory(): Walk directory tree
# - get_file_metadata(): Git info, timestamps
# - read_file_content(): Handle multiple formats
# - apply_gitignore(): Filter ignored files
```

#### B2: Text Processing (`utils/query_utils.py`)

```python
# Key functions to implement:
# - chunk_text(): Smart markdown/code chunking
# - classify_query(): Determine query type
# - extract_temporal_markers(): Parse time references
# - build_metadata_filters(): Convert to SQL/FAISS filters
```

**Deliverables**:

- File scanning with git integration
- Smart text chunking that respects document structure
- Query classification logic
- Unit tests with sample files

---

### Track C: LLM Integration (2-3 days)

**Dependencies**: None - can start immediately

#### C1: Embedding Utilities (`utils/embedding_utils.py`)

```python
# Key functions to implement:
# - init_ollama_embeddings(): Setup connection
# - generate_embeddings(): Single/batch embedding
# - validate_model_availability(): Check if model exists
# - fallback_to_cloud(): Handle Ollama failures
```

#### C2: LLM Utilities (`utils/llm_utils.py`)

```python
# Key functions to implement:
# - init_providers(): Setup Ollama/cloud connections
# - call_llm(): Unified interface
# - route_to_provider(): MCP-style routing
# - format_context(): Prepare prompts
# - handle_streaming(): For chat responses
```

**Deliverables**:

- Working Ollama integration for embeddings
- LLM provider abstraction with routing
- Fallback handling for local/cloud
- Integration tests with mock responses

---

### Track D: Core Nodes - Indexing (3-4 days)

**Dependencies**: Tracks A, B, C must be ~50% complete

#### D1: Indexing Nodes (`nodes.py` - partial)

```python
# Nodes to implement:
# - ScanFilesNode
# - FilterRelevantNode
# - ChunkDocumentsNode
# - GenerateEmbeddingsNode
# - UpdateVectorDBNode
# - UpdateMetadataDBNode
```

#### D2: Indexing Flow (`flow.py` - partial)

```python
# Functions to implement:
# - create_indexing_flow()
# - run_full_index()
# - run_incremental_index()
```

**Deliverables**:

- All indexing nodes implemented
- Working indexing flow
- Test with sample business-os structure

---

### Track E: Core Nodes - Query (3-4 days)

**Dependencies**: Tracks A, B, C must be ~50% complete

#### E1: Query Nodes (`nodes.py` - partial)

```python
# Nodes to implement:
# - QueryRouterNode
# - SemanticSearchNode
# - TemporalMapperNode
# - AgentOrchestratorNode
# - LLMProcessorNode
# - OutputFormatterNode
```

#### E2: Query Flow (`flow.py` - partial)

```python
# Functions to implement:
# - create_query_flow()
# - create_simple_search_flow()
# - create_temporal_flow()
# - create_agent_flow()
```

**Deliverables**:

- All query nodes implemented
- Multiple flow variants for different query types
- Integration tests for each flow type

---

### Track F: Interfaces (2-3 days)

**Dependencies**: Tracks D & E must be ~80% complete

#### F1: CLI Interface (`interfaces/cli.py`)

```python
# Commands to implement:
# - index: Run indexing flow
# - search: Interactive search
# - ask: Single query
# - config: Manage settings
```

#### F2: API Interface (`interfaces/api.py`)

```python
# Endpoints to implement:
# - POST /index
# - POST /query
# - GET /status
# - PUT /config
```

**Deliverables**:

- Working CLI with all commands
- Simple HTTP API (Flask/FastAPI)
- Documentation for both interfaces

---

## Integration & Testing Phase (2-3 days)

**Dependencies**: All tracks complete

### Integration Tasks:

1. **main.py**: Entry point tying everything together
2. **End-to-end tests**: Full indexing and query flows
3. **Performance testing**: Measure indexing and query speeds
4. **Documentation**: Update setup.md with real examples

### Final Deliverables:

- Fully integrated system
- Performance benchmarks
- User documentation
- Example queries and outputs

---

## Parallel Development Timeline

```
Week 1:
Day 1-2: Tracks A, B, C start in parallel (3 teams)
Day 3-4: Continue A, B, C + begin D, E planning
Day 5: A, B, C complete, D & E start

Week 2:
Day 6-8: Tracks D & E in parallel
Day 9-10: Track F + Integration begins

Week 3:
Day 11-12: Integration & Testing
Day 13: Documentation & Polish
Day 14: Final testing & delivery
```

## Team Assignments

**Team 1 (Storage)**: Track A

- Focus: Database design, FAISS optimization
- Skills: SQL, vector databases

**Team 2 (Processing)**: Track B

- Focus: File handling, text processing
- Skills: Python file I/O, regex, git integration

**Team 3 (AI/LLM)**: Track C

- Focus: Ollama integration, LLM abstraction
- Skills: API integration, prompt engineering

**Team 4 (Core Logic)**: Tracks D & E

- Focus: PocketFlow nodes, flow orchestration
- Skills: PocketFlow framework, Python async

**Team 5 (Interfaces)**: Track F

- Focus: CLI/API development
- Skills: Click/Typer, FastAPI/Flask

## Critical Path Items

1. **Storage layer** (Track A) blocks both indexing and query flows
2. **Embedding generation** (Track C1) blocks indexing flow
3. **Query classification** (Track B2) blocks query routing

## Risk Mitigation

1. **Ollama availability**: Implement cloud fallback early
2. **Memory constraints**: Test with realistic data volumes early
3. **Integration issues**: Daily sync meetings between tracks
4. **Performance**: Profile and optimize throughout, not just at end

Each track can work independently initially, with integration points clearly defined. Daily standup meetings should focus on unblocking dependencies and ensuring interface compatibility between tracks.
