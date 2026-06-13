# SocialBlast — Implementation Plan

> **Stack:** XActions (automation) + Agent-Reach (social listening) + Python (orchestrator)  
> **Status:** 🚧 Phase 1 — Setup  
> **Last Updated:** 13 Jun 2026

---

## 🎯 Architecture

```
┌──────────────────────────────────────────┐
│         Python Orchestrator              │
│  (schedule, content gen, coordination)   │
└──────┬───────────────────┬───────────────┘
       │                   │
       ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│  Agent-Reach │   │    XActions      │
│  (npm CLI)   │   │   (npm CLI)      │
│              │   │                  │
│ • trending   │   │ • post tweet     │
│ • viral find │   │ • auto-reply     │
│ • social     │   │ • like/follow    │
│   listening  │   │ • scrape         │
└──────────────┘   └──────────────────┘
```

## 📋 Task Board

### 🔴 Phase 1 — Setup & MVP (Target: 1-2 hari)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Project skeleton | ✅ | Folder, PRD, plan |
| 1.2 | PRD + Plan docs | ✅ | Lengkap dengan stack options |
| 1.3 | Install Node.js deps | ✅ | XActions v0.x installed |
| 1.4 | Install Python deps | ✅ | Agent-Reach v1.3.0, OpenAI |
| 1.5 | Core orchestrator | ✅ | `src/orchestrator.py` |
| 1.6 | Workflow templates | ✅ | data/workflow-*.json |
| 1.7 | Setup script | ✅ | `scripts/setup.sh` |
| 1.8 | XActions login test | ⏳ | Username: **@QuantumFomo** |
| 1.9 | First auto-post | ⏳ | End-to-end: trending → post |

### 🟡 Phase 2 — Engagement (Target: Minggu 1-2)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Auto-reply trending | ⏳ | Agent-Reach find + XActions reply |
| 2.2 | Like & follow target | ⏳ | Grow following |
| 2.3 | Analytics tracking | ⏳ | Impressions, followers, engagement |
| 2.4 | Rate limit guard | ⏳ | Jangan kena shadowban |

### 🟢 Phase 3 — Scale (Target: Minggu 3-4)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Multi-account | ⏳ | `config/accounts.json` |
| 3.2 | Content themes | ⏳ | Rotasi niche per akun |
| 3.3 | Thread generator | ⏳ | Multi-tweet via XActions |
| 3.4 | Performance dashboard | ⏳ | Simple CLI stats |

### 🔵 Phase 4 — Monetize (Target: Minggu 5+)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | X Premium subscribe | ⏳ | $8/bln |
| 4.2 | Monetization application | ⏳ | 500 followers + 5M impressions |
| 4.3 | Revenue tracking | ⏳ | Payout log |

---

## 🧰 Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Automation | **XActions** (npm) | Post, like, reply, follow, scrape |
| Listening | **Agent-Reach** (npm) | Trending topics, viral tweets |
| Orchestrator | **Python 3.11** | Schedule, coordinate, generate |
| AI Content | **XActions built-in** | Tweet generation (no API key) |
| Scheduler | **Hermes cron** | Auto-run tiap interval |
| State | **JSON files** | Track posts & stats |

---

## 💰 Cost Estimate

| Item | Monthly |
|------|---------|
| VPS (existing) | $0 |
| X Premium | $8 |
| AI (XActions built-in) | **$0** |
| **Total** | **$8** |

---

## 📝 Changelog

| Date | Change |
|------|--------|
| 13 Jun 2026 | Init: skeleton, docs, switch to XActions + Agent-Reach |
| 13 Jun 2026 | Installed: XActions (npm), Agent-Reach (pip), orchestrator.py |
| 13 Jun 2026 | GitHub repo live: https://github.com/trimafadzi/socialblast |
