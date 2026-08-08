from __future__ import annotations

from pathlib import Path
import tempfile
from unittest.mock import patch

from fastapi.testclient import TestClient

import app.main as main
from app.db import Database
from app.llm import GeminiClient
from app.scheduler import AutonomousLoop
from app.sources import CandidateTopic


class DummyLoop:
    def __init__(self) -> None:
        self.active_agent_id: str | None = None
        self.tick_minutes: int = 45
        self.last_tick_time: str | None = None
        self.last_tick_status: str | None = None
        self.scheduler = None

    def ensure_started(self) -> None:
        return None

    def start(self, agent_id: str) -> None:
        self.active_agent_id = agent_id

    def update_interval(self, minutes: int) -> None:
        self.tick_minutes = minutes

    def get_next_run_time(self) -> str | None:
        return None



def test_init_and_feed_round_trip() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "vicodathon.db"
        original_database = main.database
        original_loop = main.autonomous_loop
        try:
            main.database = Database(db_path)
            main.autonomous_loop = DummyLoop()
            client = TestClient(main.app)

            # Test /api/agent/init endpoint
            init_response = client.post("/api/agent/init", json={"persona": {"name": "Vector", "domain": "AI Security Researcher"}})
            assert init_response.status_code == 200
            agent_id = init_response.json()["agentId"]
            assert agent_id

            # Test /api/agent/feed endpoint
            feed_response = client.get("/api/agent/feed", params={"agentId": agent_id})
            assert feed_response.status_code == 200
            assert feed_response.json() == {"posts": []}

            # Test /api/init legacy alias
            init_alias = client.post("/api/init", json={})
            assert init_alias.status_code == 200
            agent_id_2 = init_alias.json()["agentId"]

            # Test /api/feed legacy alias
            feed_alias = client.get("/api/feed", params={"agentId": agent_id_2})
            assert feed_alias.status_code == 200
            assert feed_alias.json() == {"posts": []}
        finally:
            main.database = original_database
            main.autonomous_loop = original_loop


def test_feed_unknown_agent_returns_404() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "vicodathon.db"
        original_database = main.database
        original_loop = main.autonomous_loop
        try:
            main.database = Database(db_path)
            main.autonomous_loop = DummyLoop()
            client = TestClient(main.app)

            response = client.get("/api/agent/feed", params={"agentId": "missing-id-12345"})
            assert response.status_code == 404
            assert response.json()["detail"] == "Unknown agent"
        finally:
            main.database = original_database
            main.autonomous_loop = original_loop


def test_feed_missing_agent_id_returns_404() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "vicodathon.db"
        original_database = main.database
        original_loop = main.autonomous_loop
        try:
            main.database = Database(db_path)
            main.autonomous_loop = DummyLoop()
            client = TestClient(main.app)

            response = client.get("/api/agent/feed")
            assert response.status_code == 404
        finally:
            main.database = original_database
            main.autonomous_loop = original_loop


def test_autonomous_loop_tick_creates_post() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "vicodathon.db"
        database = Database(db_path)
        gemini_client = GeminiClient(api_key=None)  # Local heuristic mode
        loop = AutonomousLoop(database=database, gemini_client=gemini_client)

        agent_id = "test-agent-uuid"
        database.create_agent(agent_id, "Vector", "AI Security Researcher", "2026-08-08T00:00:00Z")
        loop.active_agent_id = agent_id

        sample_candidates = [
            CandidateTopic(
                title="Critical AI LLM Sandbox Escape Exploit Discovered",
                summary="Researchers demonstrate zero-day prompt injection escaping model sandbox.",
                source_urls=["https://example.com/exploit"],
                source_name="arXiv",
            ),
            CandidateTopic(
                title="AI Startup Raises $50M Series A",
                summary="Company valuation surges in latest funding round.",
                source_urls=["https://example.com/hype"],
                source_name="TechCrunch",
            ),
        ]

        with patch("app.scheduler.discover_candidates", return_value=sample_candidates):
            loop.tick()

        posts = database.list_posts(agent_id)
        assert len(posts) == 1
        post = posts[0]
        assert "Sandbox Escape" in post["text"] or "Security" in post["text"] or "Critical" in post["text"]
        assert post["sources"] == ["https://example.com/exploit"]
        assert "rationale" in post
        assert "createdAt" in post
        assert "created_at" in post
        assert post["topic_fingerprint"]

