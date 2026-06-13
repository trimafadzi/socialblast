# SocialBlast — PRD (xurl + X API v2)

## 🎯 Visi
Bot X/Twitter automation pake **xurl** (official X CLI) + **X API v2** + **Python orchestrator**. Posting, search, engagement, analytics — all via official API. $5 credits = thousands of posts.

## 🏗️ Arsitektur

```
socialblast/
├── src/
│   ├── orchestrator.py     # Legacy orchestrator
│   ├── generator.py        # Template-based content
│   ├── browser.py          # Playwright utils (backup)
│   └── core.py             # Config, state, logging
├── scripts/
│   ├── orchestrator.py     # ⭐ xurl-based auto-poster
│   ├── daily_report.py     # ⭐ xurl whoami + log report
│   ├── post_tweet.py       # Playwright post (backup)
│   ├── extract_token.py    # Auth token extractor
│   └── cron_runner.py      # Silent cron wrapper
├── data/
│   ├── poster_state.json   # Topic & template rotation state
│   └── state.json          # Legacy state
├── logs/
│   └── poster.log          # Auto-post activity log
├── .env                    # X credentials (gitignored)
├── PRD.md
└── plan.md
```

**Flow:**
```
xurl search → trending context
       ↓
Template + topic pool → generate tweet
       ↓
xurl post → 1 detik, always success ✅
       ↓
xurl whoami → real metrics (followers, likes)
```

## 🛠️ Tools

| Tool | Install | Fungsi |
|------|---------|--------|
| xurl | `go install` / `npm` | Post, search, engagement, metrics |
| Python | system | Orchestrator |
| Hermes Cron | built-in | 4x/day scheduler |

## ✅ Fitur

### Phase 1 — MVP ✅ DONE
- [x] Project skeleton & docs
- [x] Smart topic pool — 4 slots × 5 categories
- [x] 12 rotating templates (natural voice)
- [x] xurl OAuth2 auth (official X API v2)
- [x] Posting via xurl — 1 detik, 100% reliable
- [x] Real trending context via xurl search
- [x] Real metrics via xurl whoami (followers, likes, tweets)
- [x] 4x/day cron jobs (07/12/16/21 WIB)
- [x] Daily report with live metrics (21:00 WIB)
- [x] Silent mode — zero token cost

### Phase 2 — Engagement
- [ ] XActions AI voice analysis
- [ ] Auto-reply trending tweets
- [ ] Like & follow
- [ ] Rate limit protection

### Phase 3 — Scale
- [ ] Multi-account
- [ ] Thread auto-post
- [ ] Analytics dashboard

### Phase 4 — Monetize
- [ ] X Ads Revenue Sharing
- [ ] Revenue tracking

## 📊 Target

| Metric | Launch | Month 1 | Month 3 |
|--------|--------|---------|---------|
| Akun | 1 | 3 | 5 |
| Posts/hari | 4 | 8 | 12 |
| Followers | 0 | 200 | 1K+ |
| Impressions | 0 | 100K | 1M+ |

## 💰 Cost

| Item | Monthly |
|------|---------|
| VPS (existing) | $0 |
| X Premium | $8 |
| X API credits ($5) | **one-time** |
| **Total Monthly** | **$8** |

## 💰 Monetization
1. **X Ads Revenue Sharing** — 5M impressions/3mo + 500 followers + Premium
2. **Affiliate links** — sisipin di reply
3. **Account flipping** — jual akun established

## ⚠️ Risiko
- Shadowban / account ban
- X auth_token expired
- X rate limit (cookie-based)
- Playwright EPIPE (mitigated: compose/post URL)

## 📝 Changelog

| Date | Change |
|------|--------|
| 13 Jun 2026 | Init: skeleton, docs, XActions + Agent-Reach |
| 13 Jun 2026 | Auth via Playwright cookie injection |
| 13 Jun 2026 | Working post found: compose/post + insert_text |
| 13 Jun 2026 | 4x/day cron auto-poster LIVE — topic rotation + templates |
| 13 Jun 2026 | **⚡ Full xurl migration — X API v2, 1 detik per post, 100% reliable** |
