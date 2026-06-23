#!/usr/bin/env python3
"""
Script 1: Engagement Cron (xurl edition)
Cari trending crypto tweets → like → log activity
Aman, low-risk, cocok buat warm-up akun baru
"""

import subprocess
import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
# X API v2 search operators (min_faves NOT supported — filter in code instead)
SEARCH_QUERIES = [
    "crypto lang:en -is:retweet -is:reply",
    "bitcoin lang:en -is:retweet -is:reply",
    "solana lang:en -is:retweet -is:reply",
    "ethereum lang:en -is:retweet -is:reply",
    "DeFi lang:en -is:retweet -is:reply",
    "crypto alpha lang:en -is:retweet -is:reply",
    "on-chain lang:en -is:retweet -is:reply",
]

# Quality filter: min engagement per tweet (lenient for growing account)
MIN_LIKES = 0         # 0 = don't filter by likes (fresh tweets often have 0)
MIN_IMPRESSIONS = 0    # 0 = don't filter by impressions
MAX_SPAM_SCORE = 2     # skip tweets with ≥2 hashtags + cashtags (spammy)

MAX_LIKES_PER_RUN = 8        # jangan langsung agresif
DELAY_BETWEEN     = (8, 20)  # detik, randomized biar ga keliatan bot

ROOT   = Path(__file__).resolve().parent.parent  # /root/socialblast
LOG_DIR  = ROOT / "logs"
DATA_DIR = ROOT / "data"
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "engagement.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─── STATE ────────────────────────────────────────────────────────────────────
STATE_FILE = DATA_DIR / "engagement_state.json"

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"liked_ids": [], "total_likes": 0, "runs": 0}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

# ─── XURL HELPERS ─────────────────────────────────────────────────────────────
def xurl(args: list[str]) -> dict | None:
    """Wrapper untuk xurl CLI. Return parsed JSON atau None kalau error."""
    cmd = ["xurl"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            log.warning(f"xurl error: {result.stderr.strip()[:200]}")
            return None
        if not result.stdout.strip():
            return None
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        log.warning(f"xurl timeout: {' '.join(args)}")
        return None
    except json.JSONDecodeError:
        log.warning(f"xurl non-JSON output: {result.stdout.strip()[:200]}")
        return None
    except FileNotFoundError:
        log.error("xurl tidak ditemukan di PATH")
        return None


def search_tweets(query: str, max_results: int = 20) -> list[dict]:
    """Cari tweets via xurl. Return list tweet objects dgn id, text, username, author_id, metrics."""
    log.info(f"Searching: '{query}'")
    result = xurl(["search", query, "-n", str(max_results)])
    if not result:
        return []

    # xurl search returns {"data": [...], "includes": {"users": [...]}}
    tweets = result.get("data", [])
    users = {u["id"]: u["username"] for u in result.get("includes", {}).get("users", [])}

    out = []
    for tw in tweets:
        tid = str(tw.get("id", ""))
        if not tid:
            continue
        author_id = str(tw.get("author_id", ""))
        metrics = tw.get("public_metrics", {})
        
        # Quality filter: skip spammy tweets
        entities = tw.get("entities", {})
        hashtags = len(entities.get("hashtags", []))
        cashtags = len(entities.get("cashtags", []))
        spam_score = hashtags + cashtags
        if spam_score > MAX_SPAM_SCORE:
            continue
        
        # Quality filter: min engagement
        likes = metrics.get("like_count", 0)
        impressions = metrics.get("impression_count", 0)
        if likes < MIN_LIKES and impressions < MIN_IMPRESSIONS:
            continue
        
        out.append({
            "id": tid,
            "text": (tw.get("text", "") or "")[:200],
            "author_id": author_id,
            "username": users.get(author_id, "unknown"),
            "likes": likes,
            "impressions": impressions,
        })
    return out


def like_tweet(tweet_id: str) -> bool:
    """Like sebuah tweet via xurl. Return True kalau berhasil."""
    result = xurl(["like", tweet_id])
    return result is not None


def random_jitter():
    """Small random delay at start so cron runs aren't exactly on the minute. Max 60s for cron timeout."""
    jitter = random.randint(0, 60)
    if jitter > 0:
        log.info(f"🎲 Startup jitter: {jitter}s")
        time.sleep(jitter)


# ─── MAIN LOGIC ───────────────────────────────────────────────────────────────
def run_engagement():
    log.info("=" * 50)
    log.info(f"Engagement cron START — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    state = load_state()
    liked_ids_set = set(state["liked_ids"])
    liked_count = 0

    # Acak urutan query biar pattern-nya ga terlalu predictable
    queries = random.sample(SEARCH_QUERIES, k=min(3, len(SEARCH_QUERIES)))

    for query in queries:
        if liked_count >= MAX_LIKES_PER_RUN:
            break

        tweets = search_tweets(query)
        if not tweets:
            log.info(f"Tidak ada hasil untuk '{query}'")
            continue

        log.info(f"Dapat {len(tweets)} tweets untuk '{query}'")

        # Shuffle biar ga always like tweet pertama
        random.shuffle(tweets)

        for tweet in tweets:
            if liked_count >= MAX_LIKES_PER_RUN:
                break

            tweet_id = tweet["id"]
            if tweet_id in liked_ids_set:
                continue

            author = tweet["username"]
            text_preview = tweet["text"][:80]

            log.info(f"Liking @{author}: {text_preview}...")

            if like_tweet(tweet_id):
                liked_ids_set.add(tweet_id)
                liked_count += 1
                log.info(f"✅ Liked tweet {tweet_id}")
            else:
                log.warning(f"❌ Gagal like tweet {tweet_id}")

            # Random delay — penting biar ga keliatan bot
            delay = random.uniform(*DELAY_BETWEEN)
            log.info(f"Waiting {delay:.1f}s...")
            time.sleep(delay)

    # Update & save state
    state["liked_ids"] = list(liked_ids_set)[-500:]  # keep 500 terakhir biar file ga gembung
    state["total_likes"] += liked_count
    state["runs"] += 1
    state["last_run"] = datetime.now().isoformat()
    save_state(state)

    log.info(f"Engagement cron DONE — {liked_count} likes | Total: {state['total_likes']}")
    log.info("=" * 50)


if __name__ == "__main__":
    random_jitter()
    run_engagement()
