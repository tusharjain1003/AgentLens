"""Lightweight arXiv API wrapper for future academic-search routing."""
from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx


ARXIV_API_URL = "https://export.arxiv.org/api/query"


@dataclass(frozen=True)
class AcademicResult:
    title: str
    url: str
    summary: str
    published: str = ""


async def search_arxiv(query: str, max_results: int = 5, timeout_s: float = 8.0) -> list[AcademicResult]:
    params = urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max(1, min(max_results, 10)),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.get(f"{ARXIV_API_URL}?{params}")
        resp.raise_for_status()
        body = resp.text

    root = ET.fromstring(body)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    results: list[AcademicResult] = []
    for entry in root.findall("atom:entry", ns):
        title = _text(entry, "atom:title", ns)
        summary = _text(entry, "atom:summary", ns)
        url = _text(entry, "atom:id", ns)
        published = _text(entry, "atom:published", ns)
        if title and url:
            results.append(AcademicResult(
                title=html.unescape(" ".join(title.split())),
                url=url.strip(),
                summary=html.unescape(" ".join(summary.split())),
                published=published[:10],
            ))
    return results


def _text(entry: ET.Element, path: str, ns: dict[str, str]) -> str:
    node = entry.find(path, ns)
    return node.text if node is not None and node.text else ""
