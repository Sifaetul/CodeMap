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

## Phase 3: AI Intelligence (Real Vector RAG & Streaming) [PENDING USER REVIEW]
- [ ] 3.1 Real RAG pipeline using embeddings and provider
- [ ] 3.2 Chat session and message persistence in PostgreSQL
- [ ] 3.3 Streaming responses for chat

## Phase 4: UI/UX & Frontend Polish [PENDING]
- [ ] 4.1 Unify design system & theme across dashboard and graph
- [ ] 4.2 React Flow performance optimization (LOD, style cleanup)
- [ ] 4.3 Rich code viewer with syntax highlighting in node details panel
