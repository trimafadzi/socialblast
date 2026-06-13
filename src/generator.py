"""AI Content Generator — XActions built-in AI (no API key needed)"""
import json
import random
import subprocess
from pathlib import Path

try:
    from .core import settings, log
except ImportError:
    from core import settings, log

ROOT = Path(__file__).parent.parent

# ─── Prompt Templates ───────────────────────────────────
TWEET_STYLES = [
    "a spicy hot take about {topic} that will trigger people. Max 280 chars.",
    "a bold prediction about {topic} for the next 6 months. Max 280 chars.",
    "a contrarian opinion about {topic} that nobody talks about. Max 280 chars.",
    "an alpha leak about {topic} disguised as a casual observation. Max 280 chars.",
    "a fomo-inducing tweet about {topic}. Make it urgent. Max 280 chars.",
    "a 'I told you so' tweet about {topic}. Smug but factual. Max 280 chars.",
]

REPLY_STYLES = [
    "a witty reply to someone who posted about {topic}. Add value, don't just agree. Max 200 chars.",
    "a contrarian reply that challenges the OP's view on {topic}. Respectful but firm. Max 200 chars.",
    "a 'here's what they're not telling you' reply about {topic}. Max 200 chars.",
]


class ContentGenerator:
    """XActions AI-powered tweet generator — no API keys needed."""

    def __init__(self):
        self.niche = [n.strip() for n in settings.NICHE]

    def _xactions_ai(self, prompt: str) -> str:
        """Call XActions AI to generate text."""
        cmd = ["npx", "xactions", "ai", "generate", prompt]
        log.debug(f"XActions AI: {prompt[:80]}...")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(ROOT),
            )
            if result.returncode != 0:
                log.warning(f"XActions AI error: {result.stderr[:100]}")
                return self._fallback()

            output = result.stdout.strip()
            # Try to parse JSON (XActions sometimes wraps in JSON)
            try:
                data = json.loads(output)
                if isinstance(data, dict):
                    text = data.get("text") or data.get("tweet") or data.get("content", "")
                elif isinstance(data, list) and data:
                    text = data[0] if isinstance(data[0], str) else data[0].get("text", "")
                else:
                    text = output
            except:
                text = output

            # Clean up
            text = text.strip('"').strip("'").strip()
            if len(text) > 280:
                text = text[:277] + "..."

            return text if text else self._fallback()

        except subprocess.TimeoutExpired:
            log.warning("XActions AI timeout")
            return self._fallback()
        except Exception as e:
            log.error(f"XActions AI failed: {e}")
            return self._fallback()

    def _fallback(self) -> str:
        """Hardcoded fallback tweets (no AI, no API needed)."""
        topic = random.choice(self.niche)
        templates = [
            f"Unpopular opinion: {topic} is still in chapter 1. The real story hasn't started yet 👀",
            f"Everyone's sleeping on {topic}. Meanwhile the smart money is accumulating silently 🧠",
            f"{topic} in 6 months will look nothing like today. Here's why nobody's ready...",
            f"Most people overcomplicate {topic}. Here's the one metric that actually matters 📊",
            f"Been tracking {topic} data for months. The pattern is too obvious to ignore at this point",
            f"Hot take: the biggest {topic} winners won't be who you think. Watch the builders, not the talkers",
        ]
        return random.choice(templates)

    def generate_tweet(self) -> str:
        """Generate a single tweet."""
        topic = random.choice(self.niche)
        style = random.choice(TWEET_STYLES).format(topic=topic)
        return self._xactions_ai(style)

    def generate_reply(self, tweet_text: str) -> str:
        """Generate a reply to a given tweet."""
        topic = self.niche[0]
        style = random.choice(REPLY_STYLES).format(topic=topic)
        prompt = f"{style}\n\nOriginal tweet: \"{tweet_text[:150]}\""
        return self._xactions_ai(prompt)


# Singleton
generator = ContentGenerator()
