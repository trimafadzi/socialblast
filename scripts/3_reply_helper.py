#!/usr/bin/env python3
"""
3_reply_helper.py — SocialBlast Reply Helper v2
=================================================
Reply quality-first ke tweet dari seed_accounts.json (bukan random trending).
Strategy: add value, build visibility di komunitas crypto yang relevan.

Cron (2x/hari — jam aktif crypto community):
  0 10 * * * cd /root/socialblast && python scripts/3_reply_helper.py >> logs/reply.log 2>&1
  0 21 * * * cd /root/socialblast && python scripts/3_reply_helper.py >> logs/reply.log 2>&1
"""

import subprocess
import json
import os
import sys
import random
import time
from datetime import datetime, timezone, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
SEED_FILE      = "data/seed_accounts.json"
STATE_FILE     = "data/reply_state.json"
TEMPLATE_FILE  = "data/tweet_templates.json"
LOG_FILE       = "logs/reply.log"

# Batas harian total reply (semua tier)
DAILY_REPLY_LIMIT = 13          # sesuai dengan sum tier limits (2+6+5)
SESSION_LIMIT     = 5           # max per sesi (cron 2x/hari = ~10 total)

# Delay antar aksi
MIN_DELAY      = 45             # detik — lebih lambat dari engagement cron
MAX_DELAY      = 120
# ──────────────────────────────────────────────────────────────────────────────


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run_xurl(args: list[str], as_json=True) -> dict | list | None:
    cmd = ["xurl"] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if r.returncode != 0:
            log(f"[WARN] xurl error: {r.stderr.strip()[:100]}")
            return None
        return json.loads(r.stdout) if as_json else r.stdout.strip()
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        log(f"[ERROR] xurl failed: {e}")
        return None


def jitter(min_s=MIN_DELAY, max_s=MAX_DELAY):
    delay = random.uniform(min_s, max_s)
    log(f"  ⏳ Waiting {delay:.0f}s...")
    time.sleep(delay)


def load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError:
            log(f"[WARN] {path} corrupt, using default")
    return default


def save_json(path: str, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_state() -> dict:
    default = {"date": get_today_key(), "replied_tweets": [], "replied_accounts": {}, "daily_count": 0}
    state = load_json(STATE_FILE, default)
    # Reset jika hari baru
    if state.get("date") != get_today_key():
        log("[INFO] New day — resetting daily state")
        state = default
    return state


def save_state(state: dict):
    state["date"] = get_today_key()
    save_json(STATE_FILE, state)


def is_tweet_eligible(tweet: dict, seed_handle: str, state: dict, rules: dict) -> tuple[bool, str]:
    """Cek apakah tweet layak di-reply. Return (eligible, reason)."""
    tweet_id = str(tweet.get("id") or tweet.get("id_str", ""))

    # Sudah pernah direply?
    if tweet_id in state["replied_tweets"]:
        return False, "already replied"

    # Sudah reply akun ini hari ini?
    if state["replied_accounts"].get(seed_handle, 0) >= 1:
        return False, f"already replied @{seed_handle} today"

    text = tweet.get("text", "")
    text_lower = text.lower()

    # Skip retweet
    if text_lower.startswith("rt @"):
        return False, "is retweet"

    # Skip reply (tweet yang mulai dengan @mention)
    if text.startswith("@"):
        return False, "is reply tweet"

    # Skip kalau cuma media tanpa teks substantif
    if len(text.strip()) < 30:
        return False, "too short / media only"

    # Cek age
    created_at = tweet.get("created_at", "")
    if created_at:
        try:
            # Parse berbagai format
            if "Z" in created_at:
                tweet_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                tweet_time = datetime.fromisoformat(created_at)
            age_minutes = (datetime.now(timezone.utc) - tweet_time).total_seconds() / 60
            min_age = rules.get("min_tweet_age_minutes", 5)
            max_age = rules.get("max_tweet_age_minutes", 120)
            if age_minutes < min_age:
                return False, f"too fresh ({age_minutes:.0f}min)"
            if age_minutes > max_age:
                return False, f"too old ({age_minutes:.0f}min)"
        except (ValueError, TypeError):
            pass  # Kalau tidak bisa parse, lanjut saja

    return True, "ok"


def score_tweet_priority(tweet: dict) -> float:
    """Skor prioritas tweet — yang lebih engaging diprioritaskan."""
    text = tweet.get("text", "")
    metrics = tweet.get("public_metrics", {})
    score = 0.0

    # Prefer tweet dengan pertanyaan atau diskusi terbuka
    if "?" in text:
        score += 15
    if any(w in text.lower() for w in ["opinion", "thoughts", "agree", "hot take", "unpopular"]):
        score += 10
    if any(w in text.lower() for w in ["data", "%", "analysis", "report", "study"]):
        score += 8

    # Prefer tweet yang sudah dapat traction tapi masih fresh
    likes = metrics.get("like_count", 0)
    replies = metrics.get("reply_count", 0)
    if 5 <= likes <= 200:    # sweet spot: cukup visible tapi tidak terlalu ramai
        score += 12
    if replies > 0:
        score += 5           # ada diskusi berjalan = lebih natural untuk join

    return score


def build_reply_context(seed_tweet_text: str, seed_handle: str) -> str:
    """
    Build prompt untuk generate reply berkualitas.
    Dalam produksi ini bisa dipanggil ke AI API atau pakai template manual.
    """
    # Template reply berdasarkan tipe konten
    tweet_lower = seed_tweet_text.lower()

    if "?" in seed_tweet_text:
        # Tweet berupa pertanyaan — jawab dengan perspective + data
        templates = [
            "Dari pengalaman gue, {point}. Data juga support ini — {data_point}. Curious apakah {handle} punya data berbeda?",
            "Perspective gue: {point}. Yang sering diabaikan adalah {nuance}. Tapi ultimately depends on timeframe.",
            "Interesting question. Gue cenderung ke {stance} karena {reason}. Counterargument terkuat adalah {counter} — tapi gue masih belum convince.",
        ]
    elif any(w in tweet_lower for w in ["predict", "will", "soon", "expect"]):
        # Prediksi — tambah data atau nuance
        templates = [
            "Setup ini menarik. Kalau tambahin context — {data_point} — probabilitasnya naik signifikan. Risk utama menurut gue: {risk}.",
            "Sepakat dengan direction, tapi timing gue lebih {stance}. On-chain data menunjukkan {observation} yang bisa delay catalyst.",
            "Thesis valid. Satu layer yang sering miss: {nuance}. Itu bisa jadi accelerator atau invalidation tergantung {condition}.",
        ]
    elif any(w in tweet_lower for w in ["data", "chart", "%", "report"]):
        # Data/analisis — extend dengan insight tambahan
        templates = [
            "Thanks for sharing data ini. Yang gue tambahkan: {additional_data}. Combined, ini paint picture yang {assessment}.",
            "Data point yang complement ini: {data_point}. Kalau dua signal ini align, biasanya {outcome} dalam {timeframe}.",
            "Interesting data. Konteks yang helpful: {context}. Ini yang bikin gue {stance} untuk {timeframe} ke depan.",
        ]
    else:
        # General — add perspective atau counter-point
        templates = [
            "Valid point. Yang gue add: {point}. Ini yang sering missed dalam diskusi ini.",
            "Agree dengan premis. Edge case yang worth considering: {nuance}. Tergantung apakah {condition}.",
            "Interesting take. Dari angle berbeda: {alternative_view}. Keduanya bisa benar tergantung {condition}.",
        ]

    # Return template terpilih — dalam produksi, fill placeholders via AI API
    # Untuk sekarang return template as-is untuk manual review mode
    return random.choice(templates)


def fetch_recent_tweets(handle: str, count: int = 10) -> list[dict]:
    """Fetch tweet terbaru dari satu akun."""
    data = run_xurl(["search", f"from:{handle}", "-n", str(count)])
    if not data:
        return []
    if isinstance(data, list):
        return data
    return data.get("data", data.get("tweets", []))


def post_reply(tweet_id: str, reply_text: str) -> bool:
    """Post reply ke tweet_id."""
    result = run_xurl(["reply", str(tweet_id), reply_text], as_json=False)
    return result is not None


def main():
    log("=== 3_reply_helper.py v2 START ===")

    # Load config
    seed_config = load_json(SEED_FILE, {})
    if not seed_config:
        log("[EXIT] seed_accounts.json tidak ditemukan")
        sys.exit(1)

    state = load_state()
    reply_rules = seed_config.get("reply_rules", {})

    # Cek daily limit
    if state["daily_count"] >= DAILY_REPLY_LIMIT:
        log(f"[EXIT] Daily limit reached ({DAILY_REPLY_LIMIT} replies)")
        sys.exit(0)

    replies_this_session = 0

    # Iterasi per tier (tier_2 dulu karena sweet spot, lalu tier_3, baru tier_1)
    tier_order = ["tier_2", "tier_3", "tier_1"]

    for tier_name in tier_order:
        tier = seed_config.get(tier_name, {})
        accounts = tier.get("accounts", [])
        tier_limit = tier.get("daily_reply_limit", 3)

        # Shuffle akun dalam tier biar tidak selalu urutan sama
        random.shuffle(accounts)

        for account in accounts:
            if replies_this_session >= SESSION_LIMIT:
                log(f"[STOP] Session limit reached ({SESSION_LIMIT})")
                break
            if state["daily_count"] >= DAILY_REPLY_LIMIT:
                break

            handle = account["handle"]
            niche = account.get("niche", "")

            # Cek tier daily limit
            tier_count_today = sum(
                1 for acc_handle, cnt in state["replied_accounts"].items()
                if cnt > 0 and any(
                    a["handle"] == acc_handle
                    for a in seed_config.get(tier_name, {}).get("accounts", [])
                )
            )
            if tier_count_today >= tier_limit:
                log(f"  [SKIP] {tier_name} limit reached ({tier_limit})")
                break

            log(f"\n🔍 Checking @{handle} [{tier_name}] — {niche}")

            tweets = fetch_recent_tweets(handle, count=15)
            if not tweets:
                log(f"  [SKIP] No tweets found for @{handle}")
                jitter(5, 15)
                continue

            # Filter dan score
            candidates = []
            for tweet in tweets:
                eligible, reason = is_tweet_eligible(tweet, handle, state, reply_rules)
                if eligible:
                    priority = score_tweet_priority(tweet)
                    candidates.append((priority, tweet))
                else:
                    log(f"  [-] Tweet ineligible: {reason}")

            if not candidates:
                log(f"  [SKIP] No eligible tweets from @{handle}")
                continue

            # Pick tweet terbaik (highest priority score)
            candidates.sort(key=lambda x: x[0], reverse=True)
            _, target_tweet = candidates[0]
            tweet_id = str(target_tweet.get("id") or target_tweet.get("id_str"))
            tweet_text = target_tweet.get("text", "")[:100]

            log(f"  📌 Target tweet: {tweet_text}...")

            # Build reply template
            reply_template = build_reply_context(target_tweet.get("text", ""), handle)

            # ── HUMAN-IN-THE-LOOP ──────────────────────────────────────────
            # Print untuk review manual sebelum post
            log(f"\n  💬 REPLY TEMPLATE (untuk di-customize):")
            log(f"  → {reply_template}")
            log(f"  Tweet ID: {tweet_id}")
            log(f"  ⚠️  Auto-post DISABLED — edit & kirim manual via xurl atau reply_helper UI")
            # ── END HUMAN-IN-THE-LOOP ──────────────────────────────────────

            # Uncomment baris di bawah untuk enable auto-post (HATI-HATI)
            # success = post_reply(tweet_id, reply_text_filled)
            # if success:
            #     ...

            # Update state (as queued untuk review)
            state["replied_tweets"].append(tweet_id)
            state["replied_accounts"][handle] = state["replied_accounts"].get(handle, 0) + 1
            state["daily_count"] += 1
            replies_this_session += 1
            save_state(state)

            log(f"  [OK] Queued reply #{state['daily_count']} to @{handle}")
            jitter()

        if replies_this_session >= SESSION_LIMIT:
            break

    log(f"\n=== DONE — {replies_this_session} replies queued this session | {state['daily_count']}/{DAILY_REPLY_LIMIT} today ===")


if __name__ == "__main__":
    main()
