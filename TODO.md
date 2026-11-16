# CodeAtlas Upgrade Roadmap & State Tracking

## Phase 1: Critical Stability & Core Bug Fixes [COMPLETED]
- [x] 1.1 Non-blocking background task ingestion in `apps/api/routes/repositories.py` (Removed `task.get(timeout=30)`)
- [x] 1.2 Qualified entity resolution in `apps/analyzer/pipeline.py` (Prevent cross-file function collisions)
- [x] 1.3 Fix `/entities/{entity_id}` endpoint in `apps/api/routes/graph.py` to handle `file-*` and `folder-*` IDs without 422 crash
- [x] 1.4 Persist module imports to `Dependency` table in `apps/analyzer/pipeline.py`
- [x] 1.5 Add workspace path traversal security checks in `get_entity_details`
- [x] 1.6 Verification & Cross-check: 12/12 Unit/Integration tests passing (FastAPI + Analyzer pipeline + SQLite/Postgres compatibility)
- [x] 1.7 Frontend TypeScript typecheck 100% clean (`tsc --noEmit` exit code 0)

## Phase 2: Engine Expansion (Polyglot AST & Deep Graph Algorithms) [COMPLETED]
- [x] 2.1 Multi-language AST parsing (Python + TypeScript/JavaScript Parser & Registry)
- [x] 2.2 Deep graph metrics: Dead code / Orphan node detection, PageRank centrality, Afferent/Efferent coupling ($C_a, C_e, I$)
- [x] 2.3 Expose findings API (`GET /api/analysis/projects/{project_id}/findings`) & annotate graph nodes with PageRank + Coupling
- [x] 2.4 Verification & Cross-check: 20/20 Unit/Integration tests passing in Docker test runner
- [x] 2.5 Frontend TypeScript compilation verified 100% clean

## Phase 3: AI Intelligence (Real Vector RAG & Streaming) [COMPLETED]
- [x] 3.1 Real RAG Context Retriever & Prompt Builder (`packages/shared/ai/retriever.py`)
- [x] 3.2 Ollama LLM provider with token-by-token streaming & intelligent AST fallback (`packages/shared/ai/provider.py`)
- [x] 3.3 Chat persistence: Sessions and Messages saved to PostgreSQL (`ChatSession` & `ChatMessage`)
- [x] 3.4 Streaming endpoint (`POST /chat/stream`) with Server-Sent Events (SSE)
- [x] 3.5 Conversation history endpoints (`GET/DELETE /chat/messages`) & frontend auto-restore on mount
- [x] 3.6 Verification & Cross-check: 23/23 Unit/Integration tests passing (100% Pass Rate)

## Phase 4: UI/UX & Frontend Polish [COMPLETED]
- [x] 4.1 Unified Modern Dark Slate Design System across landing, auth (login, register), projects dashboard, new project, repository ingestion, and architecture visualizer
- [x] 4.2 React Flow 60fps Optimization: Memoized node rendering, PageRank badges ("Core"), Instability badges ("Unstable"), smooth Bezier curves, and type-based filtering (All, Module, Class, Function, File)
- [x] 4.3 Interactive Layout Controls: Directional Dagre layout toggle (Top-to-Bottom `TB` vs Left-to-Right `LR`) and fit view shortcuts
- [x] 4.4 Architecture Findings & Code Viewer Panel: Tabbed inspector with Node Details (AST code snippet, metrics, dependencies) and "Smells & Findings" tab displaying real-time circular dependencies, dead code, and god components
- [x] 4.5 Verification & Cross-check: Next.js production build (`npm run build`) 100% clean (9/9 routes compiled), all 23 backend & analyzer pytest suites passing in Docker

## Phase 5: Security, Leak Prevention & Stability Engine [COMPLETED]
- [x] 5.1 Bulletproof Path Traversal Protection (`os.path.commonpath`) in `zip.py` and `graph.py` against prefix and parent traversal attacks
- [x] 5.2 Disk Storage Leak Prevention: Workspace directory cleanup (`cleanup_workspace`) on project deletion and on ingestion failures
- [x] 5.3 Celery Worker Transaction Rollback Guard: Added `db.rollback()` in exception handler preventing `PendingRollbackError` and job deadlocks
- [x] 5.4 Asynchronous Worker Remote Git Clone: Delegated remote cloning to Celery worker, eliminating blocking I/O in FastAPI HTTP thread
- [x] 5.5 Database Connection Pool Hardening: Enabled `pool_pre_ping=True`, `pool_recycle=1800`, and sensible pool dimensions in `packages/shared/database.py`
- [x] 5.6 Verification & Cross-check: 25/25 Pytest unit and security tests passing in Docker

## Phase 6: High-Scale Engine & Algorithmic Optimization [COMPLETED]
- [x] 6.1 In-Memory Graph Dedup & Bulk SQL Insertion in `apps/analyzer/pipeline.py`: Eliminated N+1 SQL queries during parsing & call resolution
- [x] 6.2 SQL-Indexed Full-Text RAG Retrieval in `packages/shared/ai/retriever.py`: Replaced $O(N)$ full-table memory scans with targeted SQL queries
- [x] 6.3 Graph Caching Layer: Added sub-millisecond in-memory graph cache in `apps/api/routes/graph.py`
- [x] 6.4 Live Frontend SSE Token Streaming in `apps/web`: Connected `ReadableStream` SSE reader for real-time ChatGPT-like typing animation
- [x] 6.5 Interactive Graph Search & Ripple Effect Visualizer: Instant node search bar with highlight ring and "Blast Radius" dependent component tracer
- [x] 6.6 Verification & Cross-check: Next.js production build (`npm run build`) 100% clean (9/9 routes compiled), all 25 backend tests passing in Docker
