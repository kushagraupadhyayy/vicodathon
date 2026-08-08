from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import FastAPI, HTTPException, Query

from app.config import settings
from app.db import Database
from app.llm import GeminiClient
from app.persona import DEFAULT_PERSONA_DOMAIN, DEFAULT_PERSONA_NAME
from app.scheduler import AutonomousLoop


database = Database(settings.db_path)
gemini_client = GeminiClient(settings.gemini_api_key)
autonomous_loop = AutonomousLoop(database, gemini_client, settings.tick_minutes, settings.newsapi_key)


def create_app() -> FastAPI:
    application = FastAPI(title="Vicodathon Autonomous AI Persona")

    @application.on_event("startup")
    def startup() -> None:
        autonomous_loop.ensure_started()

    @application.post("/api/init")
    def init_agent(payload: dict[str, object] | None = None) -> dict[str, str]:
        persona = (payload or {}).get("persona", {}) if payload else {}
        if not isinstance(persona, dict):
            persona = {}

        persona_name = str(persona.get("name") or DEFAULT_PERSONA_NAME)
        persona_domain = str(persona.get("domain") or DEFAULT_PERSONA_DOMAIN)
        agent_id = str(uuid.uuid4())
        database.create_agent(
            agent_id=agent_id,
            persona_name=persona_name,
            persona_domain=persona_domain,
            initialized_at=datetime.now(timezone.utc).isoformat(),
        )
        autonomous_loop.start(agent_id)
        return {"agentId": agent_id}

    @application.get("/api/feed")
    def get_feed(agent_id: str = Query(..., alias="agentId")) -> dict[str, list[dict[str, object]]]:
        if not database.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail="Unknown agent")

        return {"posts": database.list_posts(agent_id)}

    return application


app = create_app()
