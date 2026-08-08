from __future__ import annotations

import json
from dataclasses import dataclass

from app.persona import PERSONA_SYSTEM_PROMPT


@dataclass(frozen=True)
class EditorialDecision:
    publish: bool
    reason: str


class GeminiClient:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key
        self._client = None
        if api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=api_key)
            except Exception:
                self._client = None

    def judge(self, candidate_summary: str, recent_context: str) -> EditorialDecision:
        if self._client is None:
            publish = "security" in candidate_summary.lower() or "vulnerability" in candidate_summary.lower()
            reason = "Local heuristic fallback because Gemini is unavailable."
            return EditorialDecision(publish=publish, reason=reason)

        prompt = (
            f"{PERSONA_SYSTEM_PROMPT}\n\n"
            "You are deciding whether to publish a topic. Output only JSON.\n"
            f"Recent context:\n{recent_context}\n\n"
            f"Candidate topic:\n{candidate_summary}\n\n"
            '{"publish": true, "reason": "..."}'
        )
        response = self._client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)
        return EditorialDecision(publish=bool(data.get("publish")), reason=str(data.get("reason", "")))

    def write_post(self, candidate_summary: str, decision_reason: str, chosen_over: str) -> tuple[str, str]:
        if self._client is None:
            text = f"{candidate_summary}\n\nWhat matters here: {decision_reason}"
            rationale = f"Selected because it clears the security bar. Chosen over: {chosen_over}"
            return text, rationale

        prompt = (
            f"{PERSONA_SYSTEM_PROMPT}\n\n"
            "Write a concise post and rationale. Output only JSON.\n"
            f"Candidate topic:\n{candidate_summary}\n\n"
            f"Why selected:\n{decision_reason}\n\n"
            f"Chosen over:\n{chosen_over}\n\n"
            '{"text": "...", "rationale": "..."}'
        )
        response = self._client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        data = json.loads(response.text)
        return str(data.get("text", "")), str(data.get("rationale", ""))
