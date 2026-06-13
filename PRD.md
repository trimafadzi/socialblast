# SocialBlast — PRD (XActions + Playwright)

## 🎯 Visi
Bot X/Twitter automation pake **XActions** (scraping, AI) + **Playwright** (posting) + **Python orchestrator**. Zero external API key — posting via cookie auth, AI via XActions internal.

## 🏗️ Arsitektur

```
socialblast/
├── src/
│   ├── orchestrator.py     # Main loop: trending → generate → post
│   ├── generator.py        # XActions AI + smart template fallback
│   ├── browser.py          # Playwright browser utilities
│   └── core.py             # Config, state, logging
├── scripts/
│   ├── orchestrator.py     # ⭐ 4-slot topic rotation auto-poster
│   ├── post_tweet.py       # ⭐ Working! Playwright + cookie
│   ├── extract_token.py    # Auto-extract X auth_token
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
Cron trigger (07/12/16/21 WIB)
       ↓
Pick topic dari pool (5 kategori per slot)
       ↓
Generate tweet (XActions AI → fallback template)
       ↓
Playwright: x.com/compose/post + insert_text()
       ↓
Redirect → home = posted ✅
       ↓
Silent log (cuma lapor kalo error)
```

## 🛠️ Tools

| Tool | Install | Fungsi |
|------|---------|--------|
| XActions | `npm i xactions` | Scraping, AI generation |
| Playwright | `pip install playwright` | Posting via cookie auth |
| Python | system | Orchestrator |
| Hermes Cron | built-in | 4x/day scheduler |

## ✅ Fitur

### Phase 1 — MVP ✅ DONE
- [x] Project skeleton & docs
- [x] XActions AI generator (no API key)
- [x] Python orchestrator CLI
- [x] Auth token extraction (Playwright + manual)
- [x] Posting via Playwright (compose/post + insert_text)
- [x] Smart topic pool — 4 slots × 5 categories
- [x] 12 rotating templates (natural voice)
- [x] 4x/day cron jobs (07/12/16/21 WIB)
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
| AI (XActions built-in) | **$0** |
| Hermes Cron | **$0** |
| **Total** | **$8** |

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
| 13 Jun 2026 | Switch to XActions built-in AI |
| 13 Jun 2026 | Auth via Playwright cookie injection |
| 13 Jun 2026 | **Working post method found:** compose/post + insert_text |
| 13 Jun 2026 | **4x/day cron auto-poster LIVE** — topic rotation + smart templates |
