"""
Human feedback persistence for rag_feedback table.

Stores ratings, corrections, and citation-level feedback per message.
"""
from __future__ import annotations
import logging

import db.client as db

logger = logging.getLogger(__name__)


async def save_feedback(
    session_id: str,
    message_id: int,
    rating: int,
    correction: str = "",
    feedback_type: str = "overall",
    citation_num: int | None = None,
    metadata: dict | None = None,
) -> int:
    """Insert a feedback row. Returns the new row's id."""
    rating = max(-1, min(1, int(rating)))
    row = await db.fetchrow(
        """
        INSERT INTO rag_feedback
            (session_id, message_id, rating, correction, feedback_type, citation_num, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        session_id,
        int(message_id),
        rating,
        correction,
        feedback_type,
        citation_num,
        metadata or {},
    )
    return row["id"] if row else -1


async def get_feedback_for_message(
    session_id: str,
    message_id: int,
) -> list[dict]:
    """Return all feedback rows for a given session message."""
    rows = await db.fetch(
        """
        SELECT id, rating, correction, feedback_type, citation_num, metadata, created_at
        FROM rag_feedback
        WHERE session_id = $1 AND message_id = $2
        ORDER BY created_at DESC
        """,
        session_id,
        int(message_id),
    )
    return [dict(r) for r in rows]


async def get_feedback_stats() -> dict:
    """Return aggregated feedback statistics."""
    row = await db.fetchrow(
        """
        SELECT
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE rating = 1) AS thumbs_up,
            COUNT(*) FILTER (WHERE rating = -1) AS thumbs_down,
            COUNT(*) FILTER (WHERE rating = 0) AS neutral,
            COUNT(*) FILTER (WHERE correction != '') AS with_corrections,
            COUNT(*) FILTER (WHERE feedback_type = 'citation') AS citation_reports
        FROM rag_feedback
        """
    )
    return dict(row) if row else {}
