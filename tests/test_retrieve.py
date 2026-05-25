from pipeline.chunk import Chunk
from pipeline.retrieve import (
    RankedChunk,
    _apply_credibility_boost,
    _cap_per_url,
    _dedupe_ranked,
    _domain_tier,
    _rrf_merge,
)


def _chunk(url: str, index: int, text: str = "body") -> Chunk:
    return Chunk(url=url, title=url, chunk_index=index, chunk_text=text, heading="")


def test_rrf_merge_combines_dense_and_bm25_rank_positions():
    merged = _rrf_merge(
        vec_ranks=[(0, 0.9), (1, 0.8)],
        bm25_ranks=[(1, 10.0), (2, 9.0)],
        n=3,
        k=60,
    )

    assert merged[0][0] == 1
    assert {idx for idx, _ in merged} == {0, 1, 2}


def test_dedupe_ranked_drops_exact_and_text_duplicates():
    ranked = [
        RankedChunk(_chunk("https://a.test", 0, "alpha " * 120), 0.9, 0),
        RankedChunk(_chunk("https://a.test", 0, "alpha " * 120), 0.8, 1),
        RankedChunk(_chunk("https://b.test", 0, "alpha " * 120), 0.7, 2),
    ]

    kept, dropped = _dedupe_ranked(ranked)

    assert kept == [ranked[0]]
    assert dropped == 2


def test_cap_per_url_limits_source_dominance():
    ranked = [
        RankedChunk(_chunk("https://a.test", i), 1.0 - i / 10, i)
        for i in range(4)
    ] + [
        RankedChunk(_chunk("https://b.test", 0), 0.1, 4)
    ]

    kept, dropped = _cap_per_url(ranked, top_k=4)

    assert [rc.chunk.url for rc in kept] == [
        "https://a.test",
        "https://a.test",
        "https://b.test",
    ]
    assert dropped == 2


def test_domain_tier_classifies_common_edu_and_gov_hosts():
    assert _domain_tier("https://harvard.edu/news/research") == 0
    assert _domain_tier("https://www.nih.gov/news-events") == 0
    assert _domain_tier("https://example.edu.au/report") == 0


def test_recency_boost_only_applies_when_requested():
    chunks = [
        _chunk("https://general.test/2026/report", 0),
        _chunk("https://general.test/2021/report", 1),
    ]
    ranked = [(0, 0.02), (1, 0.02)]

    without_recency, _ = _apply_credibility_boost(ranked, chunks, apply_recency=False)
    with_recency, _ = _apply_credibility_boost(ranked, chunks, apply_recency=True)

    assert without_recency == ranked
    assert with_recency[0][1] > with_recency[1][1]
