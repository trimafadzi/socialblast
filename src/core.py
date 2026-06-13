"""SocialBlast — X/Twitter Automation Core"""
import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ──────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
LOGS_DIR = ROOT / "logs"
CONFIG_DIR = ROOT / "config"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ─── Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "socialblast.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("socialblast")

# ─── Settings ────────────────────────────────────────────
class Settings:
    # X Account
    X_EMAIL = os.getenv("X_EMAIL", "")
    X_USERNAME = os.getenv("X_USERNAME", "")
    X_PASSWORD = os.getenv("X_PASSWORD", "")

    # Content
    NICHE = os.getenv("NICHE", "crypto,tech,AI").split(",")
    POST_INTERVAL_MINUTES = int(os.getenv("POST_INTERVAL_MINUTES", "120"))
    MAX_DAILY_POSTS = int(os.getenv("MAX_DAILY_POSTS", "12"))

    # Engagement
    REPLY_ENABLED = os.getenv("REPLY_ENABLED", "false").lower() == "true"
    REPLY_MAX_DAILY = int(os.getenv("REPLY_MAX_DAILY", "20"))

    # Browser
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    BROWSER_DATA_DIR = os.getenv("BROWSER_DATA_DIR", str(DATA_DIR / "browser"))

    # Tracking
    STATE_FILE = DATA_DIR / "state.json"

settings = Settings()

# ─── State Management ────────────────────────────────────
class State:
    """Persistent state tracking for posts, engagement, stats."""

    def __init__(self):
        self.data = self._load()

    def _load(self) -> dict:
        if settings.STATE_FILE.exists():
            return json.loads(settings.STATE_FILE.read_text())
        return {
            "posts_today": 0,
            "replies_today": 0,
            "last_post_at": None,
            "last_reply_at": None,
            "date": str(datetime.now().date()),
            "total_posts": 0,
            "total_replies": 0,
            "total_impressions": 0,
            "avg_engagement": 0,
            "history": [],
        }

    def save(self):
        settings.STATE_FILE.write_text(json.dumps(self.data, indent=2))

    def reset_daily(self):
        today = str(datetime.now().date())
        if self.data["date"] != today:
            self.data["posts_today"] = 0
            self.data["replies_today"] = 0
            self.data["date"] = today
            self.save()

    def can_post(self) -> bool:
        self.reset_daily()
        if self.data["posts_today"] >= settings.MAX_DAILY_POSTS:
            return False
        if self.data["last_post_at"]:
            last = datetime.fromisoformat(self.data["last_post_at"])
            if datetime.now() - last < timedelta(minutes=settings.POST_INTERVAL_MINUTES):
                return False
        return True

    def record_post(self, tweet_id: str, content: str):
        self.data["posts_today"] += 1
        self.data["total_posts"] += 1
        self.data["last_post_at"] = datetime.now().isoformat()
        self.data["history"].append({
            "type": "post",
            "id": tweet_id,
            "content": content[:100],
            "time": datetime.now().isoformat(),
        })
        self.save()

    def can_reply(self) -> bool:
        self.reset_daily()
        return (
            settings.REPLY_ENABLED
            and self.data["replies_today"] < settings.REPLY_MAX_DAILY
        )

    def record_reply(self, tweet_id: str, reply_to: str):
        self.data["replies_today"] += 1
        self.data["total_replies"] += 1
        self.data["last_reply_at"] = datetime.now().isoformat()
        self.data["history"].append({
            "type": "reply",
            "id": tweet_id,
            "reply_to": reply_to,
            "time": datetime.now().isoformat(),
        })
        self.save()

state = State()
