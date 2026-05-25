# AgentLens — Agentic AI Improvement Plan (Final)

> **Target role:** AI Engineer — Agentic AI focus  
> **Repository:** [weblens-main](file:///Users/tusharjain/Downloads/weblens-main)  
> **Current state:** 12-node LangGraph pipeline, 0.789 aggregate eval score, 0 hard fails

---

## Current Baseline (v9 latest eval: `20260511T161015Z_full`)

| Metric | Score | Status |
|---|---|---|
| Faithfulness | 0.649 | Weakest core metric |
| Context Recall | 0.867 | Strong |
| Context Precision | 0.654 | Open issue |
| Answer Correctness | 0.950 | Strong |
| Routing / Decomposition | 0.825 | Good |
| **Aggregate** | **0.789** | |
| Pass / Partial / Fail | 15 / 15 / 0 | Zero hard fails |
| Avg latency | 38.1s | |
| P95 latency | 73.0s | |

**Graph topology (12 nodes):** `rewrite_query → analyze → {parametric_answer | cache_lookup → {cache_replay | search_urls → extract_pages → chunk_pages → retrieve_and_generate → embedding_cleanup → cache_insert}} → emit_done`

---

## Design Constraints

### Latency Budget

> [!WARNING]
> Baseline avg latency is **38.1s**, P95 is **73s**. New nodes must not make the common case worse.

| Feature | Trigger Condition | Skip Condition | Latency Impact |
|---|---|---|---|
| Reflection | Multi-hop (>1 sub-query), low confidence | Single sub-query, parametric, cache hit | +500ms LLM call; +5-10s only if gap retrieval fires |
| Claim verifier (default) | Runs after answer tokens, before `done` event | Parametric, cache replay | Does not delay first-token latency; delays final `done` metadata by ~1-2s |
| Claim verifier (quality mode) | Opt-in via `quality_mode=true` query param | Default off | +3-5s (re-generation pass, also before `done`) |
| Adaptive tools | Always-on | — | Calculator/direct_answer **reduce** latency |

### Reflection Loop: Cached-Only Retrieval

> [!IMPORTANT]
> The reflection loop must NOT re-fetch the web. When gaps are found, re-decomposed sub-queries run only against **chunks already in `rt.workspace`** from the original pipeline run. The loop goes back to `retrieve_and_generate` — NOT to `search_urls → extract_pages → chunk_pages`.
>
> This means reflection re-runs BM25 + dense retrieval + cross-encoder reranking + LLM generation on the existing chunk set, with new gap-focused sub-queries. Latency: ~5-10s per gap sub-query (retrieval + generation), not 20-30s (full web pipeline).
>
> **GraphState flag:** `reflection_iteration: int` (0 = first pass, 1 = reflection pass). The routing edge `_route_after_reflect` checks this to prevent infinite loops.

### Claim Verifier: Two Modes + SSE Timing

> [!IMPORTANT]
> The plan must be honest about what moves the faithfulness metric and where the verifier sits in the SSE lifecycle.
>
> **SSE timing:** The verifier runs **after answer tokens stream but before the `done` event**. It does not delay first-token latency, but it delays the final `done` metadata by ~1-2s (default) or ~3-5s (quality mode). The `verify_done` SSE event is emitted before `done`, so the frontend can render the verification badge before the pipeline closes.
>
> **Default mode (post-hoc flagging):** Decomposes answer into atomic claims, checks each against chunks, emits `verify_done` SSE event with supported/unsupported counts. The frontend shows a badge. **This does NOT improve the faithfulness eval score** because the answer text is unchanged.
>
> **Quality mode (re-generation):** Opt-in via `quality_mode=true`. After claim verification identifies unsupported claims, a second LLM pass re-generates the answer with explicit instructions to drop or qualify unsupported claims. **Target: faithfulness 0.649 → 0.8+** (to be validated by eval). Quality mode adds ~3-5s but produces a cleaner answer.
>
> **The reflection node also contributes to faithfulness** by ensuring retrieval covers all parts of the question — better retrieval → better grounding → fewer hallucinated claims.

---

## Execution Order

### Phase 1: Professional Foundation

*Make the repo credible before adding features. Interviewers will clone it.*

---

#### 1. Fix Docs + Fork to Your Account (Day 1)

**Goal:** Fix stale documentation and ensure the repo is under your GitHub account.

| File | Issue | Fix |
|---|---|---|
| [INTERVIEW.md](file:///Users/tusharjain/Downloads/weblens-main/docs/INTERVIEW.md) | Says "8-stage pipeline," references `pipeline/decompose.py`, old fast-path heuristics. No LangGraph/LangSmith/cache/eval mention. | Rewrite from scratch to match v9 architecture |
| [README.md](file:///Users/tusharjain/Downloads/weblens-main/README.md) | Says "13 nodes." Pipeline diagram shows separate retrieve + generate. | Fix to 12 nodes; update topology diagram |
| [ARCHITECTURE.md](file:///Users/tusharjain/Downloads/weblens-main/docs/ARCHITECTURE.md) | Says "13 nodes," old topology | Fix count, update graph diagram |
| [RESUME-ONE-PAGER.md](file:///Users/tusharjain/Downloads/weblens-main/docs/RESUME-ONE-PAGER.md) | Says "13-node" throughout | Grep-and-fix |
| GitHub link | Points to `swapnil18800/weblens` | Fork to your account; update all links |

**Effort:** ~3-4 hours

---

#### 2. Docker + Railway Deploy → Live URL (Day 2-3)

**Goal:** One-command local dev AND a live deployed URL in the resume.

> [!IMPORTANT]
> A live URL in the resume is worth 3× any doc improvement. Railway free tier is sufficient. Prioritize keeping it live and fast, even on a subset of queries.

**Deliverables:**
- `Dockerfile` (multi-stage: Python backend + built React frontend as static files)
- `docker-compose.yml` (backend + frontend dev + local pgvector)
- Railway deploy verified and live
- Live URL added to README header

**Effort:** ~1-1.5 days

---

#### 3. Unit Tests (Week 1)

| Module | What to test |
|---|---|
| [chunk.py](file:///Users/tusharjain/Downloads/weblens-main/pipeline/chunk.py) | Heading-aware splitting, overlap, garbage filter, min-body, dedup |
| [retrieve.py](file:///Users/tusharjain/Downloads/weblens-main/pipeline/retrieve.py) | RRF fusion math, dedup fingerprint, per-URL cap, edge cases |
| [analyze.py](file:///Users/tusharjain/Downloads/weblens-main/pipeline/analyze.py) | `_extract_json_object`, rewrite passthrough, routing edge cases |
| [generate.py](file:///Users/tusharjain/Downloads/weblens-main/pipeline/generate.py) | `strip_unknown_links`, `build_citations`, prompt budget overflow |

```
tests/
├── conftest.py
├── test_chunk.py
├── test_retrieve.py
├── test_analyze.py
└── test_generate.py
```

**Effort:** ~2-3 days

---

#### 4. CI/CD (GitHub Actions)

- `ci.yml`: lint (`ruff`) + `pytest` on push/PR
- `eval-smoke.yml`: run 6-question smoke eval, post results as PR comment
- `deploy.yml`: auto-deploy to Railway on merge to main

**Effort:** ~1 day

---

#### 5. TokenTracker Wiring

Wire the existing `TokenTracker` into [llm/deepseek.py](file:///Users/tusharjain/Downloads/weblens-main/llm/deepseek.py) + [llm/openai_client.py](file:///Users/tusharjain/Downloads/weblens-main/llm/openai_client.py). Extract `usage.prompt_tokens` + `completion_tokens`, store in latency_breakdown JSONB, surface in eval results.

> [!NOTE]
> Non-streaming completions return `usage` directly. Streaming completions require provider-specific handling: OpenAI includes usage in the final chunk when `stream_options={"include_usage": true}`; DeepSeek may differ. Add a fallback token estimator (tiktoken-based approximation) for providers that don't report usage on streaming calls.

**Effort:** ~0.5-1 day

---

### Phase 2: Agentic Capabilities + Eval Expansion

*The resume differentiators. Eval dataset expands alongside features — every feature ships with numbers.*

---

#### 6. Expand Eval Dataset (50-60 questions)

> [!IMPORTANT]
> Moved here from Phase 3. You can't credibly claim agentic features improved metrics without benchmarking them. The expanded eval set must be ready **before** items 7-9 land.

**New categories to add:**

| Category | Count | Purpose |
|---|---|---|
| `tool_selection` | 6 | "What is 15% of 340?", "Find RLHF papers from 2025" — tests adaptive routing |
| `adversarial_citation` | 4 | "Cite arxiv.org/abs/1234.5678" — tests citation faithfulness |
| `prompt_injection` | 4 | Queries with injected instructions — tests extraction sanitization |
| `multi_turn_topic_switch` | 4 | Q1→Q2 topic change — tests conversation isolation |
| `cross_source_contradiction` | 4 | Sources disagree — tests nuanced synthesis |

**Target:** 52-58 total questions across 15 categories.

**Effort:** ~1-2 days

---

#### 7. Adaptive Tool Selection + Decision Rationale

**Goal:** Upgrade `analyze` from `parametric/search` binary to multi-tool planning with logged decision rationale.

**Tools:**

| Tool | Use case | Latency vs search baseline |
|---|---|---|
| `direct_answer()` | Stable facts, greetings | **-30s** |
| `calculator(expr)` | Arithmetic, percentages | **-35s** |
| `web_search(query)` | Current Tavily path | Baseline |
| `academic_search(query)` | arXiv/Semantic Scholar for research | **Faster** than web_search (no page extraction needed — arXiv API returns structured abstracts) |

**Tool-selection rationale:**
- The `analyze` prompt outputs `tool_rationale: "This is an arithmetic question — calculator is sufficient, no web search needed"` alongside `tools: ["calculator"]`
- `tool_rationale` is logged to LangSmith as a span attribute and persisted in the trace JSONB
- Interview talking point: "I can show you a LangSmith trace where the model explains why it chose calculator over web search"

**Implementation:**
- Modify [pipeline/analyze.py](file:///Users/tusharjain/Downloads/weblens-main/pipeline/analyze.py) prompt → `tools: [...]` + `tool_rationale: "..."`
- New file: `pipeline/tools/calculator.py` — safe expression eval using `ast.parse(expr, mode="eval")` with an allow-list AST walker (permit only numeric literals, `+`, `-`, `*`, `/`, `**`, `%`; reject calls, attribute access, names). Not `ast.literal_eval` (can't evaluate arithmetic) and not raw `eval()`.
- New file: `pipeline/tools/academic.py` — arXiv API wrapper returning structured abstracts
- Backward compatible: `mode: "search"` internally maps to `tools: ["web_search"]`

**Effort:** ~3-4 days

---

#### 8. Reflection Node (Cached-Only Gap Retrieval + Merge)

**Goal:** Post-answer LLM reflection → gap detection → re-retrieve + re-generate from cached chunks → merge with original answers.

**Loop design:**
```
retrieve_and_generate (first pass)
        ↓
   node_reflect ←────────────────┐
        ↓                        │
  _route_after_reflect           │
   /          \                  │
COMPLETE    GAPS_FOUND           │
   ↓        ↓                    │
node_      save first-pass state │
verify     to base_* fields,     │
           inject gap_queries    │
           as sub_queries,       │
           loop back ────────────┘
           (only if iteration == 0)
```

**Critical constraint:** Gap retrieval uses `rt.workspace["chunks"]` (already fetched and cached from the original pipeline run). No `search_urls → extract_pages → chunk_pages` re-run. The reflection loop adds ~5-10s per gap sub-query, not 20-30s.

**Merge design (the key correctness issue):**

> [!IMPORTANT]
> `node_retrieve_and_generate` initializes fresh accumulators from `state["sub_queries"]` and returns new `final_answer`, `traces`, `citations`, and `all_chunks`. Looping back with gap queries will **replace** the original answers unless we explicitly preserve and merge them.
>
> Before looping, `node_reflect` must save first-pass outputs to merge state:
> - `base_sub_answers: list[dict]` — `{query, answer, citations}` from the first pass
> - `base_traces: list[dict]` — per-sub-query trace objects from the first pass
> - `base_citation_map: dict[str, int]` — the global `[N]` assignments so far
> - `base_all_chunks: list[dict]` — chunk dicts from the first pass
>
> After the reflection pass completes, `node_reflect` (on iteration=1) merges:
> - `sub_answers = base_sub_answers + gap_sub_answers`
> - `traces = base_traces + gap_traces`
> - `citations` union with consistent `[N]` numbering (extend from `base_citation_map`)
> - A final synthesis LLM call over the merged sub-answers produces the new `final_answer`
>
> This ensures the gap answers **augment** the original, not replace it.

**GraphState additions:**
- `reflection_iteration: int` — 0 = first pass, 1 = reflection pass
- `reflection_gaps: list[str]` — gap sub-queries identified by reflection
- `reflection_triggered: bool` — whether reflection actually fired
- `base_sub_answers: list[dict]` — saved first-pass sub-answers for merge
- `base_traces: list[dict]` — saved first-pass traces for merge
- `base_citation_map: dict[str, int]` — saved citation numbering for consistent [N]s
- `base_all_chunks: list[dict]` — saved first-pass chunks for merge

**Conditional activation:**
- ON: `len(sub_queries) > 1`, or `confidence < 0.7`, or `reflection_enabled=true` query param
- OFF: single sub-query with high confidence, parametric, cache hit

**Eval target:** Improves faithfulness (better retrieval coverage → fewer hallucinated claims) and context_recall on under-decomposed queries.

**Effort:** ~2-3 days

---

#### 9. Claim-Level Verifier (Two Modes)

**SSE position:** Runs after answer tokens complete but **before** the `done` event. Does not delay first-token latency, but delays final `done` metadata by ~1-2s (default) or ~3-5s (quality mode).

**Default mode (post-hoc flagging):**
- Decomposes answer into ≤8 atomic claims
- Checks each claim against retrieved chunk text (string matching + semantic similarity)
- Emits `verify_done` SSE event before `done`: `{total_claims, supported, unsupported, unsupported_claims[]}`
- Frontend shows "✓ 6/7 claims verified" badge
- **Does NOT change the answer or improve faithfulness eval score**

**Quality mode (re-generation):**
- Opt-in via `quality_mode=true` query param or `QUALITY_MODE_DEFAULT=true` env var
- After verification identifies unsupported claims, a second LLM pass re-generates with:
  - "The following claims from your previous answer are NOT supported by the sources: [list]. Re-write the answer, dropping or qualifying these claims."
- Adds ~3-5s
- **Target: faithfulness 0.649 → 0.8+** (to be validated by eval after implementation — only use this number in resume bullets once proven)
- Eval runs use `quality_mode=true` by default

**Effort:** ~2-3 days

---

### Phase 3: Production Hardening

---

#### 10. Prompt-Injection Protection (Deep, Not Shallow)

> [!WARNING]
> Pattern-matching "ignore previous instructions" is trivially bypassable. Either go deep or keep it as hygiene and don't pitch it on the resume.

**Deep implementation (resume-worthy):**
- **Unicode normalization** in extraction: NFKC normalize + strip zero-width chars, homoglyphs, RTL overrides before chunking
- **Structured prompt delimiters**: all source blocks wrapped in `<SOURCE id="N">...</SOURCE>` XML tags with explicit `<INSTRUCTION>` boundary — model trained to treat anything outside `<INSTRUCTION>` as untrusted data
- **Output validation**: post-generation regex check that `[N]` citations reference valid source IDs; reject answers that contain instruction-like patterns ("As an AI...", "I cannot...")
- **Indirect injection via URLs**: if extracted markdown contains `http://` links not in the original search results, flag as suspicious

**Effort:** ~1-2 days

---

#### 11. Auth + Rate Limiting

- `slowapi` rate limiter: 10 req/min per IP on `/api/search`
- Optional `X-API-Key` auth (env-driven, off for dev)

**Effort:** ~0.5-1 day

---

#### 12. Source Credibility Ranking

- Domain reputation tiers: `.edu/.gov` > established outlets > forums
- Small RRF boost for higher-tier sources
- Recency bonus for temporal queries
- Track `source_tier_distribution` in eval results

**Effort:** ~1-2 days

---

#### 13. Human Feedback Loop

- `POST /api/feedback` with `{session_id, message_id, rating, correction}`
- `rag_feedback` table
- Frontend: thumbs up/down on answers, "report citation" on citation chips

**Effort:** ~1-2 days

---

### Phase 4: Stretch

#### 14. CONTRIBUTING.md (~1-2 hours)
#### 15. Long-Term Memory System (~3-4 days, deprioritized)

---

## Observability: LangSmith Spans for Every New Node

> Each new node must emit structured LangSmith spans so the agentic loop is debuggable, not just functional.

| Node | `run_type` | Key Span Attributes | Interview Signal |
|---|---|---|---|
| `node_reflect` | `chain` | `gaps_found: bool`, `gap_queries: list`, `iteration: int`, `action: "loop" \| "continue"`, `base_sub_answers_count: int`, `merged_sub_answers_count: int`, `latency_ms` | "I can show you a trace where the agent decides the answer is incomplete, identifies gaps, and merges new sub-answers with the originals" |
| `node_verify` | `chain` | `total_claims: int`, `supported: int`, `unsupported: int`, `unsupported_claims: list`, `mode: "flag" \| "regenerate"`, `latency_ms` | "The verifier trace shows which claims failed and what the re-generated answer changed" |
| `analyze` (upgraded) | `chain` | `tools_selected: list`, `tool_rationale: str`, `confidence: float` | "The tool-selection trace shows the model's rationale for why it chose calculator over web search" |
| Calculator tool | `tool` | `expression: str`, `result: float`, `safe_eval: bool` | — |
| Academic search | `tool` | `query: str`, `results_count: int`, `source: "arxiv" \| "semantic_scholar"` | — |

---

## Failure Modes & Fallbacks

> Every new node has an explicit fallback. No happy-path-only designs.

| Node | Failure | Fallback | Latency Cost |
|---|---|---|---|
| `node_reflect` | LLM call times out (>3s) | Skip reflection, continue to `embedding_cleanup`. Log warning. Emit `reflection_done` with `{triggered: false, reason: "timeout"}`. | 0s (timeout aborted) |
| `node_reflect` | LLM returns malformed JSON | Parse error → treat as `COMPLETE`. Log warning + raw response to LangSmith. | ~500ms (wasted LLM call) |
| `node_reflect` | Gap retrieval finds no relevant chunks | Skip re-generation for that gap. Emit `reflection_done` with `{gaps_found: true, gaps_resolved: 0}`. | ~2s (retrieval ran but no results) |
| `node_verify` | LLM call fails | Skip verification. Emit `verify_done` with `{skipped: true, reason: "llm_error"}`. | 0s |
| `node_verify` | Claim extraction returns >8 claims | Truncate to first 8 claims (ordered by position in answer). Log warning. | Same |
| `node_verify` (quality mode) | Re-generation fails | Keep original answer unchanged. Emit `verify_done` with `{regeneration_failed: true}`. | ~1s (wasted attempt) |
| Calculator tool | Unsafe expression / parse error | Fall back to `web_search` for the same query. Log tool fallback to LangSmith. | +20-30s (full pipeline) |
| Academic search | arXiv API timeout or 5xx | Fall back to `web_search`. Log tool fallback. | +5-10s (Tavily is faster than waiting for arXiv timeout) |
| Tool selection | LLM returns unknown tool name | Default to `web_search`. Log warning. | 0s |

---

## Summary: Timeline

| # | Item | Phase | Effort | Eval Run After? |
|---|---|---|---|---|
| 1 | Fix docs + fork repo | Foundation | 3-4h | No |
| 2 | Docker + Railway live URL | Foundation | 1-1.5d | No |
| 3 | Unit tests | Foundation | 2-3d | No |
| 4 | CI/CD | Foundation | 1d | No |
| 5 | TokenTracker wiring | Foundation | 0.5-1d | No |
| 6 | Expand eval to 50-60 Qs | Agentic | 1-2d | Yes — new baseline |
| 7 | Adaptive tool selection | Agentic | 3-4d | Yes — tool_selection accuracy |
| 8 | Reflection node | Agentic | 2-3d | Yes — faithfulness, context_recall |
| 9 | Claim verifier | Agentic | 2-3d | Yes — faithfulness (quality mode) |
| 10 | Prompt-injection protection | Hardening | 1-2d | Yes — prompt_injection category |
| 11 | Auth + rate limiting | Hardening | 0.5-1d | No |
| 12 | Source credibility ranking | Hardening | 1-2d | Yes — retrieval quality |
| 13 | Human feedback loop | Hardening | 1-2d | No |
| 14 | CONTRIBUTING.md | Stretch | 1-2h | No |
| 15 | Long-term memory | Stretch | 3-4d | Yes |

**Total estimated effort (items 1-13):** ~22-30 days

---

## Resume Positioning

**After Phase 1 (foundation):**
> Built a production-grade web RAG pipeline with LangGraph, hybrid retrieval (BM25 + dense + RRF + cross-encoder), semantic caching, streaming SSE observability, LangSmith tracing, and a 30-question automated eval harness with 5 RAG metrics — scoring 0.789 aggregate across 10 adversarial categories.

**After Phases 1-2 (foundation + agentic):**
> Built an agentic web research system that autonomously routes queries across tools (web search, calculator, academic search) with logged decision rationale, reflects on answer coverage to re-decompose gaps from cached context and merge augmented sub-answers, and verifies claims against source chunks via a generator-verifier architecture — targeting 0.8+ faithfulness on a 55-question adversarial benchmark with full LangSmith observability for every agentic decision. *(Update with actual eval numbers once proven.)*

**After Phases 1-3 (full):**
> Built an agentic web research system with LangGraph-based tool routing, hybrid retrieval, reflection-based gap recovery, claim-level citation verification, prompt-injection hardening, source credibility ranking, streaming responses, semantic cache, eval regression testing, Dockerized deployment, human feedback collection, and per-request cost/latency observability — deployed live at [URL].
