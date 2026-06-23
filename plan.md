# SocialBlast — Implementation Plan

> **Stack:** xurl (X API v2) + Python (orchestrator) + OpenAI (AI drafts) + Hermes Cron (scheduler)
> **Status:** ✅ Phase 1 Complete ✅ Phase 2 Growth Scripts Deployed
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

### 🟡 Phase 2 — Growth ✅ SCRIPTS DEPLOYED

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Engagement script | ✅ | `1_engagement_cron.py` — 8 likes/run, 2x/day, 8-20s delay |
| 2.2 | Smart follow | ✅ | `2_smart_follow.py` — 15/day, seed followers, 30-90s delay |
| 2.3 | Reply helper (draft) | ✅ | `3_reply_helper.py` updated to target quality-first seed accounts |
| 2.4 | Reply helper (review) | ✅ | Manual review mode default (logs/console verification) |
| 2.5 | Cron deployment | ✅ | Deployed cron schedules for analytics, poster, and reply |
| 2.6 | Feedback Loop (Analytics) | ✅ | `5_analytics.py` for computed template performance weights |
| 2.7 | Weighted Content Poster | ✅ | `4_content_poster.py` selects templates via performance rankings |

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
| AI Drafts | **OpenRouter** | Gemini 2.0 Flash — free tier, 5 drafts/hari |
| Orchestrator | **Python 3.11** | Topic pool, rotation, logging |
| Scheduler | **Hermes cron** | 4x/day, zero token, silent |
| State | **JSON files** | Topic rotation, post count |

---

## ⏰ Cron Schedule

### Content (Phase 1)
| Slot | WIB | Window Actual | Theme |
|------|-----|--------------|-------|
| 🌅 Morning | 07:00 | 07:00-07:30 | Alpha |
| ☀️ Midday | 12:00 | 12:00-12:30 | Fire |
| 🌤 Afternoon | 16:00 | 16:00-16:30 | Insight |
| 🌙 Evening | 21:00 | 21:00-21:30 | Thought |

### Growth (Phase 2)
| WIB | UTC | Job | Script | Limit |
|-----|-----|-----|--------|-------|
| 08:00 | 01:00 | Reply Drafts | `3_reply_helper.py --draft` | 5 drafts |
| 10:00 | 03:00 | Smart Follow | `2_smart_follow.py` | 5 follows |
| 11:00 | 04:00 | Engagement | `1_engagement_cron.py` | 8 likes |
| 19:00 | 12:00 | Engagement | `1_engagement_cron.py` | 8 likes |

---

## 💰 Cost Estimate

| Item | Monthly |
|------|---------|
| VPS (existing) | $0 |
| X Premium | $8 |
| X API credits ($5) | **one-time** |
| Hermes Cron | **$0** |
| **Total Monthly** | **$8** |

---

## 🔑 Key Technical Decisions

1. **xurl (X API v2)** — official CLI, 1 detik per post, 100% reliable
2. **OAuth 2.0 auto-refresh** — no token management needed
3. **Smart templates** — natural human voice, rotating to avoid pattern detection
4. **Silent cron** — `no_agent=True` → zero token cost, errors only
5. **Slot-based rotation** — 5 categories per slot, tracked to avoid repetition
6. **Real trending context** — xurl search injects live tweet themes

---

## 🌱 Phase 2 — Conservative Growth Strategy

### ⚠️ Anti-Detection Principles
| Principle | Rule |
|-----------|------|
| Warm-up | Akun baru: minggu 1 manual/organic, bot start minggu 2 |
| Random delay | Semua aksi pakai random jitter antar call + startup jitter 0-30m |
| Natural pattern | No burst at :00/:15/:30/:45 — human-like timing |
| Rate cap | Follow ≤15/hari, like ≤50/hari, reply ≤5/hari ke akun besar |
| Shadowban check | Tiap 2 hari: search `from:QuantumFomo` + cek via shadowban.io |

### Build Order (Low Risk → High Risk) ✅ ALL DEPLOYED
| # | Script | Risk | Timeline |
|---|--------|------|----------|
| 1 | `1_engagement_cron.py` — search trending → like → log | 🟢 Low | ✅ Deployed |
| 2 | `2_smart_follow.py` — follow 5/run, 15/hari, crypto niche | 🟡 Medium | ✅ Deployed |
| 3 | `3_reply_helper.py` — OpenRouter (Gemini Flash, free) → **human review → post** | 🔴 High | ✅ Deployed |

### Realistic Growth Targets (Revised)
| Metric | Now | Month 1 | Month 3 |
|--------|-----|---------|---------|
| Followers | 0 | 50-150 | 500+ |
| Engagement Rate | 0% | 1-2% | 3-5% |
| Posts/hari | 4 | 4-6 | 6-8 |
| Likes/hari (outbound) | 0 | 20-30 | 40-50 |
| Follows/hari | 0 | 5-10 | 10-15 |

### Content Pipeline (Human-in-the-Loop)
```
xurl search (trending) → AI draft → Bos review → xurl post
                          ↑                      ↑
                     bulk generate          manual approve
                     (5-10 draft/hari)      (yang terbaik aja)
```

### Shadowban Monitoring
- Cron tiap 2 hari: `xurl search "from:QuantumFomo"` → cek apakah tweet muncul di search
- Manual cross-check via shadowban.io
- Alert via daily report kalo ada indikasi suppression

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
| 13 Jun 2026 | **📋 Conservative growth strategy — anti-detection, warm-up, human-in-the-loop** |
| 13 Jun 2026 | **🔥 Phase 2 scripts built — engagement, follow, reply helper (xurl edition)** |
| 13 Jun 2026 | **⏰ 4 growth cron jobs deployed — engagement 2x, follow 1x, drafts 1x** |
| 13 Jun 2026 | **🆓 AI switched to OpenRouter free tier — Gemini 2.0 Flash, $0 cost** |
| 13 Jun 2026 | **🎲 Content jitter — random 0-30 menit sebelum auto-post (anti-detection)** |
| 23 Jun 2026 | **Phase 2.5 COMPLETE: Feedback Loop Analytics & Targeted Seed Replies** |
| 23 Jun 2026 | Integrated `5_analytics.py` and `4_content_poster.py` for weighted template selection |
| 23 Jun 2026 | Switched `3_reply_helper.py` to seed_accounts list targeting for higher quality replies |
| 23 Jun 2026 | Corrected CLI bugs for all scripts to match actual local `xurl` commands |
