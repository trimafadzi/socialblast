"""SocialBlast Orchestrator — Schedule + Coordinate + Execute"""
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

# Support both direct execution and import
try:
    from .core import settings, state, log
except ImportError:
    from core import settings, state, log

ROOT = Path(__file__).parent.parent


# ═══════════════════════════════════════════════════════
#  XActions CLI Wrapper
# ═══════════════════════════════════════════════════════

def xactions(*args) -> dict | None:
    """Run XActions CLI and return parsed JSON if available."""
    cmd = ["npx", "xactions", *args]
    log.debug(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
        if result.returncode != 0:
            log.error(f"XActions error: {result.stderr[:200]}")
            return None
        stdout = result.stdout.strip()
        # Try to parse JSON
        try:
            return json.loads(stdout)
        except:
            return {"text": stdout}
    except subprocess.TimeoutExpired:
        log.error("XActions timeout")
        return None
    except Exception as e:
        log.error(f"XActions failed: {e}")
        return None


# ═══════════════════════════════════════════════════════
#  Actions
# ═══════════════════════════════════════════════════════

def login():
    """Login to X via XActions browser session."""
    log.info("Logging into X...")
    result = xactions("login")
    if result:
        log.info("✅ X login successful")
        return True
    log.error("❌ X login failed")
    return False


def search_tweets(query: str, limit: int = 10) -> list[dict]:
    """Search tweets by keyword."""
    log.info(f"Searching: {query}")
    result = xactions("search", query, "--limit", str(limit), "--json")
    if result:
        tweets = result if isinstance(result, list) else result.get("tweets", [])
        log.info(f"Found {len(tweets)} tweets")
        return tweets
    return []


def trending() -> list[str]:
    """Get trending topics."""
    log.info("Fetching trending...")
    result = xactions("scrape", "trending", "--json")
    if result:
        trends = result if isinstance(result, list) else result.get("trends", [])
        return [t.get("name") or t.get("topic") or str(t) for t in trends[:10]]
    return []


def post_tweet(content: str) -> str | None:
    """Post a tweet. Returns tweet URL/ID."""
    log.info(f"Posting: {content[:80]}...")
    result = xactions("workflow", "run", "post-tweet", "--var", f"content={content}")
    if result and result.get("ok"):
        tweet_id = result.get("tweetId") or "posted"
        log.info(f"✅ Posted: {tweet_id}")
        return tweet_id
    log.error("Post failed")
    return None


def reply_tweet(tweet_url: str, content: str) -> bool:
    """Reply to a tweet."""
    log.info(f"Replying to: {tweet_url}")
    result = xactions("workflow", "run", "reply-tweet", 
                       "--var", f"url={tweet_url}",
                       "--var", f"content={content}")
    return result and result.get("ok", False)


def like_tweet(tweet_url: str) -> bool:
    """Like a tweet."""
    result = xactions("workflow", "run", "like-tweet", "--var", f"url={tweet_url}")
    return result and result.get("ok", False)


def follow_user(username: str) -> bool:
    """Follow a user."""
    result = xactions("follow", username)
    return result is not None


# ═══════════════════════════════════════════════════════
#  Orchestrator
# ═══════════════════════════════════════════════════════

def run_cycle():
    """One cycle: find topic → generate content → post."""
    log.info("═══ Starting cycle ═══")

    # 1. Check if we can post
    if not state.can_post():
        log.info(f"Rate limited: {state.data['posts_today']}/{settings.MAX_DAILY_POSTS} today")
        return

    # 2. Get trending or niche topic
    topics = trending()
    if not topics:
        # Fallback: search by niche
        niche = settings.NICHE[0].strip()
        results = search_tweets(niche)
        topics = [niche] if not results else [r.get("text", niche) for r in results[:3]]

    topic = topics[0] if topics else settings.NICHE[0].strip()
    log.info(f"Topic: {topic}")

    # 3. Generate tweet content
    try:
        from .generator import generator
    except ImportError:
        from generator import generator
    content = generator.generate_tweet()
    log.info(f"Content: {content}")

    # 4. Post
    tweet_id = post_tweet(content)
    if tweet_id:
        state.record_post(tweet_id, content)
        log.info(f"Cycle complete ✅ | Total today: {state.data['posts_today']}")
    else:
        log.warning("Post failed — will retry next cycle")


def main():
    """Main entry point — run once (use cron for scheduling)."""
    import argparse
    parser = argparse.ArgumentParser(description="SocialBlast X/Twitter Bot")
    parser.add_argument("--cycle", action="store_true", help="Run one post cycle")
    parser.add_argument("--setup", action="store_true", help="Login & initialize")
    parser.add_argument("--trending", action="store_true", help="Show trending topics")
    parser.add_argument("--search", type=str, help="Search tweets")
    args = parser.parse_args()

    if args.setup:
        login()
    elif args.trending:
        trends = trending()
        for t in trends:
            print(f"  📈 {t}")
    elif args.search:
        results = search_tweets(args.search)
        for r in results:
            text = r.get("text", str(r))[:100]
            print(f"  🐦 {text}")
    elif args.cycle:
        run_cycle()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
