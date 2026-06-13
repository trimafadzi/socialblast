#!/usr/bin/env python3
"""
Script 3: Reply Helper — Human-in-the-Loop (xurl + OpenRouter)
Cari tweet bagus di niche → OpenRouter AI draft → lo approve → post via xurl
PENTING: Script ini TIDAK auto-post tanpa approval lo
"""

import subprocess
import json
import time
import random
import logging
import os
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SEARCH_QUERIES = [
    "solana ecosystem lang:en -is:retweet min_faves:100",
    "crypto alpha today lang:en -is:retweet min_faves:100",
    "DeFi analysis lang:en -is:retweet min_faves:50",
    "on-chain insights lang:en -is:retweet min_faves:50",
    "bitcoin thesis lang:en -is:retweet min_faves:100",
]

MAX_DRAFTS_PER_RUN  = 5        # Berapa draft yang lo mau review per sesi
NICHE_CONTEXT = "crypto, DeFi, Solana, on-chain analysis, market alpha"

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
        logging.FileHandler(LOG_DIR / "reply.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─── OPENROUTER CLIENT ────────────────────────────────────────────────────────
def get_openai_client():
    from openai import OpenAI
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        log.error("OPENROUTER_API_KEY tidak ditemukan di environment")
        return None
    return OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

# ─── STATE ────────────────────────────────────────────────────────────────────
STATE_FILE   = DATA_DIR / "reply_state.json"
DRAFTS_FILE  = DATA_DIR / "pending_replies.json"

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"replied_ids": [], "total_replies": 0, "approved": 0, "rejected": 0}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def load_drafts() -> list:
    if DRAFTS_FILE.exists():
        return json.loads(DRAFTS_FILE.read_text())
    return []

def save_drafts(drafts: list):
    DRAFTS_FILE.write_text(json.dumps(drafts, indent=2))

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


def search_tweets(query: str) -> list[dict]:
    result = xurl(["search", query, "-n", "10"])
    if not result:
        return []

    tweets = result.get("data", [])
    users = {u["id"]: u["username"] for u in result.get("includes", {}).get("users", [])}

    out = []
    for tw in tweets:
        tid = str(tw.get("id", ""))
        if not tid:
            continue
        author_id = str(tw.get("author_id", ""))
        out.append({
            "id": tid,
            "text": tw.get("text", ""),
            "author_id": author_id,
            "username": users.get(author_id, "unknown"),
        })
    return out


def post_reply(tweet_id: str, content: str) -> bool:
    """Reply to tweet via xurl. Return True kalau berhasil."""
    result = xurl(["reply", tweet_id, content])
    return result is not None


# ─── AI DRAFT GENERATOR ───────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""Kamu adalah crypto analyst dengan voice yang opinionated tapi berbobot.
Niche: {NICHE_CONTEXT}

Tugas: Buat reply pendek untuk tweet crypto yang dikasih.

Rules:
- Max 200 karakter (harus muat di Twitter)
- Bahasa: Inggris (crypto Twitter = English)
- Voice: Direct, confident, ada insight-nya — BUKAN sycophantic
- JANGAN mulai dengan "Great point!" atau "I agree!"
- Kasih hot take atau tambah data/angle yang tweet aslinya belum sebut
- Boleh controversial tapi tetap berdasar
- Jangan pake hashtag atau emoji berlebihan (max 1 emoji kalau perlu)

Output: Hanya teks reply-nya saja, tanpa penjelasan atau tanda kutip."""

def generate_reply_draft(tweet_text: str, author: str, client) -> str | None:
    """Generate draft reply pakai OpenAI."""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",  # hemat via OpenRouter
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Tweet dari @{author}:\n\n{tweet_text}"}
            ],
            max_tokens=100,
            temperature=0.85,
        )
        draft = response.choices[0].message.content.strip()
        draft = draft.strip('"').strip("'")
        return draft
    except Exception as e:
        log.error(f"OpenAI error: {e}")
        return None


# ─── INTERACTIVE APPROVAL ─────────────────────────────────────────────────────
def review_and_post_drafts():
    """Mode interaktif: review semua pending drafts, approve/reject/edit."""
    drafts = load_drafts()
    if not drafts:
        log.info("Tidak ada pending drafts. Jalankan dengan --draft dulu.")
        return

    state = load_state()
    log.info(f"\n{'='*60}")
    log.info(f"Ada {len(drafts)} draft reply menunggu review")
    log.info(f"{'='*60}\n")

    remaining = []

    for i, draft in enumerate(drafts, 1):
        print(f"\n[{i}/{len(drafts)}] TWEET ASLI dari @{draft['author']}:")
        print(f"{'─'*50}")
        print(draft["tweet_text"][:300])
        print(f"\n💬 DRAFT REPLY:")
        print(f"{'─'*50}")
        print(draft["reply_draft"])
        print(f"\n({len(draft['reply_draft'])} karakter)")
        print(f"\nOptions: [y] Post | [e] Edit | [s] Skip | [q] Quit")

        choice = input("Pilihan lo: ").strip().lower()

        if choice == "q":
            remaining.extend(drafts[i-1:])
            break
        elif choice == "y":
            if post_reply(draft["tweet_id"], draft["reply_draft"]):
                print(f"✅ Reply posted!")
                state["total_replies"] += 1
                state["approved"] += 1
                state["replied_ids"].append(draft["tweet_id"])
            else:
                print(f"❌ Gagal post reply")
                remaining.append(draft)

            delay = random.uniform(15, 45)
            print(f"Waiting {delay:.0f}s sebelum lanjut...")
            time.sleep(delay)

        elif choice == "e":
            print(f"\nEdit reply (Enter kosong = batal):")
            edited = input("> ").strip()
            if edited:
                draft["reply_draft"] = edited
                if post_reply(draft["tweet_id"], edited):
                    print(f"✅ Reply edited & posted!")
                    state["total_replies"] += 1
                    state["approved"] += 1
                    state["replied_ids"].append(draft["tweet_id"])
                else:
                    print(f"❌ Gagal post reply")
                    remaining.append(draft)

                delay = random.uniform(15, 45)
                print(f"Waiting {delay:.0f}s...")
                time.sleep(delay)
            else:
                print("Batal edit, draft disimpan")
                remaining.append(draft)
        else:
            state["rejected"] += 1
            print(f"⏭ Skipped")

        save_state(state)

    save_drafts(remaining)
    print(f"\n{'='*60}")
    print(f"Review selesai. Approved: {state['approved']} | Pending: {len(remaining)}")
    print(f"{'='*60}")


# ─── DRAFT GENERATION MODE ────────────────────────────────────────────────────
def generate_drafts():
    """Cari tweets dan generate draft replies. Simpan ke pending queue."""
    log.info("=" * 50)
    log.info(f"Reply Helper (DRAFT MODE) — {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    client = get_openai_client()
    if not client:
        return

    state = load_state()
    existing_drafts = load_drafts()
    replied_ids = set(state["replied_ids"])
    existing_draft_ids = {d["tweet_id"] for d in existing_drafts}

    new_drafts = []
    queries = random.sample(SEARCH_QUERIES, min(3, len(SEARCH_QUERIES)))

    for query in queries:
        if len(new_drafts) >= MAX_DRAFTS_PER_RUN:
            break

        log.info(f"Searching: '{query}'...")
        tweets = search_tweets(query)

        if not tweets:
            log.info("Tidak ada tweets ditemukan")
            continue

        random.shuffle(tweets)

        for tweet in tweets:
            if len(new_drafts) >= MAX_DRAFTS_PER_RUN:
                break

            tweet_id = tweet["id"]
            if tweet_id in replied_ids or tweet_id in existing_draft_ids:
                continue

            author = tweet["username"]
            text   = tweet["text"]

            if len(text) < 20:
                continue

            log.info(f"Generating draft untuk tweet @{author}...")
            draft_text = generate_reply_draft(text, author, client)

            if draft_text:
                new_drafts.append({
                    "tweet_id":    tweet_id,
                    "author":      author,
                    "tweet_text":  text,
                    "reply_draft": draft_text,
                    "created_at":  datetime.now().isoformat(),
                })
                log.info(f"✅ Draft: {draft_text[:80]}...")

            time.sleep(1)  # rate limit OpenAI

    all_drafts = existing_drafts + new_drafts
    save_drafts(all_drafts)
    log.info(f"Generated {len(new_drafts)} draft baru. Total pending: {len(all_drafts)}")
    log.info("Jalankan dengan --review untuk approve & post")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if "--review" in sys.argv:
        review_and_post_drafts()
    elif "--draft" in sys.argv or len(sys.argv) == 1:
        generate_drafts()
    else:
        print("Usage:")
        print("  python3 3_reply_helper.py --draft    # Generate drafts baru")
        print("  python3 3_reply_helper.py --review   # Review & post pending drafts")
