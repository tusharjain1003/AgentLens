# Contributing to WebLens

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account (PostgreSQL + pgvector), or Docker Compose for local Postgres
- API keys: DeepSeek (or OpenAI), Tavily

### Local Dev Setup

```bash
git clone https://github.com/tusharjain1003/AgentLens.git
cd AgentLens
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in your API keys
```

### One-Command Dev with Docker

```bash
docker compose up --build
# Then initialize DB once:
docker compose exec backend python db/setup.py
```

Backend at `http://localhost:8765`, frontend at `http://localhost:5174`, Postgres at `localhost:5432`.

### Manual Backend

```bash
uvicorn app:app --reload --port 8000
```

### Manual Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
pipeline/         RAG pipeline — one file per stage (graph, retrieve, generate, …)
  graph.py        LangGraph StateGraph: nodes, edges, orchestration
  runtime.py      SSE queue + timing via contextvars
  retrieve.py     BM25 → dense → RRF → cross-encoder rerank
  generate.py     Streaming LLM + synthesis + citation alignment
  …
llm/              Vendor-agnostic LLM protocol (base.py) + providers
db/               PostgreSQL access layer (asyncpg), schema.sql, sessions
frontend/         React 18 + Vite + TypeScript SPA
  src/state/      Zustand store (chatStore.ts — SSE handlers + rehydrate)
  src/components/ UI components
evals/            Evaluation harness, benchmark questions, results
docs/             Architecture, deployment, implementation summaries
```

See `docs/DIRECTORY-STRUCTURE.md` for a full file-by-file map.

---

## Development Workflow

### 1. Pick an Issue

Check the roadmap in `implementation_plan.md` for planned work. Current phases:

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | Foundation (tests, CI/CD, Docker) | Complete |
| 2 | Agentic (reflection, verification, tool routing) | Complete |
| 3 | Hardening (prompt-injection, auth, credibility, feedback) | Complete |
| 4 | Stretch (memory, docs) | In progress |

### 2. Make Changes

- Follow existing code style (type hints, no comments, async where possible)
- All pipeline modules are pure — they take inputs, return outputs, never write to SSE directly
- SSE emission flows through `RuntimeContext.emit()` in `pipeline/runtime.py`
- DB writes in `db/` are fire-and-forget: log on failure, never raise

### 3. Test

```bash
# Unit tests
python -m pytest tests/ -q

# Run a specific test file
python -m pytest tests/test_retrieve.py -v

# Eval smoke test (requires live API keys + DB)
python evals/run_eval.py --smoke
```

### 4. Lint

```bash
pip install ruff
python -m ruff check pipeline/ db/ app.py config.py
```

Pre-existing E402 errors in `app.py` (from `load_dotenv()`) are allowed. Do not introduce new warnings.

### 5. Commit

```bash
git commit -m "Phase N.N: Short description of what changed"
```

Keep commits scoped to one logical change. Use the `Phase N.N:` prefix matching the plan.

---

## Pipeline Architecture Notes

- **Every query passes through an LLM.** No heuristic routing — the `analyze` node classifies each query.
- **Streaming must start in under 3 seconds.** First SSE events fire ~500ms in.
- **Retrieval is global, not per-sub-query.** Extraction runs once on the deduplicated URL union.
- **Citation numbers are globally assigned** and preserved through synthesis.
- **Validation is warn + repair**, not block — invalid `[N]` citations are stripped; instruction-hijacked answers are replaced with a block message.

### Adding a New Pipeline Node

1. Create the stage function in the appropriate `pipeline/` module
2. Add the node to the `StateGraph` in `graph.py`
3. Wire conditional routing edges
4. Add a `@traceable` wrapper for LangSmith observability
5. Add failure modes + fallbacks per the pattern in `implementation_plan.md#failure-modes--fallbacks`
6. Write a unit test in `tests/`
7. Update `docs/DIRECTORY-STRUCTURE.md` if adding a new file

---

## Using LangSmith

Tracing is off by default. Enable per-request via header:

```bash
curl -H "X-Langsmith-Trace: true" ...
```

Or for eval runs: `python evals/run_eval.py --full --trace on`

Each LangGraph node emits typed spans (`llm`, `retriever`, `tool`, `chain`). Check the LangSmith project dashboard after tracing runs.

---

## Deployment

See `docs/DEPLOYMENT.md` for Railway setup.

---

## Feedback

- Report bugs via GitHub Issues
- Human feedback collected in-app: thumbs up/down on answers, citation-level reports
