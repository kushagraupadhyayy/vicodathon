from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import uuid

from apscheduler.schedulers.background import BackgroundScheduler

from app.db import Database
from app.llm import GeminiClient
from app.sources import CandidateTopic, discover_candidates

logger = logging.getLogger("autonomous_loop")

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
    "ai",
    "cyber",
    "malware",
    "jailbreak",
    "safety",
    "alignment",
    "zero-day",
    "backdoor",
    "breach",
    "adversarial",
    "sandbox",
    "privacy",
    "leak",
    "weight",
)


class AutonomousLoop:
    def __init__(
        self,
        database: Database,
        gemini_client: GeminiClient,
        tick_minutes: int = 45,
        newsapi_key: str | None = None,
    ) -> None:
        self.database = database
        self.gemini_client = gemini_client
        self.tick_minutes = tick_minutes
        self.newsapi_key = newsapi_key
        self.scheduler = BackgroundScheduler()
        self.active_agent_id: str | None = None
        self.last_tick_time: str | None = None
        self.last_tick_status: str | None = None

    def start(self, agent_id: str) -> None:
        self.active_agent_id = agent_id
        self.ensure_started()
        seconds = max(1, int(self.tick_minutes * 60))
        self.scheduler.add_job(
            self.tick,
            "interval",
            seconds=seconds,
            next_run_time=datetime.now(timezone.utc) + timedelta(seconds=seconds),
            id="autonomous-loop",
            replace_existing=True,
        )

    def ensure_started(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def get_next_run_time(self) -> str:
        if self.scheduler:
            job = self.scheduler.get_job("autonomous-loop")
            if job and job.next_run_time:
                return job.next_run_time.isoformat()
        seconds = max(1, int(self.tick_minutes * 60))
        return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()

    def update_interval(self, minutes: float) -> None:
        if minutes < 0.1:
            minutes = 0.5
        self.tick_minutes = minutes
        if self.active_agent_id:
            self.ensure_started()
            seconds = max(1, int(minutes * 60))
            self.scheduler.add_job(
                self.tick,
                "interval",
                seconds=seconds,
                next_run_time=datetime.now(timezone.utc) + timedelta(seconds=seconds),
                id="autonomous-loop",
                replace_existing=True,
            )



    def tick(self) -> None:
        if not self.active_agent_id:
            return

        now_str = datetime.now(timezone.utc).isoformat()
        self.last_tick_time = now_str

        try:
            # 1. Fill queue if queue count is below 2
            current_q_count = self.database.queued_count(self.active_agent_id)
            if current_q_count < 2:
                raw_candidates = discover_candidates(self.newsapi_key)
                candidates = self._cheap_filter(raw_candidates)
                print(f"[autonomous-loop] Queue low ({current_q_count}). Discovered {len(raw_candidates)} candidates, {len(candidates)} passed cheap filter.")

                recent_context = self._recent_context()
                recent_fingerprints = self.database.recent_fingerprints(self.active_agent_id)
                recent_rejected_fingerprints = self.database.recent_rejected_fingerprints(self.active_agent_id)
                recent_queued_fingerprints = self.database.recent_queued_fingerprints(self.active_agent_id)
                blocked_fingerprints = recent_fingerprints | recent_rejected_fingerprints | recent_queued_fingerprints

                for candidate in candidates:
                    if candidate.fingerprint in blocked_fingerprints:
                        continue

                    decision = self.gemini_client.judge(self._candidate_summary(candidate), recent_context)
                    if not decision.publish:
                        self._record_rejection(candidate, decision.reason)
                        blocked_fingerprints.add(candidate.fingerprint)
                        continue

                    # Queue approved topic for publication
                    self.database.enqueue_topic(
                        agent_id=self.active_agent_id,
                        queue_id=str(uuid.uuid4()),
                        queued_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        title=candidate.title,
                        summary=candidate.summary,
                        source_name=candidate.source_name,
                        source_urls=candidate.source_urls,
                        topic_fingerprint=candidate.fingerprint,
                        decision_reason=decision.reason,
                    )
                    blocked_fingerprints.add(candidate.fingerprint)

            # 2. Pop 1 topic from queue and publish it on this tick
            queued_item = self.database.pop_queued_topic(self.active_agent_id)
            if queued_item:
                candidate_summary = f"Title: {queued_item['title']}\nSummary: {queued_item['summary']}\nSource: {queued_item['source_name']}\nURLs: {', '.join(queued_item['source_urls'])}"
                
                candidate = CandidateTopic(
                    title=str(queued_item["title"]),
                    summary=str(queued_item["summary"]),
                    source_name=str(queued_item["source_name"]),
                    source_urls=list(queued_item["source_urls"]),
                )
                
                rejected_context = self._recent_rejected_summary()
                text, rationale = self.gemini_client.write_post(
                    candidate_summary, str(queued_item["decision_reason"]), rejected_context
                )
                self._store_post(candidate, text, rationale)
                remaining_q = self.database.queued_count(self.active_agent_id)
                self.last_tick_status = f"Success: Published 1 post from queue ({remaining_q} remaining in queue)."
                print(f"[autonomous-loop] Published queued post: '{candidate.title}' ({remaining_q} remaining in queue)")
            else:
                self.last_tick_status = "Idle: No approved topics in queue."

        except Exception as err:
            self.last_tick_status = f"Error: {err}"
            logger.error("Error in autonomous tick: %s", err, exc_info=True)

    def _recent_rejected_summary(self) -> str:
        if not self.active_agent_id:
            return "None rejected recently."
        recent_rejections = self.database.recent_context(self.active_agent_id)
        if not recent_rejections:
            return "None rejected recently."
        return "\n".join(f"- {item['topicSummary']}: {item['rejectReason']}" for item in recent_rejections[:10])



    def _cheap_filter(self, candidates: list[CandidateTopic]) -> list[CandidateTopic]:
        filtered: list[CandidateTopic] = []
        for candidate in candidates:
            haystack = f"{candidate.title} {candidate.summary}".lower()
            if any(keyword in haystack for keyword in KEYWORDS):
                filtered.append(candidate)
        return filtered

    def _candidate_summary(self, candidate: CandidateTopic) -> str:
        source_urls = ", ".join(candidate.source_urls) if candidate.source_urls else "No source URL provided"
        return f"Title: {candidate.title}\nSummary: {candidate.summary}\nSource: {candidate.source_name}\nURLs: {source_urls}"

    def _recent_context(self) -> str:
        if not self.active_agent_id:
            return "No recent context yet."
        recent_posts = self.database.recent_posts_context(self.active_agent_id)
        recent_rejections = self.database.recent_context(self.active_agent_id)
        if not recent_posts and not recent_rejections:
            return "No recent context yet."

        recent_posts_block = "\n".join(f"- {item['text']} :: {item['rationale']}" for item in recent_posts[:15]) or "None"
        recent_rejections_block = "\n".join(
            f"- {item['topicSummary']}: {item['rejectReason']}" for item in recent_rejections[:15]
        ) or "None"
        return f"Published recently:\n{recent_posts_block}\n\nRejected recently:\n{recent_rejections_block}"

    def _rejected_rollup(self, rejected: list[tuple[CandidateTopic, str]]) -> str:
        if not rejected:
            return "None rejected this cycle."
        return "\n".join(f"- {candidate.title}: {reason}" for candidate, reason in rejected[:10])

    def _store_post(self, candidate: CandidateTopic, text: str, rationale: str) -> None:
        if not self.active_agent_id:
            return
        self.database.record_post(
            agent_id=self.active_agent_id,
            post_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
            seen_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            topic_summary=self._candidate_summary(candidate),
            reject_reason=reason,
            topic_fingerprint=candidate.fingerprint,
        )

