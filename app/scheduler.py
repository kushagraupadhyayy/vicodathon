from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid

from apscheduler.schedulers.background import BackgroundScheduler

from app.db import Database
from app.llm import GeminiClient
from app.sources import CandidateTopic, discover_candidates


KEYWORDS = (
    "security",
    "vulnerability",
    "attack",
    "exploit",
    "prompt injection",
    "llm",
    "model",
    "agent",
    "arxiv",
    "ransomware",
)


class AutonomousLoop:
    def __init__(self, database: Database, gemini_client: GeminiClient, tick_minutes: int = 60, newsapi_key: str | None = None) -> None:
        self.database = database
        self.gemini_client = gemini_client
        self.tick_minutes = tick_minutes
        self.newsapi_key = newsapi_key
        self.scheduler = BackgroundScheduler()
        self.active_agent_id: str | None = None

    def start(self, agent_id: str) -> None:
        self.active_agent_id = agent_id
        if not self.scheduler.get_job("autonomous-loop"):
            self.scheduler.add_job(self.tick, "interval", minutes=self.tick_minutes, id="autonomous-loop", replace_existing=True)

    def ensure_started(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def tick(self) -> None:
        if not self.active_agent_id:
            return
        candidates = self._cheap_filter(discover_candidates(self.newsapi_key))
        for candidate in candidates:
            print(f"[autonomous-loop] candidate: {candidate.title} ({candidate.source_name})")
        recent_context = self._recent_context()
        recent_fingerprints = self.database.recent_fingerprints(self.active_agent_id)
        recent_rejected_fingerprints = self.database.recent_rejected_fingerprints(self.active_agent_id)
        blocked_fingerprints = recent_fingerprints | recent_rejected_fingerprints
        rejected: list[tuple[CandidateTopic, str]] = []
        approved: list[tuple[CandidateTopic, str]] = []
        for candidate in candidates:
            if candidate.fingerprint in blocked_fingerprints:
                rejected.append((candidate, "duplicate or recently rejected"))
                self._record_rejection(candidate, "duplicate or recently rejected")
                continue
            decision = self.gemini_client.judge(self._candidate_summary(candidate), recent_context)
            if not decision.publish:
                rejected.append((candidate, decision.reason))
                self._record_rejection(candidate, decision.reason)
                continue
            approved.append((candidate, decision.reason))

        rejected_rollup = self._rejected_rollup(rejected)
        for candidate, decision_reason in approved:
            text, rationale = self.gemini_client.write_post(
                self._candidate_summary(candidate), decision_reason, rejected_rollup
            )
            self._store_post(candidate, text, rationale)

    def _cheap_filter(self, candidates: list[CandidateTopic]) -> list[CandidateTopic]:
        filtered: list[CandidateTopic] = []
        for candidate in candidates:
            haystack = f"{candidate.title} {candidate.summary}".lower()
            if any(keyword in haystack for keyword in KEYWORDS):
                filtered.append(candidate)
        return filtered

    def _candidate_summary(self, candidate: CandidateTopic) -> str:
        source_urls = ", ".join(candidate.source_urls) if candidate.source_urls else "no source url"
        return f"Title: {candidate.title}\nSummary: {candidate.summary}\nSource: {candidate.source_name}\nURLs: {source_urls}"

    def _recent_context(self) -> str:
        if not self.active_agent_id:
            return "No recent context yet."
        recent_posts = self.database.recent_posts_context(self.active_agent_id)
        recent_rejections = self.database.recent_context(self.active_agent_id)
        if not recent_posts and not recent_rejections:
            return "No recent context yet."
        recent_posts_block = "\n".join(f"- {item['text']} :: {item['rationale']}" for item in recent_posts[:25]) or "None"
        recent_rejections_block = "\n".join(
            f"- {item['topicSummary']}: {item['rejectReason']}" for item in recent_rejections[:25]
        ) or "None"
        return f"Published recently:\n{recent_posts_block}\n\nRejected recently:\n{recent_rejections_block}"

    def _rejected_rollup(self, rejected: list[tuple[CandidateTopic, str]]) -> str:
        if not rejected:
            return "None"
        return "\n".join(f"- {candidate.title}: {reason}" for candidate, reason in rejected)

    def _store_post(self, candidate: CandidateTopic, text: str, rationale: str) -> None:
        if not self.active_agent_id:
            return
        self.database.record_post(
            agent_id=self.active_agent_id,
            post_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            text=text,
            rationale=rationale,
            sources=candidate.source_urls,
            topic_fingerprint=candidate.fingerprint,
        )

    def _record_rejection(self, candidate: CandidateTopic, reason: str) -> None:
        if not self.active_agent_id:
            return
        self.database.record_rejection(
            agent_id=self.active_agent_id,
            rejection_id=str(uuid.uuid4()),
            seen_at=datetime.now(timezone.utc).isoformat(),
            topic_summary=self._candidate_summary(candidate),
            reject_reason=reason,
                topic_fingerprint=candidate.fingerprint,
        )
