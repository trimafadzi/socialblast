# SocialBlast — PRD (XActions + Agent-Reach)

## 🎯 Visi
Bot X/Twitter automation pake **XActions** (post, reply, engagement + **built-in AI**) + **Agent-Reach** (social listening) + **Python orchestrator**. Zero external API key — semua AI pake XActions internal.

## 🏗️ Arsitektur

```
socialblast/
├── src/
│   ├── orchestrator.py     # Main loop: schedule → listen → generate → post
│   ├── generator.py        # XActions AI content generation (no API key)
│   └── core.py             # Config, state, logging
├── config/
│   └── accounts.json       # X credentials per account
├── data/
│   └── state.json          # Post history & metrics
├── scripts/
│   ├── setup.sh            # Install deps
│   └── healthcheck.sh      # Monitoring
├── logs/
├── PRD.md
└── plan.md
```

**Flow:**
```
Agent-Reach: trending search
       ↓
XActions AI: generate tweet (built-in)
       ↓
XActions CLI: post tweet
       ↓
Agent-Reach: find viral replies
       ↓
XActions CLI: auto-reply + engage
```

## 🛠️ Tools

| Tool | Install | Fungsi |
|------|---------|--------|
| XActions | `npm i xactions` | Post, reply, like, follow, scrape + AI generation |
| Agent-Reach | `pip install agent-reach` | Social listening, trending |
| Python | system | Orchestrator |
| PM2 | system | Process manager |

## ✅ Fitur

### Phase 1 — MVP
- [x] Project skeleton & docs
- [x] XActions AI generator (no API key)
- [x] Python orchestrator CLI
- [ ] XActions login (session cookie)
- [ ] First auto-post (trending → AI generate → post)

### Phase 2 — Engagement
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
| Posts/hari | 6-12 | 12-24 | 24 |
| Followers | 0 | 500 | 2K+ |
| Impressions | 0 | 500K | 5M+ |

## 💰 Cost

| Item | Monthly |
|------|---------|
| VPS (existing) | $0 |
| X Premium | $8 |
| AI (XActions built-in) | **$0** |
| **Total** | **$8** |

## 💰 Monetization
1. **X Ads Revenue Sharing** — 5M impressions/3mo + 500 followers + Premium
2. **Affiliate links** — sisipin di reply
3. **Account flipping** — jual akun established

## ⚠️ Risiko
- Shadowban / account ban
- X API changes
- XActions upstream break
