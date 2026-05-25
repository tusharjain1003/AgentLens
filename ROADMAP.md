# AgentLens Roadmap

## Completed

### Phase 1 — Foundation
- Fix docs, fork repo, rename
- Docker multi-stage build + docker-compose (Postgres + pgvector)
- Unit tests (18 tests across 6 modules)
- CI/CD: lint + test, eval smoke, Railway deploy
- TokenTracker wiring for LLM cost attribution

### Phase 2 — Agentic
- Adaptive tool selection (calculator, academic search, web search)
- Reflection node: post-retrieval coverage check with gap re-decomposition
- Claim verifier: flag mode and quality (regenerate) mode
- Expanded eval dataset (52 questions, 15 categories)

### Phase 3 — Production Hardening
- Prompt-injection protection (Unicode normalization, structured delimiters, output validation)
- API authentication (opt-in `X-API-Key`) + rate limiting
- Source credibility ranking (domain tiers, recency bonus)
- Human feedback loop (thumbs up/down, citation reports)

### Phase 4 — Docs & Polish
- CONTRIBUTING.md with architecture principles and dev workflow
- Comprehensive README with architecture diagrams and eval results
- Name consistency and repo presentation

## Planned

### Phase 5 — Stretch
- Long-term memory system (incremental summarization, topic eviction)
- Cross-encoder upgrade (BGE-reranker-v2-m3 for ~5–8% precision improvement)
- Streaming synthesis while sub-answers are still generating
- LLM cost dashboard via TokenTracker

### Phase 6 — Scale
- Multi-instance deployment with Redis-backed state
- Websocket-based real-time updates (replace SSE polling)
- Feedback-driven fine-tuning pipeline
