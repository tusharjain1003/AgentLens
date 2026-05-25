# WebLens Implementation Plan — Code Review

> Reviewed against: [implementation_plan.md](file:///Users/tusharjain/Downloads/weblens-main/implementation_plan.md)
> Tests: ✅ 18/18 passed

---

## Scorecard: Plan Item Coverage

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | Fix Docs + Fork | ⚠️ Partial | README updated; **3 stale references remain** |
| 2 | Docker + Railway | ✅ Done | Multi-stage Dockerfile + docker-compose + Railway workflows |
| 3 | Unit Tests | ✅ Done | 6 test files, 18 tests, all passing |
| 4 | CI/CD | ✅ Done | `ci.yml` + `eval-smoke.yml` + `deploy.yml` |
| 5 | TokenTracker Wiring | ✅ Done | Both `deepseek.py` and `openai_client.py` wired with usage extraction + fallback estimation |
| 6 | Expand Eval Dataset | ✅ Done | 52 questions, 15 categories including `tool_selection`, `adversarial_citation`, `prompt_injection`, `multi_turn_topic_switch`, `cross_source_contradiction` |
| 7 | Adaptive Tool Selection | ✅ Done | `calculator.py`, `academic.py`, analyze prompt with tool routing + `tool_rationale` |
| 8 | Reflection Node | ✅ Done | `node_reflect` with cached-only gap retrieval, merge, citation shifting |
| 9 | Claim Verifier | ✅ Done | `node_verify` with two modes (flag / regenerate), quality_mode config |
| 10 | Prompt-Injection Protection | ✅ Done | NFKC normalize, zero-width strip, `<SOURCE>` delimiters, output validation, indirect URL injection |
| 11 | Auth + Rate Limiting | ✅ Done | `slowapi` + `X-API-Key` header |
| 12 | Source Credibility Ranking | ✅ Done | `_domain_tier`, `_apply_credibility_boost`, recency bonus, tier distribution in explain |
| 13 | Human Feedback Loop | ✅ Done | `POST /api/feedback`, `rag_feedback` table, `db/feedback.py` |
| 14 | CONTRIBUTING.md | ✅ Done | Comprehensive guide with project structure, workflow, architecture notes |
| 15 | Long-Term Memory | N/A | Deprioritized per plan |

---

## 🟢 What's Implemented Well

### Graph Architecture
The [graph.py](file:///Users/tusharjain/Downloads/weblens-main/pipeline/graph.py) is the standout. The topology correctly wires all the plan's new nodes:

```
retrieve_and_generate → reflect → (loop back or continue) → verify → embedding_cleanup → cache_insert → emit_done
```

- **Reflection loop** is correctly bounded (iteration ≤ 1), cached-only (re-uses `rt.workspace["chunks"]`), and merges sub-answers with citation number shifting — exactly matching the plan's merge design.
- **Verify node** correctly implements two modes with the `quality_mode` config, and the SSE timing is right (runs after answer tokens, before `done`).
- **Calculator routing** has proper fallback to `web_search` on error.
- **Output validation** (`_validate_answer`) is a solid prompt-injection defense — checks invalid `[N]` citations and instruction-like patterns, with repair-not-block semantics.

### Tool Selection ([analyze.py](file:///Users/tusharjain/Downloads/weblens-main/pipeline/analyze.py))
The analyze prompt is well-designed:
- 4 tools (`direct_answer`, `calculator`, `web_search`, `academic_search`) with clear use-case definitions
- `tool_rationale` is logged — good for interview demos
- Backward-compatible: `mode="search"` without tools maps to `["web_search"]`
- Tool allowlist validation with sensible fallbacks (unknown tool → `web_search`)

### Calculator Tool ([calculator.py](file:///Users/tusharjain/Downloads/weblens-main/pipeline/tools/calculator.py))
Correctly uses `ast.parse(expr, mode="eval")` with an AST walker — not `eval()`. Has:
- Power limit (max exponent 12)
- Division-by-zero guard
- Result magnitude cap (1e18)
- Unicode normalization (`×` → `*`, `÷` → `/`, `^` → `**`)

### Tests
All test files are well-structured:
- [test_calculator.py](file:///Users/tusharjain/Downloads/weblens-main/tests/test_calculator.py): Tests safe arithmetic, name injection rejection, div-by-zero, huge power
- [test_retrieve.py](file:///Users/tusharjain/Downloads/weblens-main/tests/test_retrieve.py): Tests RRF math, dedup, per-URL cap, domain tier, recency boost
- [test_chunk.py](file:///Users/tusharjain/Downloads/weblens-main/tests/test_chunk.py): Heading preservation, short-body filter, cross-page dedup
- [test_analyze.py](file:///Users/tusharjain/Downloads/weblens-main/tests/test_analyze.py): JSON extraction from fenced/plain, tool fields
- [test_generate.py](file:///Users/tusharjain/Downloads/weblens-main/tests/test_generate.py): Link stripping, citation dedup

### CI/CD
- [ci.yml](file:///Users/tusharjain/Downloads/weblens-main/.github/workflows/ci.yml): Ruff lint + pytest + frontend build on every push/PR ✅
- [eval-smoke.yml](file:///Users/tusharjain/Downloads/weblens-main/.github/workflows/eval-smoke.yml): 6-question smoke eval with pgvector service, PR comment with results ✅
- [deploy.yml](file:///Users/tusharjain/Downloads/weblens-main/.github/workflows/deploy.yml): Railway deploy on merge to main, with graceful skip when token missing ✅

---

## 🟡 Issues Found (Should Fix)

### 1. Stale GitHub Links in Frontend (from Plan Item #1)

> [!WARNING]
> Two frontend files still reference the **original** repo owner `swapnil18800/weblens` instead of your fork. An interviewer cloning the repo will see these.

| File | Line | Current | Should Be |
|---|---|---|---|
| [Header.tsx](file:///Users/tusharjain/Downloads/weblens-main/frontend/src/components/Header.tsx#L64) | 64 | `github.com/swapnil18800/weblens` | `github.com/tusharjain1003/AgentLens` |
| [InfoPopover.tsx](file:///Users/tusharjain/Downloads/weblens-main/frontend/src/components/InfoPopover.tsx#L7-L8) | 7-8 | `github.com/swapnil18800/weblens` + LinkedIn `swapnil18800` | Your GitHub + LinkedIn URLs |

### 2. Stale "13-node" References in Docs (from Plan Item #1)

The plan explicitly called out fixing the node count from 13 → 12, but several docs still say "13":

| File | Line(s) | Issue |
|---|---|---|
| [EVALUATION-RESULTS.md](file:///Users/tusharjain/Downloads/weblens-main/docs/EVALUATION-RESULTS.md#L135) | 135, 150, 344, 358, 555 | "13-node" references |
| [implementation-summary-v9.md](file:///Users/tusharjain/Downloads/weblens-main/docs/implementation-summary-v9.md#L26) | 26, 178 | "13 nodes" |
| [OVERALL-IMPROVEMENT-SUMMARY.md](file:///Users/tusharjain/Downloads/weblens-main/docs/OVERALL-IMPROVEMENT-SUMMARY.md#L32) | 32 | "8-stage pipeline" |

> [!NOTE]
> With the addition of `reflect`, `verify`, and `calculator_answer` nodes, the actual node count is now **15** (rewrite_query, analyze, parametric_answer, calculator_answer, cache_lookup, cache_replay, search_urls, extract_pages, chunk_pages, retrieve_and_generate, reflect, verify, embedding_cleanup, cache_insert, emit_done). The README says 12, which was the v9 count. You should update docs to the actual current count.

### 3. README Roadmap Section is Stale

[README.md lines 553-569](file:///Users/tusharjain/Downloads/weblens-main/README.md#L553-L569) still lists these as "Planned improvements" with unchecked boxes:
- `[ ] Reflection node` — **already implemented**
- `[ ] Post-hoc hallucination verification pass` — **already implemented**
- `[ ] LLM cost attribution via TokenTracker` — **already implemented**

The "Known Limitations" section at L556-561 still says "TokenTracker wired but not called from LLM clients" — which is no longer true. The faithfulness score listed (0.606) is also from the old baseline.

### 4. `_route_after_chunk` Points to Wrong Node Name

In [graph.py L1959](file:///Users/tusharjain/Downloads/weblens-main/pipeline/graph.py#L1959):
```python
def _route_after_chunk(state: GraphState) -> str:
    return "emit_done" if state.get("error") else "retrieve"
```

But the node registered is `"retrieve_and_generate"`, not `"retrieve"`. The edge map at [L2018-2019](file:///Users/tusharjain/Downloads/weblens-main/pipeline/graph.py#L2018-L2019) correctly maps `"retrieve"` → `"retrieve_and_generate"`:
```python
g.add_conditional_edges("chunk_pages", _route_after_chunk,
                        {"emit_done": "emit_done", "retrieve": "retrieve_and_generate"})
```

This works because the edge map remaps the string, but it's confusing. The routing function returns `"retrieve"` which the edge map silently translates to `"retrieve_and_generate"`. This is technically correct but fragile — if someone refactors the edge map, the implicit rename would break.

### 5. DeepSeek Streaming Doesn't Request Usage

[deepseek.py L66-71](file:///Users/tusharjain/Downloads/weblens-main/llm/deepseek.py#L66-L71) creates the streaming request without `stream_options={"include_usage": True}`. The plan's Item #5 note says:

> *"DeepSeek may differ. Add a fallback token estimator."*

The fallback estimator (`_estimate_tokens`) is present, which is good. But the OpenAI client at [openai_client.py L67](file:///Users/tusharjain/Downloads/weblens-main/llm/openai_client.py#L67) correctly sends `stream_options={"include_usage": True}`. You should try adding it to DeepSeek too — if their API supports it, you'll get real token counts instead of estimates.

### 6. `node_reflect` Merge: `_shift_citation_numbers` with offset=0 is a No-op

At [graph.py L1130](file:///Users/tusharjain/Downloads/weblens-main/pipeline/graph.py#L1130):
```python
final_answer = _shift_citation_numbers(final_answer, 0)
```

This calls `_shift_citation_numbers` with offset=0, which at [L1247](file:///Users/tusharjain/Downloads/weblens-main/pipeline/graph.py#L1247) returns the text unchanged:
```python
if offset <= 0:
    return text
```

This is dead code — not a bug, but should be removed for clarity.

---

## 🔴 Potential Bugs

### 1. Claim Verifier: Word-Overlap Threshold May Be Too Loose

The [_claim_supported](file:///Users/tusharjain/Downloads/weblens-main/pipeline/graph.py#L1370-L1379) function uses a 45% word-overlap threshold to determine if a claim is supported by chunks:

```python
return hits / max(1, len(set(words))) >= 0.45
```

With only a stop-word filter of 9 common words, many content-bearing words like "the", "and", "for", "are", "has", "was" etc. are NOT filtered. This means the overlap count gets inflated by common words that appear in most texts. A claim like "The results are very impressive and show significant progress" could match chunk text about a completely different topic just by sharing "results", "impressive", "show", "significant", "progress" which are all fairly common.

**Recommendation**: Either expand the stop-word list significantly, or use TF-IDF weighted matching, or use a semantic similarity check (you already have embeddings infrastructure).

### 2. Academic Search: Response Used Outside HTTP Context

In [academic.py L31-33](file:///Users/tusharjain/Downloads/weblens-main/pipeline/tools/academic.py#L31-L33):
```python
async with httpx.AsyncClient(timeout=timeout_s) as client:
    resp = await client.get(f"{ARXIV_API_URL}?{params}")
    resp.raise_for_status()

root = ET.fromstring(resp.text)  # resp used after client is closed
```

The `resp` object is used **after** the `async with` block exits and the client is closed. For `httpx`, the response body is fully loaded by the time `resp.raise_for_status()` returns (since it's not streaming), so `resp.text` should still be accessible. However, this is fragile — if someone changes this to streaming mode, it would break. Better to capture the text inside the context manager:

```python
async with httpx.AsyncClient(timeout=timeout_s) as client:
    resp = await client.get(f"{ARXIV_API_URL}?{params}")
    resp.raise_for_status()
    text = resp.text
root = ET.fromstring(text)
```

---

## 📊 Summary

| Area | Grade | Comment |
|---|---|---|
| **Architecture** | A | Reflection loop, verify node, tool routing all correctly wired |
| **Safety** | A | NFKC normalization, `<SOURCE>` delimiters, output validation, injection detection |
| **Tests** | B+ | Good coverage of core utils; no tests for reflection/verify nodes themselves |
| **CI/CD** | A | All 3 workflows well-designed, secret-gated |
| **Docs** | B- | Content is good; stale references need cleanup |
| **Eval Dataset** | A | 52 questions across 15 categories, well-tagged |

### Priority Fixes

1. **🔴 Fix frontend GitHub/LinkedIn links** — interviewers will see these immediately
2. **🟡 Update README "Planned improvements"** — contradicts what's already built
3. **🟡 Fix node count in docs** — should be 15, not 12 or 13
4. **🟡 Extract `resp.text` inside the httpx context manager** in `academic.py`
5. **🟢 Consider adding `stream_options` to DeepSeek** for real token counts
6. **🟢 Clean up dead `_shift_citation_numbers(…, 0)` call**

Want me to apply any of these fixes?
