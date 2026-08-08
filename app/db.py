from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS posts (
  id TEXT PRIMARY KEY,
    agent_id TEXT,
  created_at TEXT,
  text TEXT,
  rationale TEXT,
  sources TEXT,
  topic_fingerprint TEXT
);

CREATE TABLE IF NOT EXISTS rejected_topics (
  id TEXT PRIMARY KEY,
  agent_id TEXT,
  seen_at TEXT,
  topic_summary TEXT,
  reject_reason TEXT,
  topic_fingerprint TEXT
);

CREATE TABLE IF NOT EXISTS queued_posts (
  id TEXT PRIMARY KEY,
  agent_id TEXT,
  queued_at TEXT,
  title TEXT,
  summary TEXT,
  source_name TEXT,
  source_urls TEXT,
  topic_fingerprint TEXT,
  decision_reason TEXT
);

CREATE TABLE IF NOT EXISTS agent (
  agent_id TEXT PRIMARY KEY,
  persona_name TEXT,
  persona_domain TEXT,
  initialized_at TEXT
);
"""


class Database:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.db_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA journal_mode=WAL;")
            connection.execute("PRAGMA synchronous=NORMAL;")
        except Exception:
            pass
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(SCHEMA_SQL)

    def create_agent(self, agent_id: str, persona_name: str, persona_domain: str, initialized_at: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO agent(agent_id, persona_name, persona_domain, initialized_at) VALUES (?, ?, ?, ?)",
                (agent_id, persona_name, persona_domain, initialized_at),
            )

    def list_posts(self, agent_id: str) -> list[dict[str, object]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, created_at, text, rationale, sources, topic_fingerprint FROM posts WHERE agent_id = ? ORDER BY created_at DESC",
                (agent_id,),
            ).fetchall()
        return [self._row_to_post(row) for row in rows]

    def recent_context(self, agent_id: str, days: int = 7) -> list[dict[str, str]]:
        cutoff = datetime_utc_days_ago(days)
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT topic_summary, reject_reason FROM rejected_topics WHERE agent_id = ? AND seen_at >= ? ORDER BY seen_at DESC",
                (agent_id, cutoff),
            ).fetchall()
        return [{"topicSummary": row["topic_summary"], "rejectReason": row["reject_reason"]} for row in rows]

    def recent_posts_context(self, agent_id: str, days: int = 7) -> list[dict[str, str]]:
        cutoff = datetime_utc_days_ago(days)
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT text, rationale FROM posts WHERE agent_id = ? AND created_at >= ? ORDER BY created_at DESC",
                (agent_id, cutoff),
            ).fetchall()
        return [{"text": row["text"], "rationale": row["rationale"]} for row in rows]

    def recent_fingerprints(self, agent_id: str, days: int = 7) -> set[str]:
        cutoff = datetime_utc_days_ago(days)
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT topic_fingerprint FROM posts WHERE agent_id = ? AND created_at >= ?",
                (agent_id, cutoff),
            ).fetchall()
        return {row["topic_fingerprint"] for row in rows}

    def recent_rejected_fingerprints(self, agent_id: str, days: int = 7) -> set[str]:
        cutoff = datetime_utc_days_ago(days)
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT topic_fingerprint FROM rejected_topics WHERE agent_id = ? AND seen_at >= ? AND topic_fingerprint IS NOT NULL",
                (agent_id, cutoff),
            ).fetchall()
        return {row["topic_fingerprint"] for row in rows}

    def recent_queued_fingerprints(self, agent_id: str) -> set[str]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT topic_fingerprint FROM queued_posts WHERE agent_id = ? AND topic_fingerprint IS NOT NULL",
                (agent_id,),
            ).fetchall()
        return {row["topic_fingerprint"] for row in rows}

    def enqueue_topic(self, agent_id: str, queue_id: str, queued_at: str, title: str, summary: str, source_name: str, source_urls: list[str], topic_fingerprint: str, decision_reason: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO queued_posts(id, agent_id, queued_at, title, summary, source_name, source_urls, topic_fingerprint, decision_reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (queue_id, agent_id, queued_at, title, summary, source_name, json.dumps(source_urls), topic_fingerprint, decision_reason),
            )

    def pop_queued_topic(self, agent_id: str) -> dict[str, object] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, queued_at, title, summary, source_name, source_urls, topic_fingerprint, decision_reason FROM queued_posts WHERE agent_id = ? ORDER BY queued_at ASC LIMIT 1",
                (agent_id,),
            ).fetchone()
            if not row:
                return None
            
            queue_id = row["id"]
            connection.execute("DELETE FROM queued_posts WHERE id = ?", (queue_id,))
            
            urls = row["source_urls"]
            if isinstance(urls, str):
                try:
                    urls = json.loads(urls)
                except Exception:
                    urls = [urls] if urls else []
            return {
                "id": row["id"],
                "title": row["title"],
                "summary": row["summary"],
                "source_name": row["source_name"],
                "source_urls": urls,
                "topic_fingerprint": row["topic_fingerprint"],
                "decision_reason": row["decision_reason"],
            }

    def queued_count(self, agent_id: str) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM queued_posts WHERE agent_id = ?", (agent_id,)).fetchone()
            return row[0] if row else 0

    def list_queued_topics(self, agent_id: str) -> list[dict[str, object]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, queued_at, title, summary, source_name, source_urls, topic_fingerprint, decision_reason FROM queued_posts WHERE agent_id = ? ORDER BY queued_at ASC",
                (agent_id,),
            ).fetchall()
        result = []
        for row in rows:
            urls = row["source_urls"]
            if isinstance(urls, str):
                try:
                    urls = json.loads(urls)
                except Exception:
                    urls = [urls] if urls else []
            result.append(
                {
                    "id": row["id"],
                    "queued_at": row["queued_at"],
                    "title": row["title"],
                    "summary": row["summary"],
                    "source_name": row["source_name"],
                    "source_urls": urls,
                    "topic_fingerprint": row["topic_fingerprint"],
                    "decision_reason": row["decision_reason"],
                }
            )
        return result

    def record_post(self, agent_id: str, post_id: str, created_at: str, text: str, rationale: str, sources: list[str], topic_fingerprint: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO posts(id, agent_id, created_at, text, rationale, sources, topic_fingerprint) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (post_id, agent_id, created_at, text, rationale, json.dumps(sources), topic_fingerprint),
            )

    def record_rejection(self, agent_id: str, rejection_id: str, seen_at: str, topic_summary: str, reject_reason: str, topic_fingerprint: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO rejected_topics(id, agent_id, seen_at, topic_summary, reject_reason, topic_fingerprint) VALUES (?, ?, ?, ?, ?, ?)",
                (rejection_id, agent_id, seen_at, topic_summary, reject_reason, topic_fingerprint),
            )

    def agent_exists(self, agent_id: str) -> bool:
        with self.connect() as connection:
            row = connection.execute("SELECT 1 FROM agent WHERE agent_id = ?", (agent_id,)).fetchone()
        return row is not None

    def get_latest_agent_id(self) -> str | None:
        with self.connect() as connection:
            row = connection.execute("SELECT agent_id FROM agent ORDER BY initialized_at DESC LIMIT 1").fetchone()
        return str(row["agent_id"]) if row else None


    def list_rejections(self, agent_id: str) -> list[dict[str, object]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT id, seen_at, topic_summary, reject_reason, topic_fingerprint FROM rejected_topics WHERE agent_id = ? AND reject_reason NOT LIKE '%evaluation error%' AND reject_reason NOT LIKE '%404%' ORDER BY seen_at DESC LIMIT 50",
                (agent_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "seen_at": row["seen_at"],
                "topic_summary": row["topic_summary"],
                "reject_reason": row["reject_reason"],
                "topic_fingerprint": row["topic_fingerprint"],
            }
            for row in rows
        ]

    def clear_rejections(self, agent_id: str) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM rejected_topics WHERE agent_id = ?", (agent_id,))



    @staticmethod
    def _row_to_post(row: sqlite3.Row) -> dict[str, object]:

        sources = row["sources"]
        if isinstance(sources, str):
            try:
                sources = json.loads(sources)
            except Exception:
                sources = [sources] if sources else []
        elif not isinstance(sources, list):
            sources = []

        return {
            "id": row["id"],
            "createdAt": row["created_at"],
            "created_at": row["created_at"],
            "text": row["text"],
            "rationale": row["rationale"],
            "sources": sources,
            "topic_fingerprint": row["topic_fingerprint"],
        }



def datetime_utc_days_ago(days: int) -> str:
    from datetime import datetime, timedelta, timezone

    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
