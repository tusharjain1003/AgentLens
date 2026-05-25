from pipeline.chunk import Chunk
from pipeline.retrieve import RankedChunk, _cap_per_url, _dedupe_ranked, _rrf_merge


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
