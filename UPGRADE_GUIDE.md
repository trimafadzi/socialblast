# SocialBlast Upgrade Guide — Phase 2.5
## Analytics + Template Pool v2 + Seed Reply Strategy

---

## Files Baru / Updated

| File | Status | Keterangan |
|------|--------|-----------|
| `scripts/5_analytics.py` | ✨ NEW | Baca performa tweet, simpan ke JSON |
| `scripts/3_reply_helper.py` | 🔄 UPDATED | Target seed accounts, quality-first |
| `scripts/4_content_poster.py` | 🔄 UPDATED | Baca analytics, weighted template selection |
| `data/tweet_templates.json` | ✨ NEW | 48 templates, 10 type berbeda |
| `data/seed_accounts.json` | ✨ NEW | 24 crypto influencer dalam 3 tier |

---

## Deploy ke VPS Hermes

### 1. Upload files

```bash
# Dari local machine
scp scripts/5_analytics.py root@103.59.160.62:/root/socialblast/scripts/
scp scripts/3_reply_helper.py root@103.59.160.62:/root/socialblast/scripts/
scp scripts/4_content_poster.py root@103.59.160.62:/root/socialblast/scripts/
scp data/tweet_templates.json root@103.59.160.62:/root/socialblast/data/
scp data/seed_accounts.json root@103.59.160.62:/root/socialblast/data/

# Atau kalau pakai git
cd /root/socialblast && git pull origin main
```

### 2. Test manual dulu sebelum cron

```bash
cd /root/socialblast

# Test analytics (pastikan xurl auth sudah ada)
python scripts/5_analytics.py

# Cek output
cat data/performance_state.json | python -m json.tool | head -50

# Test reply helper (dry run — auto-post disabled by default)
python scripts/3_reply_helper.py

# Test content poster
python scripts/4_content_poster.py
```

### 3. Setup cron

```bash
crontab -e
```

Tambahkan:

```
# Analytics — 1x/hari jam 08:00 WIB (01:00 UTC)
0 1 * * * cd /root/socialblast && python scripts/5_analytics.py >> logs/analytics.log 2>&1

# Content poster — 4x/hari jam peak activity
# 09:00, 13:00, 18:00, 22:00 WIB = 02, 06, 11, 15 UTC
0 2,6,11,15 * * * cd /root/socialblast && python scripts/4_content_poster.py >> logs/poster.log 2>&1

# Reply helper — 2x/hari
# 10:00 dan 21:00 WIB = 03 dan 14 UTC
0 3,14 * * * cd /root/socialblast && python scripts/3_reply_helper.py >> logs/reply.log 2>&1
```

---

## Cara Kerja Feedback Loop

```
5_analytics.py (pagi)
       ↓
performance_state.json
       ↓
4_content_poster.py (baca weights)
       ↓
Template dengan engagement tinggi → dipilih lebih sering
Template dengan engagement rendah → dikurangi frekuensinya
```

### Contoh output performance_state.json setelah 1 minggu:

```json
{
  "template_performance": {
    "hot_take": { "avg_score": 45.2, "rank": "top" },
    "question": { "avg_score": 32.1, "rank": "top" },
    "data_insight": { "avg_score": 28.5, "rank": "mid" },
    "general": { "avg_score": 8.3, "rank": "low" }
  }
}
```

Artinya content_poster akan boost `hot_take` dan `question` 2.5x lebih sering.

---

## Reply Helper — Cara Enable Auto-Post

Default: **manual review mode** (print template, tidak auto-post).

Untuk enable auto-post, edit `3_reply_helper.py` baris ~170:

```python
# Sekarang (disabled):
# success = post_reply(tweet_id, reply_text_filled)

# Aktifkan:
reply_filled = fill_reply_template(reply_template, target_tweet)
success = post_reply(tweet_id, reply_filled)
if success:
    log(f"  [OK] Reply posted!")
```

⚠️ **Rekomendasi**: Jalankan manual review mode dulu 3-5 hari untuk pastikan quality reply bagus sebelum auto-post.

---

## Customisasi seed_accounts.json

Edit `data/seed_accounts.json` untuk update akun target:

```json
{
  "tier_2": {
    "accounts": [
      { "handle": "NamaAkun", "niche": "topik yang mereka bahas" }
    ]
  }
}
```

**Tips pilih akun yang bagus:**
- Aktif posting (min 3x/hari)
- Follower 10k-100k (reach oke, tidak terlalu ramai)
- Sering dapat reply dan diskusi di tweet-nya
- Niche sama (crypto, trading, DeFi)

---

## Monitoring

```bash
# Lihat log real-time
tail -f /root/socialblast/logs/analytics.log
tail -f /root/socialblast/logs/reply.log
tail -f /root/socialblast/logs/poster.log

# Cek berapa tweet sudah dipost hari ini
cat data/posted_state.json

# Cek template mana yang perform
cat data/performance_state.json | python -m json.tool | grep -A5 "template_performance"

# Cek reply state
cat data/reply_state.json
```
