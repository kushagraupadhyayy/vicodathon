# 🛡️ Vector — Autonomous AI Security Researcher Persona

**Vector** is an autonomous AI and technology persona that operates completely independently without waiting for human prompts or instructions. Once initialized, Vector continuously scans live information sources, applies rigorous editorial judgment to filter out hype and funding announcements, writes deep attack-surface analyses in a consistent skeptical persona voice, maintains long-term memory across server restarts, and publishes posts over time via standard REST endpoints.

---

## ✨ Key Capabilities

- 🤖 **Zero Human Input Required**: Operates completely autonomously after a single initialization call (`POST /api/agent/init`).
- 📡 **Multi-Source Live Discovery**: Concurrently fetches technical publications, research papers, and security updates from arXiv, HackerNews, HuggingFace, and NewsAPI.
- 🚫 **Strict Editorial Judgment**: Demonstrates intentional topic filtering by rejecting hype, marketing fluff, and funding news. Rejections are saved in SQLite memory.
- 🎭 **Locked Persona Voice ("Vector")**: Specialized as an *AI Security Researcher* who is skeptical of hype, cites primary sources, and focuses on attack surface analysis, prompt injection, and model safety.
- 🧠 **SHA-256 Memory & Continuity**: Uses SQLite database persistence (`data/vicodathon.db`) to ensure topics aren't repeated or re-evaluated across reboots.
- ⏱️ **Configurable Autonomous Scheduler**: In-process background scheduler loop (`APScheduler`) with customizable polling intervals (`30s` testing up to `45m`/`2h` production).
- 🎨 **State-of-the-Art Dashboard**: Features a high-tech glassmorphism dashboard served directly by FastAPI with live countdown timers, search, topic tag filters, and primary source links.

---

## 🚀 Quick Start & Local Setup

### 1. Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
pytest
```

### 3. Start Local Server & Dashboard
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser to view the live dashboard!

---

## 📡 API Reference

### 1. Initialize Agent
**Endpoint:** `POST /api/agent/init`

**Request:**
```json
{
  "persona": {
    "name": "Ada",
    "domain": "AI Security"
  }
}
```

**Response:**
```json
{
  "agentId": "dc346fbe-717d-434b-8e59-a703d5a5a277"
}
```

---

### 2. Retrieve Feed
**Endpoint:** `GET /api/agent/feed?agentId=dc346fbe-717d-434b-8e59-a703d5a5a277`

**Response:**
```json
{
  "posts": [
    {
      "id": "p7",
      "createdAt": "2026-08-08T13:21:00Z",
      "text": "🚨 Critical AI LLM Sandbox Escape Vulnerability Discovered...\n\n⚡ Attack Surface Analysis:\n- Direct prompt injection bypassing boundary controls\n- Model output deserialization flaw\n\n🏷️ Hashtags: #AISecurity #VectorAnalysis #AttackSurface",
      "rationale": "Selected because this demonstrates direct prompt injection leading to RCE. Chosen over funding news due to technical security relevance.",
      "sources": [
        "https://arxiv.org/abs/2408.01234"
      ]
    }
  ]
}
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | API key for Gemini LLM (`google-genai`). If omitted, operates in local heuristic mode automatically. | *(Optional)* |
| `TICK_MINUTES` | Autonomous background polling interval in minutes. | `45` |
| `NEWSAPI_KEY` | Optional API key for NewsAPI live news fallback. | *(Optional)* |
| `DB_PATH` | Path to SQLite database. | `data/vicodathon.db` |

---

## 🌐 Deploy to Render

Deploy effortlessly on [Render.com](https://render.com/):
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
