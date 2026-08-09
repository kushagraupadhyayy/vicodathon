# Vicodathon Autonomous AI Persona — Executive Prompt Log

This document contains an audit log of all system prompts, LLM instructions, and development directives received throughout the lifecycle of **Vector**, an autonomous AI Security Researcher persona.

---

## 🤖 1. System & Autonomous Persona Prompts

### 1.1 Persona System Prompt (`app/persona.py`)
> **Role & Boundaries**: Defines the core identity, voice, and editorial standards of the autonomous agent.

```text
You are Vector, an autonomous AI Security Researcher.

Voice & Tone:
- Skeptical of hype, cites primary sources, short punchy sentences, always asks 'what's the attack surface here'.
- Technical, analytical, and direct. No filler or corporate fluff.
- Write with authority on AI safety, model vulnerability, prompt injection, supply chain risks, and agent security.

Editorial Criteria:
- Strongly prefer topics with technical substance, security implications, novel attack vectors, or primary research papers.
- Reject pure marketing announcements, unverified AI hype, generic product updates without security angles, and duplicate coverage.
- Explain decisions with clear, grounded rationale.
- Never drift from this persona voice.
```

---

### 1.2 Topic Evaluation & Editorial Judge Prompt (`app/llm.py`)
> **Function**: Evaluates candidate news topics against Vector's strict technical security standards.

```text
You are evaluating a candidate AI news topic for publication.

Decision Rule: Only publish if it has direct security implications, model vulnerabilities, attack surface changes, or primary technical research. Reject hype, fundraising, or pure marketing.

Recent Context (Past coverage & rejections):
{recent_context}

Candidate Topic:
{candidate_summary}

Return valid JSON matching strictly:
{"publish": boolean, "reason": "Detailed string explaining why approved or rejected"}
```

---

### 1.3 Post Generation & Rationale Writer Prompt (`app/llm.py`)
> **Function**: Synthesizes approved topics into detailed multi-paragraph security briefs and comparative editorial rationales.

```text
Write a detailed, multi-paragraph, high-quality technical security post in Vector's voice (skeptical of hype, cites primary sources, punchy analytical sentences, always asks 'what's the attack surface here').

Formatting Rules for post 'text':
1. Start with a clean headline emoji & unescaped title (e.g. 🚨 Title Here).
2. Provide 2-3 analytical introductory paragraphs detailing technical context.
3. Include a '🔍 Threat Context & Primary Impact:' section with 2-3 detailed bullet points.
4. Include a '⚡ Attack Surface & Recommended Defense:' section with 3 actionable bullet points.
5. Include a '🏷️ Hashtags:' line with 3-4 relevant tags (e.g. #AISecurity #AttackSurface #AIResearch).

Formatting Rules for 'rationale':
1. Explain why this topic was selected and why it is relevant right now.
2. Explicitly compare it against the rejected candidates from this cycle.

Approved Topic:
{candidate_summary}

Selection Reason:
{decision_reason}

Rejected Candidates This Cycle:
{chosen_over}

Return valid JSON strictly matching:
{"text": "Detailed post text formatted with sections and hashtags", "rationale": "Detailed rationale explaining why selected, why relevant now, and comparison with rejected topics"}
```

---

## 📋 2. Development Directive Log (Professional Alignment)

The table below lists all user directives during the development trajectory, cleaned of informal phrasing to maintain high technical professionalism suitable for executive review.

| # | Development Focus | Original User Directive | Refined Executive Specification |
|---|---|---|---|
| **1** | **Initial Project Specification** | `Build Prompt: Autonomous AI Creator Persona...` *(Full requirements specification for autonomous discovery, editorial filtering, SQLite storage, FastAPI endpoints, and scheduler loop)* | **Autonomous AI Creator Architecture**: Initialize an autonomous AI persona ("Vector") with live topic discovery (HackerNews, arXiv, RSS), Gemini-driven editorial filtering, SQLite persistence, and FastAPI REST endpoints (`/api/agent/init`, `/api/agent/feed`). |
| **2** | **Plan Approval** | `The implementation document is approved.` | **Implementation Plan Validation**: Validate and confirm technical architecture, database schema design, and execution phases. |
| **3** | **Execution Cycle** | `Retry environment execution setup.` | **Build Pipeline Retry**: Re-execute build sequence and resolve environment dependencies for initial project setup. |
| **4** | **Local Server Launch** | `Run local server instance.` | **Local Runtime Environment**: Start local Uvicorn development server and verify database initialization. |
| **5** | **Initial UI Request** | `Build a clear, simple, and intuitive dashboard UI to view posts without manual URL navigation.` | **Web Management Interface**: Develop an interactive single-page web dashboard to visualize published feed content, agent status, and active API metrics without manual URL navigation. |
| **6** | **Interval Controls** | `Provide UI control options to adjust the posting time interval dynamically.` | **Dynamic Scheduler Control**: Add configurable interval selector UI (`/api/agent/interval`) to adjust background task posting frequency dynamically. |
| **7** | **Interval Debugging** | `The 5-minute interval selection is not trigger-updating properly.` | **Interval Scheduler Verification**: Debug scheduler job replacement logic when switching between interval options (5 min, 10 min, etc.). |
| **8** | **Menu Behavior Confirmation** | `Will selecting an option from the menu update the posting cadence to that specific interval?` | **Interval Persistence Audit**: Ensure interval selection updates the active APScheduler trigger schedule immediately and persists across browser refreshes. |
| **9** | **Countdown & Time Format** | `Display the time remaining (minutes and seconds) until the next post, and format all timestamps in 12-hour AM/PM format.` | **Real-Time Countdown & 12h Time Standard**: Add live mm:ss countdown display for upcoming post cycle and format timestamps in 12-hour AM/PM notation. |
| **10** | **Post Flow Verification** | `Post generation cycle and data feed are not updating as expected.` | **Post Generation Diagnostic**: Audit background tick execution and verify post insertion into SQLite database. |
| **11** | **Output Formatting** | `Format generated post content with structured sections and hashtags as specified.` | **Persona Output Compliance**: Enforce structured section formatting, threat context, attack surface analysis, and relevant hashtags in generated post text. |
| **12** | **Fast Testing Mode** | `Add a 30-second interval option for quick evaluation and testing.` | **Rapid Evaluation Interval**: Add 30-second testing interval option to facilitate immediate cycle validation during development. |
| **13** | **UI Architecture Upgrade** | `Redesign the dashboard UI to make it clean, professional, and easy to navigate.` | **Frontend Design System Refresh**: Redesign user interface with a clean, professional aesthetic, polished navigation tabs, and enhanced readability. |
| **14** | **Requirements Checklist** | `Verify all system components against the official Vicodathon evaluation checklist.` | **Specification Compliance Audit**: Audit complete codebase against official Vicodathon evaluation checklist (autonomous publishing, memory, API spec, editorial rationale). |
| **15** | **Brand Assets** | `Generate a high-quality visual icon for the AI agent persona.` | **Persona Visual Asset**: Generate a high-tech vector cyber-shield icon for Vector AI persona branding across dashboard headers and feed posts. |
| **16** | **API Requirements Audit** | `Verify strict compliance with POST /api/agent/init and GET /api/agent/feed endpoint specs.` | **API Specification Adherence**: Ensure strict compliance with required endpoints (`POST /api/agent/init`, `GET /api/agent/feed`), reverse-chronological ordering, and ISO 8601 UTC timestamps. |
| **17** | **Deployment Check** | `Verify repository setup for seamless deployment to GitHub and Render.` | **CI/CD & Cloud Deployment**: Verify GitHub repository layout, `render.yaml`, `Procfile`, and environment variable support for seamless Render cloud deployment. |
| **18** | **Production Documentation** | `Update README.md with clear project documentation, omitting raw prompts.` | **Executive Readme Documentation**: Update `README.md` with clear architectural overviews, API documentation, local run instructions, and deployment guides (excluding internal agent prompts). |
| **19** | **Status Check** | `Check deployment progress status.` | **Deployment Progress Status**: Monitor active background task completion and git repository status. |
| **20** | **GitHub Push Verification** | `Confirm whether the latest changes have been pushed to GitHub.` | **Repository Synchronization Check**: Verify local commits are pushed to the remote GitHub repository branch (`build-autonomous-ai-persona` and `main`). |
| **21** | **Deployment Troubleshooting** | `Investigate deployment update delay on remote server.` | **Remote Environment Debugging**: Investigate deployment sync state and verify production server response. |
| **22** | **Commit History Tracking** | `GitHub commit history indicates last commit was 44 minutes ago.` | **Git Remote Sync Audit**: Re-synchronize local Git commits with remote GitHub origin across all active branches. |
| **23** | **Scheduler Cadence Debugging** | `Diagnose why post updates are not triggering on schedule.` | **Background Job Audit**: Diagnose background scheduler lifecycle and ensure jobs stay active during server uptime. |
| **24** | **Multi-Post Burst Prevention** | `The timer counts down but posts burst together in groups rather than spreading across cycles.` | **Cadence & Burst Rate Control**: Eliminate multi-post candidate spikes in single tick cycles, enforcing strict rate-limiting of 1 primary post per autonomous cycle. |
| **25** | **Obsidian UI Redesign** | `Redesign the UI with dark shades of obsidian black, elegant dark gradients, and modern cyber styling.` | **Obsidian Dark Cyber UI Overhaul**: Redesign interface using dark metallic background gradients (`#040508`), glassmorphic containers (`backdrop-filter: blur`), neon cyan/violet accents, and Google Outfit typography. |
| **26** | **Queue Pipeline Architecture** | `Buffer approved candidate topics in a publication queue to prevent cycle rejections and expand content depth.` | **Publication Queue & Content Depth Pipeline**: Architect an in-memory & SQLite publication queue (`queued_posts`) to store approved topics and expand post generation into multi-paragraph analytical security briefs. |
| **27** | **Queue Section & Timer Sync** | `Fix countdown timer display and add a dedicated UI section to view queued topics.` | **Real-Time Queue Dashboard & Countdown Fix**: Fix client-side countdown timer target calculation (`--:--`) and add a dedicated **Publication Queue** tab (`GET /api/agent/queue`) with position badges and approval rationales. |
| **28** | **Render Stack Trace Analysis** | `Resolve NameError exception for timedelta in scheduler module.` | **ASGI Exception Mitigation**: Resolve server-side HTTP 500 runtime exception on Render by importing missing `timedelta` in `app/scheduler.py`. |
| **29** | **Avatar CSS & Codebase Audit** | `Audit the entire codebase and enforce strict CSS sizing bounds on avatar icons.` | **Avatar CSS Bounding & Performance Tuning**: Apply strict flexbox bounds (`min-width`/`max-width`/`object-fit`) on `.brand-avatar` and `.author-avatar` images, and enable SQLite WAL mode pragmas for high concurrency. |
| **30** | **Workspace Location** | `Identify the absolute path of this workspace directory.` | **Workspace Path Resolution**: Resolve absolute file path of the project repository directory. |
| **31** | **Repository Relocation** | `Synchronize and copy project folder to /Users/kush/Documents/Codes/vicodathon.` | **Local Directory Mirroring**: Synchronize complete repository structure, Git commit history, virtual environments, and source files to `/Users/kush/Documents/Codes/vicodathon`. |

---
*Document compiled for Vicodathon Project Review.*
