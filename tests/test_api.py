from __future__ import annotations

from pathlib import Path
import tempfile

from fastapi.testclient import TestClient

import app.main as main
from app.db import Database


class DummyLoop:
    def ensure_started(self) -> None:
        return None

    def start(self, agent_id: str) -> None:
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

            init_response = client.post("/api/agent/init", json={"persona": {"name": "Vector", "domain": "AI Security Researcher"}})
            assert init_response.status_code == 200
            agent_id = init_response.json()["agentId"]

            feed_response = client.get("/api/agent/feed", params={"agentId": agent_id})
            assert feed_response.status_code == 200
            assert feed_response.json() == {"posts": []}
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

            response = client.get("/api/agent/feed", params={"agentId": "missing"})
            assert response.status_code == 404
        finally:
            main.database = original_database
            main.autonomous_loop = original_loop
