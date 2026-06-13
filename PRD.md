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
│   ├── orchestrator.py        # ⭐ xurl-based auto-poster
│   ├── daily_report.py        # ⭐ xurl whoami + log report
│   ├── 1_engagement_cron.py   # ⭐ Search trending → like (8/run)
│   ├── 2_smart_follow.py      # ⭐ Follow seed followers (15/day)
│   ├── 3_reply_helper.py      # ⭐ AI draft → human review → post
│   ├── run_engagement.sh      # Cron wrapper
│   ├── run_follow.sh          # Cron wrapper
│   ├── run_reply_draft.sh     # Cron wrapper
│   ├── post_tweet.py          # Playwright post (backup)
│   ├── extract_token.py       # Auth token extractor
│   └── cron_runner.py         # Silent cron wrapper
├── data/
│   ├── poster_state.json      # Topic & template rotation state
│   ├── engagement_state.json  # Liked tweet tracking
│   ├── follow_state.json      # Follow queue + daily count
│   ├── pending_replies.json   # AI draft replies (review queue)
│   └── state.json             # Legacy state
├── logs/
│   ├── poster.log             # Auto-post activity log
│   ├── engagement.log         # Like activity log
│   ├── follow.log             # Follow activity log
│   └── reply.log              # Reply draft + post log
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

### Phase 2 — Growth (Conservative) 🚀 DEPLOYED
- [x] Shadowban monitoring — cron tiap 2 hari cek search visibility
- [x] Engagement script — search trending → like → log (8 likes/run, 16/hari)
- [x] Smart follow — 5/run, 15/hari, crypto niche, random delay 30-90s
| Reply assistant — AI draft (OpenRouter, Gemini Flash free) → **human review** → post (≤5/hari)
- [x] Content pipeline — 5-10 AI drafts/hari, Bos approve via `--review`
- [x] Random jitter — semua aksi anti-pattern detection (startup + antar-call)
- [x] Cron deployment — 4 Hermes cron jobs (08:00/10:00/11:00/19:00 WIB)

### Phase 3 — Content Scale
- [ ] Thread generator — 5-7 tweet threads (AI draft → review → post)
- [ ] Visual content — chart screenshots + commentary
- [ ] A/B test timing — geser jam posting berdasarkan engagement data
- [ ] Voice refinement — 1 bulan performance data → optimize templates

### Phase 4 — Monetize
- [ ] X Ads Revenue Sharing — 5M impressions/3mo + 500 followers + Premium
- [ ] Revenue tracking
- [ ] (Optional) Account flipping — jual akun established

## 📊 Target

| Metric | Launch | Month 1 | Month 3 |
|--------|--------|---------|---------|
| Followers | 0 | 50-150 | 500+ |
| Posts/hari | 4 | 4-6 | 6-8 |
| Engagement rate | 0% | 1-2% | 3-5% |
| Likes/hari (outbound) | 0 | 20-30 | 40-50 |

## ⚠️ Risiko
- **Shadowban** — detection algo makin ketat. Mitigation: warm-up, random delay, human review
- **X rate limit** — Basic API tier ketat. Mitigation: ≤50 likes, ≤15 follows, ≤5 replies/hari
- **Content quality** — full AI = obvious. Mitigation: human-in-the-loop pipeline
- **Account suspension** — new account + aggressive = red flag. Mitigation: minggu 1 manual

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

## 📝 Changelog

| Date | Change |
|------|--------|
| 13 Jun 2026 | Init: skeleton, docs, XActions + Agent-Reach |
| 13 Jun 2026 | Auth via Playwright cookie injection |
| 13 Jun 2026 | Working post found: compose/post + insert_text |
| 13 Jun 2026 | 4x/day cron auto-poster LIVE — topic rotation + templates |
| 13 Jun 2026 | **⚡ Full xurl migration — X API v2, 1 detik per post, 100% reliable** |
| 13 Jun 2026 | **📋 Revised Phase 2-4 — conservative growth, anti-detection, human-in-the-loop** |
| 13 Jun 2026 | **🔥 Phase 2 scripts built — engagement, follow, reply helper (xurl edition)** |
| 13 Jun 2026 | **⏰ 4 growth cron jobs deployed — engagement 2x, follow 1x, drafts 1x** |
| 13 Jun 2026 | **🆓 OpenRouter free tier — Gemini Flash, $0 AI cost** |
| 13 Jun 2026 | **🎲 Content jitter — random 0-30m window before auto-post** |
