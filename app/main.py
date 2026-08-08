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
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #040508;
      --bg-card: rgba(10, 12, 18, 0.85);
      --bg-card-hover: rgba(16, 19, 28, 0.95);
      --border-color: rgba(255, 255, 255, 0.08);
      --border-glow: rgba(6, 182, 212, 0.35);
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent-cyan: #06b6d4;
      --accent-cyan-glow: rgba(6, 182, 212, 0.25);
      --accent-violet: #8b5cf6;
      --accent-emerald: #10b981;
      --accent-rose: #f43f5e;
      --accent-amber: #f59e0b;
      --radius-xl: 24px;
      --radius-lg: 16px;
      --radius-md: 12px;
      --radius-sm: 8px;
      --shadow-main: 0 20px 50px -10px rgba(0, 0, 0, 0.8);
      --shadow-glow: 0 0 40px rgba(6, 182, 212, 0.15);
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg-dark);
      background-image: 
        radial-gradient(ellipse at 50% 0%, rgba(139, 92, 246, 0.12), transparent 60%),
        radial-gradient(ellipse at 80% 60%, rgba(6, 182, 212, 0.08), transparent 50%),
        radial-gradient(ellipse at 20% 90%, rgba(16, 185, 129, 0.06), transparent 50%);
      background-attachment: fixed;
      color: var(--text-primary);
      min-height: 100vh;
      line-height: 1.6;
      padding-bottom: 80px;
    }

    .container {
      max-width: 1180px;
      margin: 0 auto;
      padding: 36px 24px;
    }

    /* Header Nav */
    .nav-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 18px 28px;
      background: rgba(8, 10, 15, 0.85);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      backdrop-filter: blur(20px);
      margin-bottom: 32px;
      box-shadow: var(--shadow-main);
      flex-wrap: wrap;
      gap: 18px;
    }

    .brand-section {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .brand-avatar {
      width: 48px !important;
      height: 48px !important;
      min-width: 48px !important;
      max-width: 48px !important;
      min-height: 48px !important;
      max-height: 48px !important;
      flex-shrink: 0 !important;
      border-radius: 12px;
      background: linear-gradient(135deg, #090d16, #141a29);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
      border: 1px solid rgba(6, 182, 212, 0.4);
      overflow: hidden !important;
    }

    .brand-avatar img {
      width: 100% !important;
      height: 100% !important;
      max-width: 100% !important;
      max-height: 100% !important;
      object-fit: cover !important;
      display: block !important;
    }

    .author-avatar {
      width: 34px !important;
      height: 34px !important;
      min-width: 34px !important;
      max-width: 34px !important;
      min-height: 34px !important;
      max-height: 34px !important;
      flex-shrink: 0 !important;
      border-radius: 10px;
      background: linear-gradient(135deg, #090d16, #141a29);
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid rgba(6, 182, 212, 0.4);
      box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
      overflow: hidden !important;
    }

    .author-avatar img {
      width: 100% !important;
      height: 100% !important;
      max-width: 100% !important;
      max-height: 100% !important;
      object-fit: cover !important;
      display: block !important;
    }

    .brand-title-group h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 60%, #94A3B8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-title-group p {
      font-size: 13px;
      color: var(--text-secondary);
    }

    .badge-status {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(16, 185, 129, 0.12);
      color: var(--accent-emerald);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 3px 12px;
      border-radius: 20px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .pulse-dot {
      width: 7px;
      height: 7px;
      background: var(--accent-emerald);
      border-radius: 50%;
      box-shadow: 0 0 10px var(--accent-emerald);
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
      padding: 10px 18px;
      border-radius: var(--radius-md);
      border: 1px solid transparent;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      display: inline-flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
    }

    .btn-primary {
      background: linear-gradient(135deg, #090d16, #161c2e);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.4);
      box-shadow: 0 4px 20px rgba(6, 182, 212, 0.15);
    }

    .btn-primary:hover {
      background: linear-gradient(135deg, #101625, #1e273e);
      border-color: #38bdf8;
      box-shadow: 0 6px 24px rgba(6, 182, 212, 0.3);
      transform: translateY(-1px);
    }

    .btn-accent {
      background: linear-gradient(135deg, #8b5cf6, #6366f1);
      color: white;
      box-shadow: 0 4px 18px rgba(139, 92, 246, 0.35);
    }

    .btn-accent:hover {
      box-shadow: 0 6px 22px rgba(139, 92, 246, 0.5);
      transform: translateY(-1px);
    }

    .btn-secondary {
      background: rgba(18, 22, 32, 0.8);
      color: var(--text-primary);
      border: 1px solid var(--border-color);
    }

    .btn-secondary:hover {
      background: rgba(28, 34, 48, 0.9);
      border-color: rgba(255, 255, 255, 0.2);
    }

    /* Metric Dashboard Grid */
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 32px;
    }

    .metric-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 22px 24px;
      backdrop-filter: blur(16px);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: all 0.25s ease;
      box-shadow: var(--shadow-main);
      position: relative;
      overflow: hidden;
    }

    .metric-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
    }

    .metric-card:hover {
      border-color: var(--border-glow);
      box-shadow: var(--shadow-glow);
      transform: translateY(-2px);
    }

    .metric-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--text-muted);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .metric-value {
      font-family: 'Outfit', sans-serif;
      font-size: 30px;
      font-weight: 800;
      color: var(--text-primary);
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .metric-sub {
      font-size: 12px;
      color: var(--text-secondary);
    }

    /* Countdown Section */
    .countdown-display {
      font-family: 'Fira Code', monospace;
      font-size: 30px;
      font-weight: 700;
      color: #38bdf8;
      text-shadow: 0 0 16px rgba(56, 189, 248, 0.4);
      letter-spacing: -0.5px;
    }

    .select-custom {
      appearance: none;
      -webkit-appearance: none;
      background: rgba(14, 18, 26, 0.9) url("data:image/svg+xml;utf8,<svg fill='%2338bdf8' height='16' viewBox='0 0 24 24' width='16' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>") no-repeat right 12px center;
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: var(--radius-md);
      padding: 8px 36px 8px 12px;
      font-family: 'Inter', sans-serif;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      outline: none;
      width: 100%;
      margin-top: 8px;
      transition: all 0.2s ease;
    }

    .select-custom:hover, .select-custom:focus {
      border-color: #38bdf8;
      box-shadow: 0 0 12px rgba(56, 189, 248, 0.2);
    }

    .select-custom option {
      background: #090d16;
      color: #f8fafc;
      padding: 10px;
    }

    /* Search and Tag Filter Bar */
    .filter-section {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 16px 20px;
      margin-bottom: 28px;
      backdrop-filter: blur(16px);
      display: flex;
      gap: 16px;
      align-items: center;
      flex-wrap: wrap;
      box-shadow: var(--shadow-main);
    }

    .search-box {
      flex: 1;
      min-width: 260px;
      position: relative;
    }

    .search-box input {
      width: 100%;
      background: rgba(14, 18, 26, 0.8);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 10px 14px 10px 38px;
      color: var(--text-primary);
      font-size: 13px;
      outline: none;
      transition: all 0.2s ease;
    }

    .search-box input:focus {
      border-color: var(--accent-cyan);
      box-shadow: 0 0 14px rgba(6, 182, 212, 0.2);
    }

    .search-icon {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      font-size: 14px;
    }

    .tag-group {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .tag-pill {
      font-size: 12px;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 20px;
      background: rgba(18, 24, 36, 0.8);
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      cursor: pointer;
      transition: all 0.2s ease;
      user-select: none;
    }

    .tag-pill:hover, .tag-pill.active {
      background: rgba(6, 182, 212, 0.15);
      border-color: var(--accent-cyan);
      color: var(--accent-cyan);
    }

    /* Tabs Header */
    .tabs-header {
      display: flex;
      gap: 12px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 24px;
      padding-bottom: 2px;
    }

    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: 'Outfit', sans-serif;
      font-size: 16px;
      font-weight: 700;
      padding: 10px 18px;
      cursor: pointer;
      position: relative;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .tab-btn:hover {
      color: var(--text-secondary);
    }

    .tab-btn.active {
      color: var(--text-primary);
    }

    .tab-btn.active::after {
      content: '';
      position: absolute;
      bottom: -3px;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent-cyan), var(--accent-violet));
      border-radius: 3px;
      box-shadow: 0 0 12px var(--accent-cyan);
    }

    .tab-count {
      font-family: 'Fira Code', monospace;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
      background: rgba(30, 41, 59, 0.8);
      color: var(--text-secondary);
    }

    .tab-btn.active .tab-count {
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
      box-shadow: var(--shadow-main);
      transition: all 0.25s ease;
      position: relative;
    }

    .post-card:hover {
      border-color: rgba(6, 182, 212, 0.3);
      box-shadow: var(--shadow-glow);
    }

    .post-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
    }

    .author-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .author-name {
      font-family: 'Outfit', sans-serif;
      font-weight: 800;
      font-size: 16px;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 6px;
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
      background: rgba(14, 18, 26, 0.8);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border-color);
    }

    .post-body {
      font-size: 14px;
      line-height: 1.7;
      color: #e2e8f0;
      white-space: pre-wrap;
      margin-bottom: 20px;
    }

    /* Rationale Accordion */
    .rationale-details {
      background: rgba(6, 9, 14, 0.8);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      overflow: hidden;
      margin-bottom: 18px;
    }

    .rationale-details summary {
      padding: 12px 16px;
      font-size: 13px;
      font-weight: 600;
      color: var(--accent-violet);
      cursor: pointer;
      outline: none;
      user-select: none;
      transition: background 0.2s ease;
    }

    .rationale-details summary:hover {
      background: rgba(139, 92, 246, 0.08);
    }

    .rationale-content {
      padding: 16px;
      font-size: 13px;
      line-height: 1.6;
      color: var(--text-secondary);
      border-top: 1px solid var(--border-color);
      background: rgba(4, 6, 10, 0.6);
      white-space: pre-wrap;
    }

    .post-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding-top: 14px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    .source-tags {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .source-link {
      font-size: 12px;
      font-weight: 600;
      color: var(--accent-cyan);
      text-decoration: none;
      background: rgba(6, 182, 212, 0.1);
      border: 1px solid rgba(6, 182, 212, 0.25);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .source-link:hover {
      background: rgba(6, 182, 212, 0.2);
      border-color: var(--accent-cyan);
    }

    .fingerprint-tag {
      font-family: 'Fira Code', monospace;
      font-size: 11px;
      color: var(--text-muted);
    }

    /* Rejections List */
    .rejections-list {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .rejection-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 16px 20px;
      backdrop-filter: blur(12px);
      transition: all 0.2s ease;
    }

    .rejection-card:hover {
      border-color: rgba(244, 63, 94, 0.3);
    }

    .rejection-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 6px;
    }

    .rejection-reason {
      font-size: 13px;
      color: #fb7185;
      background: rgba(244, 63, 94, 0.1);
      border: 1px solid rgba(244, 63, 94, 0.2);
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      display: inline-block;
      margin-top: 6px;
    }

    .empty-state {
      text-align: center;
      padding: 60px 20px;
      background: var(--bg-card);
      border: 1px dashed var(--border-color);
      border-radius: var(--radius-lg);
    }

    .empty-state h3 {
      font-family: 'Outfit', sans-serif;
      font-size: 18px;
      font-weight: 700;
      color: var(--text-primary);
      margin-bottom: 8px;
    }

    .empty-state p {
      font-size: 14px;
      color: var(--text-secondary);
      margin-bottom: 20px;
      max-width: 480px;
      margin-left: auto;
      margin-right: auto;
    }

    .spinner {
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255,255,255,0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      display: inline-block;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Top Nav -->
    <header class="nav-bar">
      <div class="brand-section">
        <div class="brand-avatar">
          <img src="/static/vector_icon.png" alt="Vector Shield">
        </div>
        <div class="brand-title-group">
          <h1>Vector AI <span class="badge-status"><span class="pulse-dot"></span> Online</span></h1>
          <p>Autonomous AI Security Researcher Persona</p>
        </div>
      </div>
      <div class="nav-actions">
        <button class="btn btn-primary" id="run-tick-btn" onclick="triggerTick()">⚡ Run Tick Now</button>
        <button class="btn btn-accent" id="init-btn" onclick="initNewAgent()">🤖 New Agent ID</button>
        <button class="btn btn-secondary" onclick="clearRejections()">🧹 Clear History</button>
        <button class="btn btn-secondary" onclick="location.reload()">🔄 Refresh</button>
        <a href="/docs" target="_blank" class="btn btn-secondary">📖 API Docs</a>
      </div>
    </header>

    <!-- Metrics Grid -->
    <section class="metrics-grid">
      <div class="metric-card">
        <div class="metric-label">
          <span>Active Agent ID</span>
          <button class="btn btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="copyAgentId()">📋 Copy</button>
        </div>
        <div class="metric-value" id="agent-id-display" style="font-size:16px; font-family:'Fira Code', monospace; color:var(--accent-cyan);">
          Loading...
        </div>
        <div class="metric-sub">SQLite Memory Session</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">Published Feed</div>
        <div class="metric-value" id="metric-posts-count">0</div>
        <div class="metric-sub">Security analysis posts</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">Publication Queue</div>
        <div class="metric-value" id="metric-queue-count" style="color: var(--accent-cyan);">0</div>
        <div class="metric-sub">Approved topics in queue</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">Editorial Rejections</div>
        <div class="metric-value" id="metric-rejections-count">0</div>
        <div class="metric-sub">Hype & duplicate topics filtered</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">
          <span>Next Post In</span>
          <span id="last-time-text" style="font-size:10px; font-weight:400; text-transform:none; color:var(--text-muted);">Syncing...</span>
        </div>
        <div class="countdown-display" id="countdown-timer">--:--</div>
        <select class="select-custom" id="interval-select" onchange="updateInterval(this.value)">
          <option value="0.5">⚡ Every 30 Seconds (Testing)</option>
          <option value="2">⚡ Every 2 Minutes</option>
          <option value="5">⚡ Every 5 Minutes</option>
          <option value="45">⚙️ Every 45 Minutes (Production)</option>
        </select>
      </div>
    </section>

    <!-- Search & Filter Bar -->
    <section class="filter-section">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input type="text" id="search-input" placeholder="Search posts, queued topics, or rejections by keyword..." oninput="applyFilters()">
      </div>
      <div class="tag-group">
        <div class="tag-pill active" onclick="filterByTag('all', this)">All Topics</div>
        <div class="tag-pill" onclick="filterByTag('#AISecurity', this)">#AISecurity</div>
        <div class="tag-pill" onclick="filterByTag('#AttackSurface', this)">#AttackSurface</div>
        <div class="tag-pill" onclick="filterByTag('#ModelSecurity', this)">#ModelSecurity</div>
        <div class="tag-pill" onclick="filterByTag('#PromptInjection', this)">#PromptInjection</div>
      </div>
    </section>

    <!-- Tabs Navigation -->
    <div class="tabs-header">
      <button class="tab-btn active" id="tab-feed" onclick="switchTab('feed')">
        📰 Published Feed <span class="tab-count" id="posts-count">0</span>
      </button>
      <button class="tab-btn" id="tab-queue" onclick="switchTab('queue')">
        📥 Publication Queue <span class="tab-count" id="queue-count">0</span>
      </button>
      <button class="tab-btn" id="tab-rejections" onclick="switchTab('rejections')">
        🛡️ Editorial Memory Rejections <span class="tab-count" id="rejections-count">0</span>
      </button>
    </div>

    <!-- Feed Tab Content -->
    <div id="feed-tab-content">
      <div class="feed-list" id="feed-list">
        <div class="empty-state">
          <h3>No Published Posts Found</h3>
          <p>Vector is discovering candidate topics and evaluating security relevance. Click 'Run Tick Now' to trigger a discovery run immediately!</p>
          <button class="btn btn-primary" onclick="triggerTick()">⚡ Run Discovery Tick Now</button>
        </div>
      </div>
    </div>

    <!-- Queue Tab Content -->
    <div id="queue-tab-content" style="display:none;">
      <div class="feed-list" id="queue-list">
        <div class="empty-state">
          <h3>Publication Queue Empty</h3>
          <p>No candidate topics currently queued. Vector will evaluate and queue approved security topics on the next tick cycle!</p>
          <button class="btn btn-primary" onclick="triggerTick()">⚡ Run Discovery Tick Now</button>
        </div>
      </div>
    </div>

    <!-- Rejections Tab Content -->
    <div id="rejections-tab-content" style="display:none;">
      <div class="rejections-list" id="rejections-list">
        <div class="empty-state">
          <h3>No Rejections Found</h3>
          <p>Topics rejected during discovery will appear here.</p>
        </div>
      </div>
    </div>
  </div>

  <script>
    let currentAgentId = localStorage.getItem('vicodathon_agent_id');
    let targetNextRunTime = null;
    let cachedPosts = [];
    let cachedQueue = [];
    let cachedRejections = [];
    let activeTagFilter = 'all';

    async function ensureAgentInitialized() {
      const savedInterval = localStorage.getItem('vicodathon_interval');
      if (savedInterval) {
        const select = document.getElementById('interval-select');
        if (select) select.value = savedInterval;
      }
      try {
        const url = '/api/agent/status' + (currentAgentId ? '?agentId=' + encodeURIComponent(currentAgentId) : '');
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          if (data && data.active_agent_id) {
            currentAgentId = String(data.active_agent_id);
            localStorage.setItem('vicodathon_agent_id', currentAgentId);
            const displayEl = document.getElementById('agent-id-display');
            if (displayEl) {
              displayEl.textContent = currentAgentId.length > 18 ? currentAgentId.substring(0, 18) + '...' : currentAgentId;
            }
          }
        } else if (res.status === 404) {
          currentAgentId = null;
        }
      } catch (e) {
        console.error('Status check error:', e);
      }

      if (!currentAgentId) {
        await initNewAgent();
      } else {
        await loadFeed();
        await loadQueue();
        await loadRejections();
        await loadStatus();
      }
    }

    async function loadStatus() {
      try {
        const url = '/api/agent/status' + (currentAgentId ? '?agentId=' + encodeURIComponent(currentAgentId) : '');
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        if (data && data.tick_minutes !== undefined && data.tick_minutes !== null) {
          const valStr = String(data.tick_minutes);
          const select = document.getElementById('interval-select');
          if (select) {
            for (let opt of select.options) {
              if (Math.abs(parseFloat(opt.value) - parseFloat(valStr)) < 0.01) {
                select.value = opt.value;
                break;
              }
            }
          }
        }
        if (data && data.last_tick_time) {
          const lastEl = document.getElementById('last-time-text');
          if (lastEl) lastEl.textContent = 'Last: ' + formatDate(data.last_tick_time);
        }
        if (data && data.next_run_time) {
          targetNextRunTime = data.next_run_time;
          updateCountdown();
        }
      } catch (err) {
        console.error('Status fetch error:', err);
      }
    }

    function updateCountdown() {
      if (!targetNextRunTime) {
        const timerEl = document.getElementById('countdown-timer');
        if (timerEl) timerEl.textContent = '--:--';
        return;
      }
      const now = new Date().getTime();
      const target = new Date(targetNextRunTime).getTime();
      const diff = target - now;

      const timerEl = document.getElementById('countdown-timer');
      if (diff <= 0) {
        if (timerEl) timerEl.textContent = '00:00';
        if (Math.abs(diff) < 3000) {
          loadStatus();
          loadFeed();
          loadQueue();
        }
        return;
      }

      const totalSecs = Math.floor(diff / 1000);
      const minutes = Math.floor(totalSecs / 60);
      const seconds = totalSecs % 60;
      const mm = String(minutes).padStart(2, '0');
      const ss = String(seconds).padStart(2, '0');
      if (timerEl) timerEl.textContent = `${mm}:${ss}`;
    }

    async function updateInterval(val) {
      const minutes = parseFloat(val);
      try {
        const url = '/api/agent/interval?minutes=' + minutes + (currentAgentId ? '&agentId=' + encodeURIComponent(currentAgentId) : '');
        const res = await fetch(url, { method: 'POST' });
        if (res.ok) {
          localStorage.setItem('vicodathon_interval', minutes);
          const data = await res.json();
          if (data && data.next_run_time) {
            targetNextRunTime = data.next_run_time;
          }
          await loadFeed();
          await loadQueue();
          await loadRejections();
          await loadStatus();
        }
      } catch (err) {
        console.error('Failed to update interval:', err);
      }
    }

    async function initNewAgent() {
      const btn = document.getElementById('init-btn');
      if (btn) btn.innerHTML = '<div class="spinner"></div> Init...';
      try {
        const res = await fetch('/api/agent/init', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ persona: { name: 'Vector', domain: 'AI Security Researcher' } })
        });
        if (!res.ok) {
          throw new Error('HTTP ' + res.status);
        }
        const data = await res.json();
        if (data && data.agentId) {
          currentAgentId = String(data.agentId);
          localStorage.setItem('vicodathon_agent_id', currentAgentId);
          const displayEl = document.getElementById('agent-id-display');
          if (displayEl) {
            displayEl.textContent = currentAgentId.length > 18 ? currentAgentId.substring(0, 18) + '...' : currentAgentId;
          }
          await loadFeed();
          await loadQueue();
          await loadRejections();
          await loadStatus();
        }
      } catch (err) {
        console.error('Failed to initialize agent:', err);
      } finally {
        if (btn) btn.innerHTML = '🤖 New Agent ID';
      }
    }

    async function triggerTick() {
      if (!currentAgentId) return;
      const btn = document.getElementById('run-tick-btn');
      if (btn) btn.innerHTML = '<div class="spinner"></div> Running...';
      try {
        await fetch('/api/agent/trigger-tick', { method: 'POST' });
        await loadFeed();
        await loadQueue();
        await loadRejections();
        await loadStatus();
      } catch (err) {
        console.error('Trigger tick error:', err);
      } finally {
        if (btn) btn.innerHTML = '⚡ Run Tick Now';
      }
    }

    async function clearRejections() {
      if (!currentAgentId) return;
      if (!confirm('Clear rejection history?')) return;
      try {
        await fetch('/api/agent/clear-rejections?agentId=' + encodeURIComponent(currentAgentId), { method: 'POST' });
        await loadRejections();
      } catch (err) {
        console.error('Clear rejections error:', err);
      }
    }

    async function loadFeed() {
      if (!currentAgentId) return;
      try {
        const res = await fetch('/api/agent/feed?agentId=' + encodeURIComponent(currentAgentId));
        if (res.status === 404) {
          console.warn('Agent ID not found on server, initializing new agent...');
          await initNewAgent();
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        cachedPosts = (data && data.posts) || [];
        const pCountEl = document.getElementById('posts-count');
        const mCountEl = document.getElementById('metric-posts-count');
        if (pCountEl) pCountEl.textContent = cachedPosts.length;
        if (mCountEl) mCountEl.textContent = cachedPosts.length;
        renderFeed();
      } catch (err) {
        console.error('Error loading feed:', err);
      }
    }

    async function loadQueue() {
      if (!currentAgentId) return;
      try {
        const res = await fetch('/api/agent/queue?agentId=' + encodeURIComponent(currentAgentId));
        if (!res.ok) return;
        const data = await res.json();
        cachedQueue = (data && data.queue) || [];
        const count = (data && data.count) !== undefined ? data.count : cachedQueue.length;
        const qCountEl = document.getElementById('queue-count');
        const mqCountEl = document.getElementById('metric-queue-count');
        if (qCountEl) qCountEl.textContent = count;
        if (mqCountEl) mqCountEl.textContent = count;
        renderQueue();
      } catch (err) {
        console.error('Error loading queue:', err);
      }
    }

    async function loadRejections() {
      if (!currentAgentId) return;
      try {
        const res = await fetch('/api/agent/rejections?agentId=' + encodeURIComponent(currentAgentId));
        if (res.status === 404) {
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        cachedRejections = (data && data.rejections) || [];
        const rCountEl = document.getElementById('rejections-count');
        const mrCountEl = document.getElementById('metric-rejections-count');
        if (rCountEl) rCountEl.textContent = cachedRejections.length;
        if (mrCountEl) mrCountEl.textContent = cachedRejections.length;
        renderRejections();
      } catch (err) {
        console.error('Error loading rejections:', err);
      }
    }

    function renderFeed() {
      const listEl = document.getElementById('feed-list');
      if (!listEl) return;
      const searchEl = document.getElementById('search-input');
      const searchQuery = searchEl ? searchEl.value.toLowerCase() : '';

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
              <div class="author-avatar"><img src="/static/vector_icon.png" alt="Vector Shield"></div>
              <div class="author-name">Vector AI</div>
            </div>
            <div class="post-time">${formatDate(post.created_at)}</div>
          </div>

          <div class="post-body">${escapeHtml(post.text)}</div>

          <details class="rationale-details">
            <summary>🔍 Vector's Editorial Rationale</summary>
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
            <div class="fingerprint-tag">ID: ${(post.topic_fingerprint || post.topicFingerprint || post.id || '').substring(0, 8)}</div>
          </div>
        </div>
      `).join('');
    }

    function renderQueue() {
      const listEl = document.getElementById('queue-list');
      if (!listEl) return;
      const searchEl = document.getElementById('search-input');
      const searchQuery = searchEl ? searchEl.value.toLowerCase() : '';

      let filtered = cachedQueue.filter(item => {
        return !searchQuery || 
          (item.title || '').toLowerCase().includes(searchQuery) || 
          (item.summary || '').toLowerCase().includes(searchQuery) ||
          (item.decision_reason || '').toLowerCase().includes(searchQuery);
      });

      if (filtered.length === 0) {
        listEl.innerHTML = `
          <div class="empty-state">
            <h3>Publication Queue Empty</h3>
            <p>No candidate topics currently queued. Vector will evaluate and queue approved security topics on the next tick cycle!</p>
            <button class="btn btn-primary" onclick="triggerTick()">⚡ Run Discovery Tick Now</button>
          </div>
        `;
        return;
      }

      listEl.innerHTML = filtered.map((item, idx) => `
        <div class="post-card" style="border-left: 4px solid var(--accent-cyan);">
          <div class="post-header">
            <div class="author-info">
              <span class="badge-status" style="background: rgba(6, 182, 212, 0.15); color: var(--accent-cyan); border-color: rgba(6, 182, 212, 0.4);">
                📥 Queued Position #${idx + 1}
              </span>
            </div>
            <div class="post-time">${formatDate(item.queued_at)}</div>
          </div>

          <div style="font-family:'Outfit', sans-serif; font-size:16px; font-weight:700; color:var(--text-primary); margin-bottom:10px;">
            ${escapeHtml(item.title || '')}
          </div>

          <div class="post-body" style="color:var(--text-secondary); font-size:14px; margin-bottom:14px;">
            ${escapeHtml(item.summary || '')}
          </div>

          <div style="background:rgba(6, 182, 212, 0.08); border:1px solid rgba(6, 182, 212, 0.2); padding:10px 14px; border-radius:var(--radius-sm); font-size:13px; color:var(--accent-cyan); margin-bottom:12px;">
            <strong>✓ Editorial Approval Reason:</strong> ${escapeHtml(item.decision_reason || '')}
          </div>

          <div class="post-footer">
            <div class="source-tags">
              ${(item.source_urls || []).map(url => `
                <a href="${escapeHtml(url)}" target="_blank" rel="noopener" class="source-link">
                  🔗 ${getDomain(url)} (${escapeHtml(item.source_name || 'Source')})
                </a>
              `).join('')}
            </div>
            <div class="fingerprint-tag">Fingerprint: ${(item.topic_fingerprint || item.id || '').substring(0, 8)}</div>
          </div>
        </div>
      `).join('');
    }

    function renderRejections() {
      const listEl = document.getElementById('rejections-list');
      if (!listEl) return;
      const searchEl = document.getElementById('search-input');
      const searchQuery = searchEl ? searchEl.value.toLowerCase() : '';

      let filtered = cachedRejections.filter(item => {
        return !searchQuery || 
          (item.topic_summary || '').toLowerCase().includes(searchQuery) || 
          (item.reject_reason || '').toLowerCase().includes(searchQuery);
      });

      if (filtered.length === 0) {
        listEl.innerHTML = `<div class="empty-state"><h3>No Rejections Found</h3><p>Topics rejected during discovery will appear here.</p></div>`;
        return;
      }

      listEl.innerHTML = filtered.map(item => `
        <div class="rejection-card">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div class="rejection-title">${escapeHtml((item.topic_summary || '').split('\\n')[0])}</div>
            <span style="font-family:'Fira Code', monospace; font-size:12px; color:var(--text-muted);">${formatDate(item.seen_at)}</span>
          </div>
          <div class="rejection-reason">🚫 ${escapeHtml(item.reject_reason || '')}</div>
        </div>
      `).join('');
    }

    function applyFilters() {
      renderFeed();
      renderQueue();
      renderRejections();
    }

    function filterByTag(tag, el) {
      activeTagFilter = tag;
      document.querySelectorAll('.tag-pill').forEach(pill => pill.classList.remove('active'));
      if (el) el.classList.add('active');
      renderFeed();
    }

    function switchTab(tab) {
      const tabFeed = document.getElementById('tab-feed');
      const tabQueue = document.getElementById('tab-queue');
      const tabRejections = document.getElementById('tab-rejections');
      if (tabFeed) tabFeed.classList.toggle('active', tab === 'feed');
      if (tabQueue) tabQueue.classList.toggle('active', tab === 'queue');
      if (tabRejections) tabRejections.classList.toggle('active', tab === 'rejections');

      const feedContent = document.getElementById('feed-tab-content');
      const queueContent = document.getElementById('queue-tab-content');
      const rejectionsContent = document.getElementById('rejections-tab-content');
      if (feedContent) feedContent.style.display = tab === 'feed' ? 'block' : 'none';
      if (queueContent) queueContent.style.display = tab === 'queue' ? 'block' : 'none';
      if (rejectionsContent) rejectionsContent.style.display = tab === 'rejections' ? 'block' : 'none';
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
        return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
      } catch (e) { return isoStr; }
    }

    function getDomain(urlStr) {
      if (!urlStr || typeof urlStr !== 'string') return 'source';
      try {
        let validUrl = urlStr.trim();
        if (!validUrl.startsWith('http://') && !validUrl.startsWith('https://')) {
          validUrl = 'https://' + validUrl;
        }
        const url = new URL(validUrl);
        return url.hostname.replace(/^www\./, '') || 'source';
      } catch(e) {
        return 'source';
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }

    setInterval(() => {
      loadFeed();
      loadQueue();
      loadRejections();
      loadStatus();
    }, 4000);

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

    @application.get("/api/agent/queue")
    def get_queue(agent_id: str | None = Query(default=None, alias="agentId")) -> dict[str, object]:
        target_id = agent_id or autonomous_loop.active_agent_id or database.get_latest_agent_id()
        if not target_id or not database.agent_exists(target_id):
            return {"queue": [], "count": 0}
        return {"queue": database.list_queued_topics(target_id), "count": database.queued_count(target_id)}

    @application.post("/api/agent/clear-rejections")
    def clear_rejections(agent_id: str | None = Query(default=None, alias="agentId")) -> dict[str, str]:
        target_id = agent_id or autonomous_loop.active_agent_id or database.get_latest_agent_id()
        if target_id and database.agent_exists(target_id):
            database.clear_rejections(target_id)
        return {"status": "ok", "message": "Rejections cleared"}

    return application


app = create_app()






