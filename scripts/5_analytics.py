#!/usr/bin/env python3
"""
5_analytics.py — SocialBlast Tweet Performance Analytics
=========================================================
Baca performa tweet terbaru @QuantumFomo via xurl CLI,
hitung engagement score tiap tweet, simpan ke performance_state.json.
Dijalankan 1x/hari (misalnya jam 08:00) setelah semalam tweet terposting.

Cron:
  0 8 * * * cd /root/socialblast && python scripts/5_analytics.py >> logs/analytics.log 2>&1
"""

import subprocess
import json
import os
import sys
import random
import time
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────────────────────────
HANDLE         = "QuantumFomo"
MAX_TWEETS     = 30           # Berapa tweet terakhir yang dianalisa
STATE_FILE     = "data/performance_state.json"
LOG_FILE       = "logs/analytics.log"
MIN_DELAY      = 3            # detik antar request xurl
MAX_DELAY      = 8

# Bobot engagement scoring (total 100)
WEIGHTS = {
    "retweet_count" : 0.35,
    "like_count"    : 0.25,
    "reply_count"   : 0.25,
    "quote_count"   : 0.15,
}
# ──────────────────────────────────────────────────────────────────────────────


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run_xurl(args: list[str]) -> dict | None:
    """Jalankan xurl command, return parsed JSON atau None kalau gagal."""
    cmd = ["xurl"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if result.returncode != 0:
            log(f"[WARN] xurl error: {result.stderr.strip()}")
            return None
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        log(f"[ERROR] xurl command failed: {e}")
        return None


def jitter():
    """Random delay untuk hindari rate limit."""
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def compute_engagement_score(metrics: dict) -> float:
    """
    Hitung engagement score 0–100 dari raw metrics.
    Normalized berdasarkan benchmark ringan (bisa disesuaikan setelah data terkumpul).
    """
    # Benchmark per-metric untuk akun < 1000 follower
    benchmarks = {
        "retweet_count" : 5,
        "like_count"    : 20,
        "reply_count"   : 5,
        "quote_count"   : 3,
    }
    score = 0.0
    for key, weight in WEIGHTS.items():
        val = metrics.get(key, 0)
        bench = benchmarks[key]
        # Capped di 2x benchmark supaya outlier tidak mendominasi
        normalized = min(val / bench, 2.0)
        score += normalized * weight * 50  # max 100 kalau semua 2x benchmark
    return round(score, 2)


def classify_performance(score: float) -> str:
    if score >= 60:
        return "🔥 viral"
    elif score >= 30:
        return "✅ good"
    elif score >= 10:
        return "⚠️  average"
    else:
        return "❌ low"


def extract_template_hint(text: str) -> str:
    """
    Coba tebak tipe template berdasarkan pola teks.
    Dipakai untuk identifikasi template mana yang perform.
    """
    text_lower = text.lower()
    if text_lower.startswith("🧵"):
        return "thread"
    elif "?" in text[:60]:
        return "question"
    elif any(w in text_lower for w in ["predict", "will", "soon", "expect"]):
        return "prediction"
    elif any(w in text_lower for w in ["%", "up", "down", "pump", "dump"]):
        return "price_action"
    elif any(w in text_lower for w in ["hot take", "unpopular opinion", "controversial"]):
        return "hot_take"
    elif any(w in text_lower for w in ["data", "chart", "report", "analysis"]):
        return "data_insight"
    elif text_lower.startswith(("reminder:", "psa:", "warning:", "alert:")):
        return "announcement"
    else:
        return "general"


def fetch_own_tweets() -> list[dict]:
    """Fetch tweet terbaru dari akun sendiri dengan metrics."""
    log(f"Fetching tweets from @{HANDLE}...")

    # Cari tweet terbaru
    data = run_xurl(["search", f"from:{HANDLE}", "-n", str(MAX_TWEETS)])
    jitter()

    if not data:
        log("[ERROR] Tidak bisa fetch tweets. Cek koneksi/auth xurl.")
        return []

    # xurl search result bisa berupa list langsung atau nested
    tweets_raw = []
    if isinstance(data, list):
        tweets_raw = data
    elif isinstance(data, dict):
        tweets_raw = data.get("data", data.get("tweets", []))

    if not tweets_raw:
        log("[WARN] Tidak ada tweet ditemukan.")
        return []

    log(f"Found {len(tweets_raw)} tweets, fetching detailed metrics...")

    results = []
    for tweet in tweets_raw:
        tweet_id = tweet.get("id") or tweet.get("id_str")
        if not tweet_id:
            continue

        # Fetch detail per-tweet untuk dapat public_metrics
        detail = run_xurl(["read", str(tweet_id)])
        jitter()

        if not detail:
            continue

        # Extract metrics — xurl bisa return flat atau nested
        metrics_raw = (
            detail.get("public_metrics") or
            detail.get("metrics") or
            {
                "like_count"    : detail.get("like_count", 0),
                "retweet_count" : detail.get("retweet_count", 0),
                "reply_count"   : detail.get("reply_count", 0),
                "quote_count"   : detail.get("quote_count", 0),
            }
        )

        text = detail.get("text", tweet.get("text", ""))
        created_at = detail.get("created_at", tweet.get("created_at", ""))

        score = compute_engagement_score(metrics_raw)
        template_type = extract_template_hint(text)
        performance = classify_performance(score)

        tweet_record = {
            "id"            : str(tweet_id),
            "text"          : text[:200],           # truncate untuk storage
            "created_at"    : created_at,
            "metrics"       : metrics_raw,
            "engagement_score" : score,
            "performance"   : performance,
            "template_type" : template_type,
        }
        results.append(tweet_record)
        log(f"  [{performance}] score={score:.1f} type={template_type} — {text[:60]}...")

    return results


def compute_template_performance(tweets: list[dict]) -> dict:
    """
    Agregasi performa per template type.
    Dipakai 4_content_poster.py untuk boost template yang bagus.
    """
    from collections import defaultdict

    type_scores: dict[str, list[float]] = defaultdict(list)
    for t in tweets:
        type_scores[t["template_type"]].append(t["engagement_score"])

    summary = {}
    for ttype, scores in type_scores.items():
        avg = sum(scores) / len(scores)
        summary[ttype] = {
            "avg_score"   : round(avg, 2),
            "count"       : len(scores),
            "top_score"   : round(max(scores), 2),
            "rank"        : "top" if avg >= 30 else "mid" if avg >= 10 else "low",
        }

    # Sorted by avg_score descending
    ranked = dict(sorted(summary.items(), key=lambda x: x[1]["avg_score"], reverse=True))
    return ranked


def update_state(tweets: list[dict], template_perf: dict):
    """Merge hasil analytics ke performance_state.json."""
    os.makedirs("data", exist_ok=True)

    # Load state existing
    existing_state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                existing_state = json.load(f)
        except json.JSONDecodeError:
            log("[WARN] performance_state.json corrupt, reset.")

    # Build tweet registry (merge, tidak overwrite yang sudah ada)
    tweet_registry = existing_state.get("tweet_registry", {})
    for t in tweets:
        tweet_registry[t["id"]] = t

    # Hitung summary stats
    all_scores = [t["engagement_score"] for t in tweet_registry.values()]
    avg_score  = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0

    # Top performers
    top_tweets = sorted(
        tweet_registry.values(),
        key=lambda x: x["engagement_score"],
        reverse=True
    )[:5]

    new_state = {
        "last_updated"       : datetime.now(timezone.utc).isoformat(),
        "account"            : HANDLE,
        "total_tweets_tracked": len(tweet_registry),
        "overall_avg_score"  : avg_score,
        "template_performance": template_perf,
        "top_tweets"         : top_tweets,
        "tweet_registry"     : tweet_registry,
    }

    with open(STATE_FILE, "w") as f:
        json.dump(new_state, f, indent=2, ensure_ascii=False)

    log(f"[OK] State saved → {STATE_FILE}")
    return new_state


def print_summary(state: dict):
    """Print ringkasan ke console/log."""
    log("=" * 55)
    log(f"📊 ANALYTICS SUMMARY — @{state['account']}")
    log(f"   Tweets tracked   : {state['total_tweets_tracked']}")
    log(f"   Overall avg score: {state['overall_avg_score']}")
    log("")
    log("📋 Template Performance Ranking:")
    for ttype, perf in state["template_performance"].items():
        icon = "🥇" if perf["rank"] == "top" else "🥈" if perf["rank"] == "mid" else "🥉"
        log(f"   {icon} {ttype:<15} avg={perf['avg_score']:.1f}  n={perf['count']}  [{perf['rank']}]")
    log("")
    log("🔥 Top 3 Tweets:")
    for i, t in enumerate(state["top_tweets"][:3], 1):
        log(f"   {i}. [{t['engagement_score']}] {t['text'][:70]}...")
    log("=" * 55)


def main():
    log("=== 5_analytics.py START ===")

    tweets = fetch_own_tweets()
    if not tweets:
        log("[EXIT] Tidak ada data untuk diproses.")
        sys.exit(0)

    template_perf = compute_template_performance(tweets)
    state = update_state(tweets, template_perf)
    print_summary(state)

    log("=== 5_analytics.py DONE ===")


if __name__ == "__main__":
    main()
