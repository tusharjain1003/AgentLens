from pipeline.chunk import Chunk
from pipeline.generate import build_citations, strip_unknown_links
from pipeline.retrieve import RankedChunk


def test_strip_unknown_links_preserves_allowed_and_unlinks_unknown():
    answer = "Read [allowed](https://example.com/a/) and [bad](https://evil.test/x)."

    cleaned, stripped = strip_unknown_links(answer, {"https://example.com/a"})

    assert "[allowed](https://example.com/a/)" in cleaned
    assert "bad" in cleaned
    assert "https://evil.test/x" not in cleaned
    assert stripped == 1


def test_build_citations_deduplicates_by_url_and_uses_global_numbers():
    first = RankedChunk(
        Chunk("https://example.com/a", "A", 0, "best snippet", "Intro"),
        score=0.5,
        rank=0,
    )
    better_same_url = RankedChunk(
        Chunk("https://example.com/a", "A", 1, "better snippet", "Details"),
        score=0.9,
        rank=1,
    )
    second = RankedChunk(
        Chunk("https://example.com/b", "B", 0, "other snippet", "Other"),
        score=0.8,
        rank=2,
    )

    citations = build_citations(
        [first, better_same_url, second],
        {"https://example.com/a": 7, "https://example.com/b": 3},
    )

    assert [c["num"] for c in citations] == [7, 3]
    assert [c["url"] for c in citations] == ["https://example.com/a", "https://example.com/b"]
    assert citations[0]["snippet"] == "better snippet"
