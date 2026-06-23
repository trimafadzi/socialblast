#!/usr/bin/env python3
"""
4_content_poster.py — SocialBlast Content Poster v2
=====================================================
Post tweet harian dengan sistem weighted template selection berdasarkan
performance_state.json dari analytics script.

Cron (4x/hari di jam peak crypto activity):
  0 9,13,18,22 * * * cd /root/socialblast && python scripts/4_content_poster.py >> logs/poster.log 2>&1
"""

import subprocess
import json
import os
import sys
import random
import time
from datetime import datetime, timezone
from string import Template

# ── Config ────────────────────────────────────────────────────────────────────
TEMPLATE_FILE  = "data/tweet_templates.json"
STATE_FILE     = "data/performance_state.json"
POSTED_FILE    = "data/posted_state.json"
LOG_FILE       = "logs/poster.log"
TOPIC_FILE     = "data/topics.json"

DAILY_LIMIT    = 4
MIN_DELAY_SECS = 30
MAX_DELAY_SECS = 90
# ──────────────────────────────────────────────────────────────────────────────

# Coins pool + price levels untuk placeholder
COINS = ["BTC", "ETH", "SOL", "BNB", "AVAX", "ARB", "OP", "INJ", "SUI", "APT"]
LEVELS = {
    "BTC": ["95,000", "97,500", "100,000", "85,000", "90,000"],
    "ETH": ["3,200", "3,500", "3,800", "2,800", "3,000"],
    "SOL": ["145", "160", "175", "130", "140"],
    "BNB": ["580", "620", "650", "520", "550"],
    "DEFAULT": ["0.85", "1.20", "1.50", "0.70", "0.90"],
}
TIMEFRAMES = ["30 hari", "2 minggu", "Q3 2025", "akhir bulan", "minggu depan", "90 hari"]
PERCENTS_PUMP = ["15", "22", "35", "18", "27", "40"]
PERCENTS_CORR = ["8", "12", "15", "10", "18"]
EVENTS = [
    "halving Bitcoin berikutnya",
    "ETF flows melambat",
    "Fed rate decision",
    "CPI data release",
    "options expiry besar",
    "end of quarter rebalancing",
]


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_json(path: str, default):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return default


def save_json(path: str, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_today_key():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_posted_state() -> dict:
    default = {"date": get_today_key(), "count": 0, "posted_hashes": []}
    state = load_json(POSTED_FILE, default)
    if state.get("date") != get_today_key():
        state = default
    return state


def fill_placeholders(template: str) -> str:
    """Isi semua placeholder dengan nilai random yang relevan."""
    coin = random.choice(COINS)
    levels = LEVELS.get(coin, LEVELS["DEFAULT"])

    replacements = {
        "COIN"      : coin,
        "PERCENT"   : random.choice(PERCENTS_PUMP),
        "TIMEFRAME" : random.choice(TIMEFRAMES),
        "LEVEL"     : random.choice(levels),
        "EVENT"     : random.choice(EVENTS),
    }

    result = template
    for key, val in replacements.items():
        result = result.replace(f"{{{key}}}", val)
    return result


def compute_type_weights(perf_state: dict) -> dict[str, float]:
    """
    Hitung weight per template type berdasarkan performance analytics.
    Template yang perform bagus dapat chance lebih tinggi dipilih.
    Default weight = 1.0, top performer dapat 2.5x boost.
    """
    template_perf = perf_state.get("template_performance", {})
    rank_multiplier = {"top": 2.5, "mid": 1.5, "low": 0.7}
    default_weight = 1.0

    weights = {}
    # Type yang ada di template file
    all_types = ["question", "hot_take", "prediction", "price_action",
                 "data_insight", "thread_hook", "announcement", "story",
                 "comparison", "general"]

    for ttype in all_types:
        if ttype in template_perf:
            rank = template_perf[ttype].get("rank", "mid")
            weights[ttype] = rank_multiplier.get(rank, default_weight)
        else:
            weights[ttype] = default_weight

    return weights


def select_template(templates: dict, weights: dict[str, float],
                    recent_types: list[str]) -> tuple[str, str]:
    """
    Pilih template dengan weighted random, hindari repeat type dalam sesi hari ini.
    Return (template_type, template_text)
    """
    # Kurangi weight untuk type yang sudah diposting hari ini
    adjusted = {}
    for ttype, weight in weights.items():
        if ttype in recent_types:
            adjusted[ttype] = weight * 0.2  # sangat kurangi repeat
        else:
            adjusted[ttype] = weight

    # Pilih type
    types = list(adjusted.keys())
    type_weights = [adjusted.get(t, 1.0) for t in types]
    chosen_type = random.choices(types, weights=type_weights, k=1)[0]

    # Pilih template dari type tersebut
    type_templates = templates.get(chosen_type, templates.get("general", []))
    if not type_templates:
        # Fallback ke general
        type_templates = templates.get("general", ["Gue lagi monitor crypto market hari ini. Apa yang kamu watch? 👇"])

    chosen_template = random.choice(type_templates)
    return chosen_type, chosen_template


def post_tweet(text: str) -> bool:
    """Post tweet via xurl."""
    try:
        result = subprocess.run(
            ["xurl", "post", text],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0:
            return True
        log(f"[ERROR] xurl post failed: {result.stderr.strip()[:100]}")
        return False
    except subprocess.TimeoutExpired:
        log("[ERROR] xurl timeout saat post tweet")
        return False


def main():
    log("=== 4_content_poster.py v2 START ===")

    # Load states
    posted_state = load_posted_state()
    perf_state   = load_json(STATE_FILE, {})
    template_data = load_json(TEMPLATE_FILE, {})

    if not template_data:
        log("[EXIT] tweet_templates.json tidak ditemukan")
        sys.exit(1)

    # Cek daily limit
    if posted_state["count"] >= DAILY_LIMIT:
        log(f"[EXIT] Daily limit reached ({DAILY_LIMIT} tweets/day)")
        sys.exit(0)

    # Ambil template pool (skip _meta)
    templates = {k: v for k, v in template_data.items() if not k.startswith("_")}

    # Compute weights dari analytics data
    weights = compute_type_weights(perf_state)

    if perf_state.get("template_performance"):
        log("📊 Template weights dari analytics:")
        for ttype, w in sorted(weights.items(), key=lambda x: x[1], reverse=True):
            log(f"   {ttype:<15}: {w:.1f}x")
    else:
        log("📊 No analytics data yet — using equal weights")

    # Jenis yang sudah diposting hari ini
    recent_types = posted_state.get("recent_types", [])

    # Select dan fill template
    chosen_type, raw_template = select_template(templates, weights, recent_types)
    tweet_text = fill_placeholders(raw_template)

    log(f"\n📝 Selected type  : {chosen_type}")
    log(f"📝 Tweet preview  :\n{'─'*50}\n{tweet_text}\n{'─'*50}")

    # Validasi panjang (Twitter max 280 chars)
    if len(tweet_text) > 280:
        log(f"[WARN] Tweet terlalu panjang ({len(tweet_text)} chars) — truncating")
        tweet_text = tweet_text[:277] + "..."

    # Cek hash untuk hindari duplikat
    tweet_hash = str(hash(tweet_text[:100]))
    if tweet_hash in posted_state.get("posted_hashes", []):
        log("[WARN] Konten duplikat terdeteksi — skip")
        sys.exit(0)

    # Post!
    success = post_tweet(tweet_text)

    if success:
        posted_state["count"] += 1
        posted_state["posted_hashes"].append(tweet_hash)
        posted_state["recent_types"] = recent_types + [chosen_type]
        posted_state["last_posted"] = datetime.now(timezone.utc).isoformat()
        save_json(POSTED_FILE, posted_state)
        log(f"[OK] Tweet #{posted_state['count']}/{DAILY_LIMIT} posted! Type: {chosen_type}")
    else:
        log("[FAIL] Tweet gagal dipost — cek logs dan koneksi xurl")

    log("=== 4_content_poster.py DONE ===")


if __name__ == "__main__":
    main()
