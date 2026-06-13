#!/usr/bin/env python3
"""
Script 2: Smart Follow (xurl edition)
Follow akun-akun di niche crypto yang relevan, dengan rate limit aman
dan random delay biar ga keliatan bot
"""

import subprocess
import json
import time
import random
import logging
from datetime import datetime, date
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────

# Seed accounts: akun besar crypto, lo follow followersnya
SEED_ACCOUNTS = [
    "ansem",
    "CryptoCobain",
    "0xMert_",
    "aeyakovenko",
    "rajgokal",
    "notthreadguy",
    "blknoiz06",
]

MAX_FOLLOWS_PER_DAY = 15      # Konservatif untuk akun baru
MAX_FOLLOWS_PER_RUN = 5       # Per satu kali jalan
DELAY_BETWEEN       = (30, 90) # detik

ROOT   = Path(__file__).resolve().parent.parent
LOG_DIR  = ROOT / "logs"
DATA_DIR = ROOT / "data"
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# ─── LOGGING ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "follow.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─── STATE ────────────────────────────────────────────────────────────────────
STATE_FILE = DATA_DIR / "follow_state.json"

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "followed": [],
        "total_follows": 0,
        "daily_follows": {},  # {"2026-06-13": 5}
        "queue": [],          # akun yang mau di-follow
    }

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def get_today_follows(state: dict) -> int:
    today = str(date.today())
    return state["daily_follows"].get(today, 0)

def increment_daily(state: dict):
    today = str(date.today())
    state["daily_follows"][today] = state["daily_follows"].get(today, 0) + 1

# ─── XURL HELPERS ─────────────────────────────────────────────────────────────
def xurl(args: list[str]) -> dict | None:
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
        log.warning("xurl timeout")
        return None
    except json.JSONDecodeError:
        log.warning(f"xurl non-JSON: {result.stdout.strip()[:200]}")
        return None
    except FileNotFoundError:
        log.error("xurl tidak ditemukan di PATH")
        return None


def get_user_id(handle: str) -> str | None:
    """Resolve username → user ID via xurl API."""
    result = xurl(["/2/users/by/username/" + handle.lstrip("@")])
    if result:
        return result.get("data", {}).get("id")
    return None


def get_followers_of(handle: str, count: int = 50) -> list[str]:
    """Ambil followers dari akun tertentu via xurl API. Return list handles."""
    log.info(f"Fetching followers of @{handle}...")
    user_id = get_user_id(handle)
    if not user_id:
        log.warning(f"Tidak bisa resolve user ID untuk @{handle}")
        return []

    result = xurl([f"/2/users/{user_id}/followers?max_results={count}"])
    if not result:
        return []

    users = result.get("data", [])
    return [u.get("username") for u in users if u.get("username")]


def follow_user(handle: str) -> bool:
    """Follow sebuah akun via xurl. Return True kalau berhasil."""
    result = xurl(["follow", "@" + handle.lstrip("@")])
    return result is not None


def get_profile(handle: str) -> dict | None:
    """Ambil info profil untuk filter followers count."""
    result = xurl(["/2/users/by/username/" + handle.lstrip("@") + "?user.fields=public_metrics"])
    if result:
        return result.get("data", {})
    return None


# ─── FILTER LOGIC ─────────────────────────────────────────────────────────────
def is_worth_following(handle: str) -> bool:
    """
    Cek apakah akun layak di-follow:
    - Followers 100-500K (medium size, lebih likely follow back)
    - Punya minimal 5 tweet
    """
    profile = get_profile(handle)
    if not profile:
        return False

    metrics = profile.get("public_metrics", {})
    followers = metrics.get("followers_count", 0)
    tweets    = metrics.get("tweet_count", 0)

    if followers < 100:
        log.debug(f"@{handle} terlalu kecil ({followers} followers), skip")
        return False
    if followers > 500_000:
        log.debug(f"@{handle} terlalu besar ({followers} followers), skip")
        return False
    if tweets < 5:
        log.debug(f"@{handle} hampir ga pernah tweet, skip")
        return False

    return True


# ─── QUEUE MANAGEMENT ─────────────────────────────────────────────────────────
def replenish_queue(state: dict) -> list[str]:
    """Isi queue dengan followers dari seed accounts."""
    log.info("Mengisi follow queue dari seed accounts...")
    already_followed = set(state["followed"])
    new_candidates = []

    for seed in random.sample(SEED_ACCOUNTS, min(3, len(SEED_ACCOUNTS))):
        followers = get_followers_of(seed, count=50)
        for handle in followers:
            if handle and handle not in already_followed and handle not in new_candidates:
                new_candidates.append(handle)

    log.info(f"Dapat {len(new_candidates)} kandidat baru")
    return new_candidates


# ─── MAIN LOGIC ───────────────────────────────────────────────────────────────
def run_follow():
    log.info("=" * 50)
    log.info(f"Follow script START — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    state = load_state()

    # Cek daily limit
    today_count = get_today_follows(state)
    if today_count >= MAX_FOLLOWS_PER_DAY:
        log.info(f"Daily limit tercapai ({today_count}/{MAX_FOLLOWS_PER_DAY}). Skip hari ini.")
        return

    remaining_today = MAX_FOLLOWS_PER_DAY - today_count
    follows_this_run = min(MAX_FOLLOWS_PER_RUN, remaining_today)

    # Replenish queue kalau kosong
    if len(state.get("queue", [])) < 10:
        new_candidates = replenish_queue(state)
        state["queue"] = list(set(state.get("queue", []) + new_candidates))
        save_state(state)

    if not state.get("queue"):
        log.warning("Queue kosong, tidak ada yang di-follow")
        return

    followed_count = 0

    while followed_count < follows_this_run and state["queue"]:
        handle = state["queue"].pop(0)
        already_followed = set(state["followed"])

        if handle in already_followed:
            continue

        log.info(f"Checking @{handle}...")

        # Filter (comment out untuk mode agresif)
        if not is_worth_following(handle):
            continue

        log.info(f"Following @{handle}...")
        if follow_user(handle):
            state["followed"].append(handle)
            state["total_follows"] = state.get("total_follows", 0) + 1
            increment_daily(state)
            followed_count += 1
            log.info(f"✅ Followed @{handle} | Today: {get_today_follows(state)}/{MAX_FOLLOWS_PER_DAY}")
        else:
            log.warning(f"❌ Gagal follow @{handle}")

        # Save setiap iterasi
        save_state(state)

        if followed_count < follows_this_run:
            delay = random.uniform(*DELAY_BETWEEN)
            log.info(f"Waiting {delay:.0f}s...")
            time.sleep(delay)

    log.info(f"Follow script DONE — {followed_count} follows | Total: {state['total_follows']}")
    log.info("=" * 50)


if __name__ == "__main__":
    run_follow()
