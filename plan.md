# SocialBlast — Implementation Plan

> **Stack:** xurl (X API v2) + Python (orchestrator) + Hermes Cron (scheduler)
> **Status:** ✅ Phase 1 Complete — 4x/day Auto-Poster LIVE via X API v2
> **Last Updated:** 13 Jun 2026

---

## 🎯 Architecture

```
┌──────────────────────────────────────────┐
│         Python Orchestrator              │
│  (topic pool → generate → post → log)    │
└──────┬───────────────────┬───────────────┘
       │                   │
       ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│  xurl search │   │   xurl post      │
│  (trending)  │   │   (1 detik)      │
│              │   │                  │
│ • real data  │   │ • X API v2       │
│ • lang:en    │   │ • 100% reliable  │
│ • -is:rt     │   │ • JSON response  │
└──────────────┘   └──────────────────┘
       │                   │
       └───────┬───────────┘
               ▼
    ┌─────────────────────┐
    │   Hermes Cron       │
    │   4x/day schedule   │
    │   silent (no_agent) │
    └─────────────────────┘
```

## 📋 Task Board

### 🔴 Phase 1 — Setup & MVP ✅ COMPLETE

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Project skeleton | ✅ | Folder, PRD, plan |
| 1.2 | PRD + Plan docs | ✅ | Full docs |
| 1.3 | Install deps | ✅ | XActions, Playwright |
| 1.4 | Auth token extraction | ✅ | Playwright auto-extract + manual |
| 1.5 | Core orchestrator | ✅ | `scripts/orchestrator.py` |
| 1.6 | Post tweet script | ✅ | `scripts/post_tweet.py` — compose/post + insert_text |
| 1.7 | Smart topic pool | ✅ | 4 slots × 5 categories = 20 topics |
| 1.8 | AI generator + fallback | ✅ | XActions AI → 12 smart templates |
| 1.9 | Cron auto-scheduler | ✅ | 07/12/16/21 WIB, silent (no_agent) |
| 1.10 | First auto-post | ✅ | Cycle tested & working |

### 🟡 Phase 2 — Engagement (Target: Minggu 1-2)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | XActions AI voice analysis | ⏳ | Need `ai analyze` token config |
| 2.2 | Auto-reply trending | ⏳ | Reply to viral tweets in niche |
| 2.3 | Like & follow target | ⏳ | Grow following organically |
| 2.4 | Analytics tracking | ⏳ | Impressions, followers, engagement |
| 2.5 | Rate limit guard | ⏳ | Anti-shadowban protection |

### 🟢 Phase 3 — Scale (Target: Minggu 3-4)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Multi-account | ⏳ | `config/accounts.json` |
| 3.2 | Thread generator | ⏳ | Multi-tweet threads |
| 3.3 | Trending scraper | ⏳ | Real trending → topic injection |
| 3.4 | Performance dashboard | ⏳ | Simple CLI stats |

### 🔵 Phase 4 — Monetize (Target: Bulan 2+)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | X Premium subscribe | ⏳ | $8/month |
| 4.2 | Monetization application | ⏳ | 500 followers + 5M impressions |
| 4.3 | Revenue tracking | ⏳ | Payout log |

---

## 🧰 Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Posting | **xurl** | X API v2 — post, search, engagement |
| Search | **xurl search** | Real trending tweets (lang:en, -is:retweet) |
| Metrics | **xurl whoami** | Followers, tweet count, likes |
| Orchestrator | **Python 3.11** | Topic pool, rotation, logging |
| Scheduler | **Hermes cron** | 4x/day, zero token, silent |
| State | **JSON files** | Topic rotation, post count |

---

## ⏰ Cron Schedule

| Slot | WIB | Theme | Categories |
|------|-----|-------|------------|
| 🌅 Morning | 07:00 | Alpha | crypto update, AI tools, prediction, contrarian, on-chain |
| ☀️ Midday | 12:00 | Fire | chart insight, dev hot take, underrated project, psychology, alpha |
| 🌤 Afternoon | 16:00 | Insight | AI×crypto, lesson learned, 6-month predict, data, narrative |
| 🌙 Evening | 21:00 | Thought | building in public, market recap, smart money, unpopular, AI future |

---

## 💰 Cost Estimate

| Item | Monthly |
|------|---------|
| VPS (existing) | $0 |
| X Premium | $8 |
| AI (XActions built-in) | **$0** |
| Hermes Cron | **$0** |
| **Total** | **$8** |

---

## 🔑 Key Technical Decisions

1. **xurl (X API v2)** — official CLI, 1 detik per post, 100% reliable
2. **OAuth 2.0 auto-refresh** — no token management needed
3. **Smart templates** — natural human voice, rotating to avoid pattern detection
4. **Silent cron** — `no_agent=True` → zero token cost, errors only
5. **Slot-based rotation** — 5 categories per slot, tracked to avoid repetition
6. **Real trending context** — xurl search injects live tweet themes

---

## 📝 Changelog

| Date | Change |
|------|--------|
| 13 Jun 2026 | Init: skeleton, docs, switch to XActions + Agent-Reach |
| 13 Jun 2026 | Installed: XActions (npm), Agent-Reach (pip), orchestrator.py |
| 13 Jun 2026 | GitHub repo live: https://github.com/trimafadzi/socialblast |
| 13 Jun 2026 | **Phase 1 COMPLETE** |
| 13 Jun 2026 | Auth via Playwright cookie injection |
| 13 Jun 2026 | Post method: compose/post + insert_text() |
| 13 Jun 2026 | Smart topic pool: 4 slots × 5 categories |
| 13 Jun 2026 | 12 rotating fallback templates |
| 13 Jun 2026 | 4x/day Hermes cron jobs deployed (07/12/16/21 WIB) |
| 13 Jun 2026 | Full cycle tested: topic → generate → post → log ✅ |
| 13 Jun 2026 | **⚡ xurl migration — X API v2, 1 detik per post, real metrics & trending** |
