# SocialBlast — Implementation Guide

> Step-by-step dari zero ke bot X/Twitter automation jalan.

## 📋 Prerequisites

- VPS Linux (Ubuntu 22.04+)
- Node.js 20+ & npm
- Python 3.11+
- Akun X/Twitter (dengan X Premium buat monetisasi)
- OpenAI API key

---

## 🔧 Step 1: Clone & Setup

```bash
git clone https://github.com/trimafadzi/socialblast.git
cd socialblast
bash scripts/setup.sh
```

Atau manual:

```bash
# Install XActions (Node.js)
npm install xactions

# Install Agent-Reach (Python)
git clone https://github.com/supersonic13/agent-reach.git /tmp/agent-reach
pip install -e /tmp/agent-reach

# Install Python deps
pip install openai python-dotenv schedule rich
```

---

## ⚙️ Step 2: Konfigurasi

```bash
cp .env.example .env
nano .env
```

Isi minimal:
```env
X_EMAIL=your_email@gmail.com
X_USERNAME=your_handle
X_PASSWORD=your_password
OPENAI_API_KEY=sk-...
NICHE=crypto,tech,AI
```

---

## 🔐 Step 3: X Login (pertama kali)

```bash
# Login via XActions browser session
npx xactions login
```

> Ini akan buka browser buat login X. Session cookie disimpan di `~/.xactions/`.

Verifikasi login:
```bash
npx xactions profile your_handle
```

---

## 🧪 Step 4: Test Komponen

```bash
# Cek trending
python3 src/orchestrator.py --trending

# Cari tweet
python3 src/orchestrator.py --search "crypto ai"

# Test post (hati-hati!)
python3 src/orchestrator.py --cycle
```

---

## 🤖 Step 5: Auto-post via Cron

### Manual cron (default)
```bash
# Post tiap 2 jam
crontab -e
# Tambahin:
0 */2 * * * cd /root/socialblast && python3 src/orchestrator.py --cycle >> logs/cron.log 2>&1
```

### Hermes cron (recommended)
```bash
hermes cron create \
  --name "socialblast-post" \
  --schedule "0 */2 * * *" \
  --prompt "Run SocialBlast post cycle: cd /root/socialblast && python3 src/orchestrator.py --cycle" \
  --deliver "origin"
```

---

## 📊 Step 6: Monitoring

```bash
# Cek state
cat data/state.json

# Cek log
tail -f logs/socialblast.log

# Statistik
python3 -c "
from src.core import state
print(f'Posts: {state.data[\"total_posts\"]}')
print(f'Today: {state.data[\"posts_today\"]}')
print(f'Replies: {state.data[\"total_replies\"]}')
"
```

---

## 🚀 Step 7: Scale Up

Setelah 1 akun jalan stabil:

1. Duplicate `.env` → `.env.acc2`
2. Bikin workflow baru di `data/workflow-*.json`
3. Tambah cron job baru dengan env berbeda:
```bash
X_ENV=.env.acc2 python3 src/orchestrator.py --cycle
```

---

## 📈 Step 8: Monetize

Setelah capai 500+ followers & 5M impressions/3 bulan:

1. Subscribe X Premium → `$8/bulan`
2. Apply X Ads Revenue Sharing
3. Tambahin affiliate link di reply
4. Scale ke 3-5 akun

---

## 🔄 Workflows Available

| Workflow | Command | Fungsi |
|----------|---------|--------|
| `post-tweet` | `npx xactions workflow run post-tweet --var content="..."` | Post single tweet |
| `reply-tweet` | `npx xactions workflow run reply-tweet --var url=... --var content=...` | Reply tweet |
| `engage` | `npx xactions workflow run engage --var query=...` | Search + like |

---

## 🛟 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Login gagal | `npx xactions logout && npx xactions login` |
| Post timeout | Cek koneksi, coba `HEADLESS=false` di .env |
| Rate limited | Kurangi `MAX_DAILY_POSTS`, delay antar post |
| Session expired | Re-login via `npx xactions login` |
| OpenAI quota | Cek billing, switch ke `gpt-4o-mini` |
