from pipeline.chunk import Chunk, _dedupe_chunks, _is_garbage_chunk, chunk_page, chunk_pages
from pipeline.extract import ExtractedPage


def _page(markdown: str, url: str = "https://example.com/a") -> ExtractedPage:
    return ExtractedPage(
        url=url,
        title="Example",
        markdown=markdown,
        char_count=len(markdown),
        from_cache=False,
    )


def test_chunk_page_preserves_heading_context():
    body = " ".join(["retrieval"] * 80)
    chunks, stats = chunk_page(_page(f"# Retrieval\n\n{body}"))

    assert stats == {"min_body_dropped": 0, "garbage_dropped": 0}
    assert len(chunks) == 1
    assert chunks[0].heading == "Retrieval"
    assert chunks[0].chunk_text.startswith("Retrieval\n\n")


def test_chunk_page_filters_short_body_and_navigation_garbage():
    short_chunks, short_stats = chunk_page(_page("# Tiny\n\nToo short."))
    nav = "\n".join(["Home", "Menu", "Search", "Privacy policy"])
    assert short_chunks == []
    assert short_stats["min_body_dropped"] == 1
    assert _is_garbage_chunk(nav) is True


def test_chunk_pages_deduplicates_across_pages_and_tracks_stats():
    text = " ".join(["same paragraph"] * 40)
    pages = [
        _page(f"# A\n\n{text}", "https://example.com/a"),
        _page(f"# A\n\n{text}", "https://example.com/b"),
    ]

    chunks, global_stats, per_url_stats = chunk_pages(pages)

    assert len(chunks) == 1
    assert global_stats["dedup_dropped"] == 1
    assert per_url_stats["https://example.com/b"]["dedup_dropped"] == 1
    assert per_url_stats["https://example.com/b"]["kept"] == 0


def test_dedupe_chunks_keeps_first_seen_chunk():
    first = Chunk("https://example.com", "Example", 0, "Repeated " * 40, "")
    duplicate = Chunk("https://example.com", "Example", 1, "Repeated " * 40, "")

    assert _dedupe_chunks([first, duplicate]) == [first]
