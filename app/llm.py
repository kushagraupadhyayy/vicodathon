from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.persona import PERSONA_SYSTEM_PROMPT


@dataclass(frozen=True)
class EditorialDecision:
    publish: bool
    reason: str


def _clean_json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


import html

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

    def _generate_json(self, prompt: str) -> dict[str, object]:
        if not self._client:
            raise RuntimeError("Gemini client not initialized")
        
        models_to_try = [
            "gemini-2.0-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
        ]
        last_err = None
        for model in models_to_try:
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                )
                raw_text = response.text or ""
                return json.loads(_clean_json_text(raw_text))
            except Exception as err:
                last_err = err
                continue
        raise last_err or RuntimeError("Failed to generate content with Gemini models")

    def _heuristic_judge(self, candidate_summary: str) -> EditorialDecision:
        lower = candidate_summary.lower()
        security_keywords = ("security", "vulnerability", "attack", "exploit", "injection", "jailbreak", "adversarial", "sandbox", "risk", "threat", "cve")
        hype_keywords = ("valuation", "funding", "hiring", "raised", "sponsor", "stock", "market cap")
        has_sec = any(k in lower for k in security_keywords)
        has_hype = any(k in lower for k in hype_keywords)
        publish = has_sec and not has_hype
        reason = (
            "Approved: technical security focus clearing Vector's standards."
            if publish
            else "Rejected: generic hype, non-security topic, or marketing."
        )
        return EditorialDecision(publish=publish, reason=reason)

    def _heuristic_write_post(self, candidate_summary: str, decision_reason: str, chosen_over: str) -> tuple[str, str]:
        title_match = re.search(r"Title:\s*(.*?)(?:\n|$)", candidate_summary)
        raw_title = title_match.group(1).strip() if title_match else "AI Security Research Update"
        clean_title = html.unescape(re.sub(r"^(Title:\s*|The Download:\s*|\s*)", "", raw_title, flags=re.IGNORECASE))

        lower = candidate_summary.lower()
        tags = ["#AISecurity", "#VectorAnalysis"]
        if "exploit" in lower or "attack" in lower or "cyber" in lower:
            tags.append("#AttackSurface")
        if "vulnerability" in lower or "sandbox" in lower:
            tags.append("#ModelSecurity")
        if "injection" in lower or "jailbreak" in lower:
            tags.append("#PromptInjection")
        if "paper" in lower or "arxiv" in lower:
            tags.append("#AIResearch")
        if "reward" in lower or "hacking" in lower or "rlhf" in lower:
            tags.append("#RLHF")
        tag_str = " ".join(tags)

        text = (
            f"🚨 {clean_title}\n\n"
            f"Vector's Technical Analysis:\n"
            f"Recent security dispatches and research disclosures highlight critical vulnerabilities in modern AI systems. "
            f"While general headlines focus on hype or corporate announcements, our primary analysis remains focused strictly on attack surface exposures and verified system impact.\n\n"
            f"🔍 Threat Context & Primary Impact:\n"
            f"• {decision_reason}\n"
            f"• Analysis indicates execution risks where model outputs interface directly with untrusted data inputs.\n"
            f"• Exploitation vectors can lead to context poisoning, data exfiltration, or boundary escalation in connected AI agents.\n\n"
            f"⚡ Attack Surface & Recommended Defense:\n"
            f"• Enforce strict privilege separation between agent reasoning modules and downstream OS/API execution.\n"
            f"• Implement deterministic schema validation and sanitization on all LLM tool calls before invocation.\n"
            f"• Audit prompt boundaries and establish isolated sandboxes for external data ingestion.\n\n"
            f"🏷️ {tag_str}"
        )

        rejected_snippet = chosen_over[:300] + "..." if len(chosen_over) > 300 else chosen_over
        rationale = (
            f"Selected '{clean_title}' due to direct, actionable technical security implications.\n\n"
            f"Why relevant now: Addresses immediate attack surface vulnerabilities in production AI agent architectures.\n\n"
            f"Comparative Choice over rejected topics from this cycle:\n{rejected_snippet}"
        )
        return text, rationale

    def judge(self, candidate_summary: str, recent_context: str) -> EditorialDecision:
        if self._client is None:
            return self._heuristic_judge(candidate_summary)

        prompt = (
            f"{PERSONA_SYSTEM_PROMPT}\n\n"
            "You are evaluating a candidate AI news topic for publication.\n"
            "Decision Rule: Only publish if it has direct security implications, model vulnerabilities, "
            "attack surface changes, or primary technical research. Reject hype, fundraising, or pure marketing.\n\n"
            f"Recent Context (Past coverage & rejections):\n{recent_context}\n\n"
            f"Candidate Topic:\n{candidate_summary}\n\n"
            "Return valid JSON matching strictly:\n"
            '{"publish": boolean, "reason": "Detailed string explaining why approved or rejected"}'
        )
        try:
            data = self._generate_json(prompt)
            return EditorialDecision(publish=bool(data.get("publish")), reason=str(data.get("reason", "No reason provided")))
        except Exception:
            return self._heuristic_judge(candidate_summary)

    def write_post(self, candidate_summary: str, decision_reason: str, chosen_over: str) -> tuple[str, str]:
        if self._client is None:
            return self._heuristic_write_post(candidate_summary, decision_reason, chosen_over)

        prompt = (
            f"{PERSONA_SYSTEM_PROMPT}\n\n"
            "Write a detailed, multi-paragraph, high-quality technical security post in Vector's voice "
            "(skeptical of hype, cites primary sources, punchy analytical sentences, always asks 'what's the attack surface here').\n\n"
            "Formatting Rules for post 'text':\n"
            "1. Start with a clean headline emoji & unescaped title (e.g. 🚨 Title Here).\n"
            "2. Provide 2-3 analytical introductory paragraphs detailing technical context.\n"
            "3. Include a '🔍 Threat Context & Primary Impact:' section with 2-3 detailed bullet points.\n"
            "4. Include a '⚡ Attack Surface & Recommended Defense:' section with 3 actionable bullet points.\n"
            "5. Include a '🏷️ Hashtags:' line with 3-4 relevant tags (e.g. #AISecurity #AttackSurface #AIResearch).\n\n"
            "Formatting Rules for 'rationale':\n"
            "1. Explain why this topic was selected and why it is relevant right now.\n"
            "2. Explicitly compare it against the rejected candidates from this cycle.\n\n"
            f"Approved Topic:\n{candidate_summary}\n\n"
            f"Selection Reason:\n{decision_reason}\n\n"
            f"Rejected Candidates This Cycle:\n{chosen_over}\n\n"
            "Return valid JSON strictly matching:\n"
            '{"text": "Detailed post text formatted with sections and hashtags", "rationale": "Detailed rationale explaining why selected, why relevant now, and comparison with rejected topics"}'
        )
        try:
            data = self._generate_json(prompt)
            post_text = str(data.get("text", "")).strip()
            rationale_text = str(data.get("rationale", "")).strip()
            if not post_text:
                post_text, rationale_text = self._heuristic_write_post(candidate_summary, decision_reason, chosen_over)
            if not rationale_text:
                rationale_text = f"Selected for security relevance: {decision_reason}"
            return post_text, rationale_text
        except Exception:
            return self._heuristic_write_post(candidate_summary, decision_reason, chosen_over)


