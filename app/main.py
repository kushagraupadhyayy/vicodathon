from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
import uuid

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import Database
from app.llm import GeminiClient
from app.persona import DEFAULT_PERSONA_DOMAIN, DEFAULT_PERSONA_NAME
from app.scheduler import AutonomousLoop


database = Database(settings.db_path)
gemini_client = GeminiClient(settings.gemini_api_key)
autonomous_loop = AutonomousLoop(database, gemini_client, settings.tick_minutes, settings.newsapi_key)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)



INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vector // Autonomous AI Security Researcher</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #080c14;
      --bg-card: rgba(15, 23, 42, 0.75);
      --bg-card-hover: rgba(26, 36, 60, 0.85);
      --border-color: rgba(99, 102, 241, 0.16);
      --border-accent: rgba(6, 182, 212, 0.4);
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-cyan: #06b6d4;
      --accent-violet: #8b5cf6;
      --accent-emerald: #10b981;
      --accent-rose: #f43f5e;
      --accent-amber: #f59e0b;
      --radius-xl: 20px;
      --radius-lg: 14px;
      --radius-md: 10px;
      --shadow-main: 0 10px 40px -10px rgba(0, 0, 0, 0.5);
      --shadow-glow: 0 0 30px rgba(6, 182, 212, 0.12);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg-dark);
      background-image: 
        radial-gradient(circle at 10% 10%, rgba(139, 92, 246, 0.12), transparent 40%),
        radial-gradient(circle at 90% 90%, rgba(6, 182, 212, 0.12), transparent 40%),
        radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.05), transparent 50%);
      color: var(--text-primary);
      min-height: 100vh;
      line-height: 1.6;
      padding-bottom: 80px;
    }

    .container {
      max-width: 1140px;
      margin: 0 auto;
      padding: 32px 24px;
    }

    /* Top Navigation Bar */
    .nav-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      backdrop-filter: blur(16px);
      margin-bottom: 32px;
      box-shadow: var(--shadow-main);
      flex-wrap: wrap;
      gap: 16px;
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    .brand-avatar {
      width: 46px;
      height: 46px;
      border-radius: 12px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: 'Outfit', sans-serif;
      font-weight: 800;
      font-size: 22px;
      color: #ffffff;
      box-shadow: 0 0 20px rgba(6, 182, 212, 0.4);
      border: 1px solid rgba(255,255,255,0.2);
    }

    .brand-title-group h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 22px;
      font-weight: 800;
      letter-spacing: -0.3px;
      background: linear-gradient(to right, #ffffff, #cbd5e1);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .brand-title-group p {
      font-size: 13px;
      color: var(--text-secondary);
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .badge-status {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(16, 185, 129, 0.12);
      color: var(--accent-emerald);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 2px 10px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 600;
    }

    .pulse-dot {
      width: 6px;
      height: 6px;
      background: var(--accent-emerald);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--accent-emerald);
      animation: pulse 1.8s infinite;
    }

    @keyframes pulse {
      0% { opacity: 0.4; transform: scale(0.9); }
      50% { opacity: 1; transform: scale(1.3); }
      100% { opacity: 0.4; transform: scale(0.9); }
    }

    .nav-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    .btn {
      font-family: 'Inter', sans-serif;
      font-size: 13px;
      font-weight: 600;
      padding: 9px 16px;
      border-radius: var(--radius-md);
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      text-decoration: none;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--accent-violet), #6366f1);
      color: white;
      box-shadow: 0 4px 14px rgba(139, 92, 246, 0.35);
    }

    .btn-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 6px 18px rgba(139, 92, 246, 0.5);
    }

    .btn-secondary {
      background: rgba(30, 41, 59, 0.6);
      color: var(--text-primary);
      border-color: var(--border-color);
    }

    .btn-secondary:hover {
      background: rgba(51, 65, 85, 0.8);
      border-color: var(--accent-cyan);
    }

    /* Summary Metrics Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }

    .metric-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 18px 20px;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.2s ease;
    }

    .metric-card:hover {
      border-color: var(--border-accent);
      box-shadow: var(--shadow-glow);
    }

    .metric-label {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--text-muted);
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .metric-value {
      font-family: 'Outfit', sans-serif;
      font-size: 26px;
      font-weight: 700;
      color: var(--text-primary);
    }

    .metric-subtext {
      font-size: 12px;
      color: var(--text-secondary);
      margin-top: 4px;
    }

    .select-interval {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--border-accent);
      color: var(--accent-cyan);
      font-family: 'Inter', sans-serif;
      font-size: 13px;
      font-weight: 600;
      padding: 6px 12px;
      border-radius: 8px;
      cursor: pointer;
      outline: none;
      width: 100%;
      margin-top: 6px;
    }

    /* Filter & Search Bar */
    .filter-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 12px 18px;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 12px;
    }

    .search-box {
      display: flex;
      align-items: center;
      gap: 10px;
      background: rgba(9, 13, 22, 0.6);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 8px 14px;
      flex: 1;
      min-width: 250px;
    }

    .search-box input {
      background: none;
      border: none;
      color: var(--text-primary);
      font-size: 14px;
      outline: none;
      width: 100%;
    }

    .search-box input::placeholder { color: var(--text-muted); }

    .tag-pills {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }

    .tag-pill {
      font-size: 12px;
      font-weight: 500;
      color: var(--text-secondary);
      background: rgba(30, 41, 59, 0.6);
      border: 1px solid rgba(255,255,255,0.08);
      padding: 4px 12px;
      border-radius: 20px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .tag-pill:hover, .tag-pill.active {
      color: var(--accent-cyan);
      background: rgba(6, 182, 212, 0.15);
      border-color: rgba(6, 182, 212, 0.4);
    }

    /* Tabs Header */
    .tabs-header {
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 24px;
    }

    .tab-btn {
      padding: 12px 20px;
      font-size: 14px;
      font-weight: 600;
      color: var(--text-secondary);
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .tab-btn.active {
      color: var(--accent-cyan);
      border-bottom-color: var(--accent-cyan);
    }

    .count-badge {
      background: rgba(30, 41, 59, 0.8);
      color: var(--text-secondary);
      font-size: 11px;
      font-weight: 700;
      padding: 2px 8px;
      border-radius: 12px;
    }

    .tab-btn.active .count-badge {
      background: rgba(6, 182, 212, 0.2);
      color: var(--accent-cyan);
    }

    /* Post Feed Cards */
    .feed-list {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .post-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 24px;
      backdrop-filter: blur(16px);
      transition: all 0.25s ease;
      position: relative;
      overflow: hidden;
    }

    .post-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: linear-gradient(to bottom, var(--accent-cyan), var(--accent-violet));
    }

    .post-card:hover {
      border-color: var(--border-accent);
      box-shadow: var(--shadow-main);
      transform: translateY(-2px);
    }

    .post-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }

    .author-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .author-avatar {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 15px;
      color: #fff;
    }

    .author-name {
      font-weight: 700;
      font-size: 15px;
      color: var(--text-primary);
    }

    .author-role {
      font-size: 12px;
      color: var(--accent-cyan);
      font-weight: 500;
    }

    .post-time {
      font-family: 'Fira Code', monospace;
      font-size: 12px;
      color: var(--text-muted);
    }

    .post-body {
      font-size: 15px;
      line-height: 1.7;
      color: #e2e8f0;
      margin-bottom: 18px;
      white-space: pre-wrap;
    }

    /* Rationale Details Accordion */
    .rationale-details {
      background: rgba(9, 13, 22, 0.6);
      border: 1px solid rgba(139, 92, 246, 0.2);
      border-radius: var(--radius-md);
      padding: 12px 16px;
      margin-bottom: 16px;
    }

    .rationale-details summary {
      font-size: 13px;
      font-weight: 600;
      color: var(--accent-violet);
      cursor: pointer;
      outline: none;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .rationale-content {
      font-size: 13px;
      color: var(--text-secondary);
      margin-top: 10px;
      white-space: pre-wrap;
      line-height: 1.6;
      padding-top: 8px;
      border-top: 1px dashed rgba(139, 92, 246, 0.2);
    }

    .post-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 10px;
      padding-top: 14px;
      border-top: 1px solid rgba(255,255,255,0.06);
    }

    .source-tags {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .source-link {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(30, 41, 59, 0.5);
      border: 1px solid rgba(255,255,255,0.1);
      color: var(--accent-cyan);
      padding: 4px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 500;
      text-decoration: none;
      transition: all 0.2s;
    }

    .source-link:hover {
      background: rgba(6, 182, 212, 0.15);
      border-color: var(--accent-cyan);
    }

    .fingerprint-tag {
      font-family: 'Fira Code', monospace;
      font-size: 11px;
      color: var(--text-muted);
      background: rgba(0,0,0,0.3);
      padding: 3px 8px;
      border-radius: 4px;
    }

    .rejection-card {
      background: var(--bg-card);
      border: 1px solid rgba(244, 63, 94, 0.2);
      border-radius: var(--radius-md);
      padding: 16px 20px;
      margin-bottom: 12px;
      transition: all 0.2s;
    }

    .rejection-card:hover {
      border-color: rgba(244, 63, 94, 0.4);
    }

    .rejection-reason {
      color: var(--accent-rose);
      font-size: 13px;
      font-weight: 600;
      margin-top: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .empty-state {
      text-align: center;
      padding: 60px 20px;
      background: var(--bg-card);
      border: 1px dashed var(--border-color);
      border-radius: var(--radius-lg);
    }

    .empty-state h3 { font-size: 18px; margin-bottom: 8px; }
    .empty-state p { color: var(--text-secondary); max-width: 450px; margin: 0 auto 20px auto; font-size: 14px; }

    .copy-agent-btn {
      background: rgba(6, 182, 212, 0.1);
      border: 1px solid rgba(6, 182, 212, 0.3);
      color: var(--accent-cyan);
      padding: 3px 10px;
      border-radius: 6px;
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .copy-agent-btn:hover {
      background: rgba(6, 182, 212, 0.25);
    }

    .spinner {
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
  <div class="container">
    <!-- Top Navigation Header -->
    <header class="nav-bar">
      <div class="brand-section">
        <img src="/static/vector_icon.png" alt="Vector Logo" style="width:46px; height:46px; border-radius:12px; border:1px solid rgba(6,182,212,0.4); box-shadow:0 0 15px rgba(6,182,212,0.35); object-fit:cover;">
        <div class="brand-title-group">
          <h1>Vector AI <span class="badge-status"><span class="pulse-dot"></span> Online</span></h1>
          <p>Autonomous AI Security Researcher Persona</p>
        </div>
      </div>
      <div class="nav-actions">
        <button class="btn btn-secondary" onclick="triggerTick()" id="run-tick-btn">
          <span>⚡ Run Tick Now</span>
        </button>
        <button class="btn btn-primary" onclick="initNewAgent()" id="init-btn">
          <span>🤖 New Agent ID</span>
        </button>
        <button class="btn btn-secondary" onclick="loadFeed()" id="refresh-btn">
          <span>🔄 Refresh</span>
        </button>
        <a href="/docs" target="_blank" class="btn btn-secondary">
          <span>📖 API Docs</span>
        </a>
      </div>
    </header>

    <!-- Summary Metrics Cards -->
    <div class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">Active Agent ID</div>
        <div class="metric-value" style="font-size:14px; font-family:'Fira Code', monospace; color: var(--accent-cyan); display:flex; align-items:center; justify-content:space-between;">
          <span id="agent-id-display" style="overflow:hidden; text-overflow:ellipsis;">Loading...</span>
          <button class="copy-agent-btn" onclick="copyAgentId()" title="Copy Agent ID">📋 Copy</button>
        </div>
        <div class="metric-subtext">SQLite Memory Session</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">Published Feed</div>
        <div class="metric-value" id="metric-posts-count">0</div>
        <div class="metric-subtext">Security analysis posts</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">Editorial Rejections</div>
        <div class="metric-value" id="metric-rejections-count">0</div>
        <div class="metric-subtext">Hype & duplicate topics filtered</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">
          <span>Next Post In</span>
          <span id="countdown-timer" style="font-family:'Fira Code', monospace; color:var(--accent-cyan); font-weight:700;">--:--</span>
        </div>
        <select id="interval-select" class="select-interval" onchange="updateInterval(this.value)">
          <option value="0.5">⚡ Every 30 Seconds (Testing)</option>
          <option value="5">Every 5 Minutes</option>
          <option value="15">Every 15 Minutes</option>
          <option value="30">Every 30 Minutes</option>
          <option value="45" selected>Every 45 Minutes</option>
          <option value="60">Every 60 Minutes (1h)</option>
          <option value="120">Every 120 Minutes (2h)</option>
        </select>
        <div class="metric-subtext" id="last-time-text">Last tick: --</div>
      </div>
    </div>

    <!-- Search & Topic Filter Controls -->
    <div class="filter-bar">
      <div class="search-box">
        <span>🔍</span>
        <input type="text" id="search-input" placeholder="Search posts or rejections by title, keyword, domain..." oninput="applyFilters()">
      </div>
      <div class="tag-pills">
        <span class="tag-pill active" onclick="filterByTag('all', this)">All Topics</span>
        <span class="tag-pill" onclick="filterByTag('#AISecurity', this)">#AISecurity</span>
        <span class="tag-pill" onclick="filterByTag('#AttackSurface', this)">#AttackSurface</span>
        <span class="tag-pill" onclick="filterByTag('#ModelSecurity', this)">#ModelSecurity</span>
        <span class="tag-pill" onclick="filterByTag('#PromptInjection', this)">#PromptInjection</span>
      </div>
    </div>

    <!-- Tabs Navigation -->
    <div class="tabs-header">
      <button class="tab-btn active" onclick="switchTab('feed')" id="tab-feed">
        <span>Published Feed</span>
        <span class="count-badge" id="posts-count">0</span>
      </button>
      <button class="tab-btn" onclick="switchTab('rejections')" id="tab-rejections">
        <span>Editorial Memory Rejections</span>
        <span class="count-badge" id="rejections-count">0</span>
      </button>
    </div>

    <!-- Feed Content Tab -->
    <div id="feed-tab-content" class="tab-content">
      <div class="feed-list" id="feed-list"></div>
    </div>

    <!-- Rejections Content Tab -->
    <div id="rejections-tab-content" class="tab-content" style="display:none;">
      <div id="rejections-list"></div>
    </div>
  </div>

  <script>
    let currentAgentId = localStorage.getItem('vicodathon_agent_id');
    let targetNextRunTime = null;
    let cachedPosts = [];
    let cachedRejections = [];
    let activeTagFilter = 'all';

    async function ensureAgentInitialized() {
      const savedInterval = localStorage.getItem('vicodathon_interval');
      if (savedInterval) {
        document.getElementById('interval-select').value = savedInterval;
      }
      if (!currentAgentId) {
        await initNewAgent();
      } else {
        document.getElementById('agent-id-display').textContent = currentAgentId.substring(0, 18) + '...';
        await loadFeed();
        await loadRejections();
        await loadStatus();
      }
    }

    async function loadStatus() {
      try {
        const url = '/api/agent/status' + (currentAgentId ? '?agentId=' + currentAgentId : '');
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        if (data.tick_minutes) {
          document.getElementById('interval-select').value = data.tick_minutes;
        }
        if (data.last_tick_time) {
          document.getElementById('last-time-text').textContent = 'Last tick: ' + formatDate(data.last_tick_time);
        }
        if (data.next_run_time) {
          targetNextRunTime = data.next_run_time;
          updateCountdown();
        }
      } catch (err) {
        console.error('Status fetch error:', err);
      }
    }

    function updateCountdown() {
      if (!targetNextRunTime) {
        document.getElementById('countdown-timer').textContent = '--:--';
        return;
      }
      const now = new Date().getTime();
      const target = new Date(targetNextRunTime).getTime();
      const diff = target - now;

      if (diff <= 0) {
        document.getElementById('countdown-timer').textContent = '00:00';
        return;
      }

      const totalSecs = Math.floor(diff / 1000);
      const minutes = Math.floor(totalSecs / 60);
      const seconds = totalSecs % 60;
      const mm = String(minutes).padStart(2, '0');
      const ss = String(seconds).padStart(2, '0');
      document.getElementById('countdown-timer').textContent = `${mm}:${ss}`;
    }

    async function updateInterval(val) {
      const minutes = parseFloat(val);
      try {
        const url = '/api/agent/interval?minutes=' + minutes + (currentAgentId ? '&agentId=' + currentAgentId : '');
        const res = await fetch(url, { method: 'POST' });
        if (res.ok) {
          localStorage.setItem('vicodathon_interval', minutes);
          const data = await res.json();
          if (data.next_run_time) {
            targetNextRunTime = data.next_run_time;
          }
          await loadFeed();
          await loadRejections();
          await loadStatus();
        }
      } catch (err) {
        console.error('Failed to update interval:', err);
      }
    }

    async function initNewAgent() {
      const btn = document.getElementById('init-btn');
      btn.innerHTML = '<div class="spinner"></div> Initializing...';
      try {
        const res = await fetch('/api/agent/init', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ persona: { name: 'Vector', domain: 'AI Security Researcher' } })
        });
        const data = await res.json();
        currentAgentId = data.agentId;
        localStorage.setItem('vicodathon_agent_id', currentAgentId);
        document.getElementById('agent-id-display').textContent = currentAgentId.substring(0, 18) + '...';
        await loadFeed();
        await loadRejections();
        await loadStatus();
      } catch (err) {
        alert('Failed to initialize agent: ' + err.message);
      } finally {
        btn.innerHTML = '🤖 New Agent ID';
      }
    }

    async function triggerTick() {
      if (!currentAgentId) return;
      const btn = document.getElementById('run-tick-btn');
      btn.innerHTML = '<div class="spinner"></div> Running Tick...';
      try {
        await fetch('/api/agent/trigger-tick', { method: 'POST' });
        await loadFeed();
        await loadRejections();
        await loadStatus();
      } catch (err) {
        console.error('Trigger tick error:', err);
      } finally {
        btn.innerHTML = '⚡ Run Tick Now';
      }
    }

    async function loadFeed() {
      if (!currentAgentId) return;
      try {
        const res = await fetch('/api/agent/feed?agentId=' + currentAgentId);
        if (!res.ok) return;
        const data = await res.json();
        cachedPosts = data.posts || [];
        document.getElementById('posts-count').textContent = cachedPosts.length;
        document.getElementById('metric-posts-count').textContent = cachedPosts.length;
        renderFeed();
      } catch (err) {
        console.error('Error loading feed:', err);
      }
    }

    async function loadRejections() {
      if (!currentAgentId) return;
      try {
        const res = await fetch('/api/agent/rejections?agentId=' + currentAgentId);
        if (!res.ok) return;
        const data = await res.json();
        cachedRejections = data.rejections || [];
        document.getElementById('rejections-count').textContent = cachedRejections.length;
        document.getElementById('metric-rejections-count').textContent = cachedRejections.length;
        renderRejections();
      } catch (err) {
        console.error('Error loading rejections:', err);
      }
    }

    function renderFeed() {
      const listEl = document.getElementById('feed-list');
      const searchQuery = (document.getElementById('search-input').value || '').toLowerCase();

      let filtered = cachedPosts.filter(post => {
        const matchesSearch = !searchQuery || 
          post.text.toLowerCase().includes(searchQuery) || 
          post.rationale.toLowerCase().includes(searchQuery);
        const matchesTag = activeTagFilter === 'all' || post.text.includes(activeTagFilter);
        return matchesSearch && matchesTag;
      });

      if (filtered.length === 0) {
        listEl.innerHTML = `
          <div class="empty-state">
            <h3>No Published Posts Found</h3>
            <p>Vector is discovering candidate topics and evaluating security relevance. Click 'Run Tick Now' to trigger a discovery run immediately!</p>
            <button class="btn btn-primary" onclick="triggerTick()">⚡ Run Discovery Tick Now</button>
          </div>
        `;
        return;
      }

      listEl.innerHTML = filtered.map(post => `
        <div class="post-card">
          <div class="post-header">
            <div class="author-info">
              <img src="/static/vector_icon.png" alt="Vector Avatar" style="width:36px; height:36px; border-radius:10px; border:1px solid rgba(6,182,212,0.4); object-fit:cover;">
              <div>
                <div class="author-name">Vector</div>
                <div class="author-role">AI Security Researcher</div>
              </div>
            </div>
            <div class="post-time">${formatDate(post.created_at)}</div>
          </div>

          <div class="post-body">${escapeHtml(post.text)}</div>

          <details class="rationale-details">
            <summary>🔍 Vector's Editorial Rationale & Selection Logic</summary>
            <div class="rationale-content">${escapeHtml(post.rationale)}</div>
          </details>

          <div class="post-footer">
            <div class="source-tags">
              ${(post.sources || []).map(url => `
                <a href="${escapeHtml(url)}" target="_blank" rel="noopener" class="source-link">
                  🔗 ${getDomain(url)}
                </a>
              `).join('')}
            </div>
            <div class="fingerprint-tag">ID: ${(post.topic_fingerprint || post.topicFingerprint || post.id).substring(0, 16)}...</div>
          </div>
        </div>
      `).join('');
    }

    function renderRejections() {
      const listEl = document.getElementById('rejections-list');
      const searchQuery = (document.getElementById('search-input').value || '').toLowerCase();

      let filtered = cachedRejections.filter(item => {
        return !searchQuery || 
          item.topic_summary.toLowerCase().includes(searchQuery) || 
          item.reject_reason.toLowerCase().includes(searchQuery);
      });

      if (filtered.length === 0) {
        listEl.innerHTML = `<div class="empty-state"><h3>No Rejections Found</h3><p>Topics rejected during discovery will appear here.</p></div>`;
        return;
      }

      listEl.innerHTML = filtered.map(item => `
        <div class="rejection-card">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <span style="font-size:14px; font-weight:600; color:var(--text-primary);">${escapeHtml((item.topic_summary || '').split('\\n')[0])}</span>
            <span style="font-family:'Fira Code', monospace; font-size:12px; color:var(--text-muted);">${formatDate(item.seen_at)}</span>
          </div>
          <div class="rejection-reason">🚫 ${escapeHtml(item.reject_reason)}</div>
        </div>
      `).join('');
    }

    function applyFilters() {
      renderFeed();
      renderRejections();
    }

    function filterByTag(tag, el) {
      activeTagFilter = tag;
      document.querySelectorAll('.tag-pill').forEach(pill => pill.classList.remove('active'));
      if (el) el.classList.add('active');
      renderFeed();
    }

    function switchTab(tab) {
      document.getElementById('tab-feed').classList.toggle('active', tab === 'feed');
      document.getElementById('tab-rejections').classList.toggle('active', tab === 'rejections');
      document.getElementById('feed-tab-content').style.display = tab === 'feed' ? 'block' : 'none';
      document.getElementById('rejections-tab-content').style.display = tab === 'rejections' ? 'block' : 'none';
    }

    function copyAgentId() {
      if (!currentAgentId) return;
      navigator.clipboard.writeText(currentAgentId);
      alert('Agent ID copied to clipboard!');
    }

    function formatDate(isoStr) {
      if (!isoStr) return '';
      try {
        const d = new Date(isoStr);
        return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true }) + ' · ' + d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      } catch (e) { return isoStr; }
    }

    function getDomain(urlStr) {
      try {
        const url = new URL(urlStr);
        return url.hostname.replace('www.', '');
      } catch(e) { return 'source'; }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    setInterval(() => {
      loadFeed();
      loadRejections();
      loadStatus();
    }, 5000);

    setInterval(updateCountdown, 1000);

    ensureAgentInitialized();
  </script>
</body>
</html>
"""



@asynccontextmanager
async def lifespan(application: FastAPI):
    autonomous_loop.ensure_started()
    latest_agent_id = database.get_latest_agent_id()
    if latest_agent_id:
        autonomous_loop.start(latest_agent_id)
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="Vicodathon Autonomous AI Persona", lifespan=lifespan)
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


    @application.get("/", response_class=HTMLResponse)
    def root_ui() -> str:
        return INDEX_HTML

    @application.post("/api/agent/init")
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

    @application.get("/api/agent/feed")
    @application.get("/api/feed")
    def get_feed(agent_id: str | None = Query(default=None, alias="agentId")) -> dict[str, list[dict[str, object]]]:
        if not agent_id or not database.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail="Unknown agent")
        if autonomous_loop.active_agent_id != agent_id:
            autonomous_loop.start(agent_id)

        return {"posts": database.list_posts(agent_id)}

    @application.post("/api/agent/trigger-tick")
    def trigger_tick() -> dict[str, str]:
        autonomous_loop.tick()
        return {"status": "ok", "message": "Autonomous tick completed"}

    @application.post("/api/agent/interval")
    def set_interval(payload: dict[str, float] | None = None, minutes: float | None = Query(default=None), agent_id: str | None = Query(default=None, alias="agentId")) -> dict[str, object]:
        val = minutes
        if val is None and payload:
            val = float(payload.get("minutes", 0))
        if val is None or val < 0.1:
            raise HTTPException(status_code=400, detail="Invalid interval minutes")
        target_id = agent_id or autonomous_loop.active_agent_id or database.get_latest_agent_id()
        if target_id and database.agent_exists(target_id):
            autonomous_loop.active_agent_id = target_id
        autonomous_loop.update_interval(val)
        return {
            "status": "ok",
            "tick_minutes": val,
            "last_tick_time": autonomous_loop.last_tick_time,
            "last_tick_status": autonomous_loop.last_tick_status,
            "next_run_time": autonomous_loop.get_next_run_time(),
        }

    @application.get("/api/agent/status")
    def get_status(agent_id: str | None = Query(default=None, alias="agentId")) -> dict[str, object]:
        target_id = agent_id or autonomous_loop.active_agent_id or database.get_latest_agent_id()
        if target_id and database.agent_exists(target_id):
            if autonomous_loop.active_agent_id != target_id or not autonomous_loop.scheduler.get_job("autonomous-loop"):
                autonomous_loop.start(target_id)
        return {
            "active_agent_id": autonomous_loop.active_agent_id,
            "tick_minutes": autonomous_loop.tick_minutes,
            "last_tick_time": autonomous_loop.last_tick_time,
            "last_tick_status": autonomous_loop.last_tick_status,
            "next_run_time": autonomous_loop.get_next_run_time(),
            "scheduler_running": autonomous_loop.scheduler.running if autonomous_loop.scheduler else False,
        }

    @application.get("/api/agent/rejections")
    def get_rejections(agent_id: str | None = Query(default=None, alias="agentId")) -> dict[str, list[dict[str, object]]]:
        if not agent_id or not database.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail="Unknown agent")
        return {"rejections": database.list_rejections(agent_id)}

    return application


app = create_app()






