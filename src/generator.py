"""AI Content Generator — OpenAI-powered tweet generation"""
import random
from openai import OpenAI
from .core import settings, log

# ─── Prompts ─────────────────────────────────────────────
TWEET_PROMPTS = [
    "Write a short, spicy hot take about {topic} in under 280 chars. Make it provocative but not offensive.",
    "Share an interesting insight about {topic} that most people don't know. Max 280 chars.",
    "Create an engaging question about {topic} to spark discussion. Max 280 chars.",
    "Post a bold prediction about {topic} for the next 6 months. Max 280 chars.",
    "Write a thread hook about {topic} (first tweet only). Attention-grabbing, max 280 chars.",
    "Share a contrarian opinion about {topic} that will get replies. Max 280 chars.",
]

REPLY_PROMPT = """You're replying to this tweet:
"{tweet}"

Write a short, witty, and engaging reply (max 200 chars). 
Be authentic — not like a bot. Add value, humor, or insight.
Niche context: {niche}"""

THREAD_PROMPT = """Create a {count}-tweet thread about {topic}.
Each tweet must be under 280 chars.
Make it educational + engaging.
Return as JSON array: ["tweet1", "tweet2", ...]"""


class ContentGenerator:
    """Generates AI-powered tweets and replies."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.niche = [n.strip() for n in settings.NICHE]

    def _generate(self, prompt: str, max_tokens: int = 150) -> str:
        """Call OpenAI API to generate text."""
        if not self.client:
            log.warning("No OpenAI API key — using placeholder content")
            return self._placeholder()

        try:
            resp = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a witty social media expert. Keep responses short, authentic, and engaging. Never sound like a bot."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.9,
            )
            text = resp.choices[0].message.content.strip()
            # Strip quotes if present
            text = text.strip('"').strip("'")
            # Truncate to 280 if needed
            if len(text) > 280:
                text = text[:277] + "..."
            return text
        except Exception as e:
            log.error(f"OpenAI API error: {e}")
            return self._placeholder()

    def _placeholder(self) -> str:
        """Fallback content when API unavailable."""
        topic = random.choice(self.niche)
        templates = [
            f"Just another day in {topic}... the innovation never stops 🚀",
            f"Hot take: {topic} will surprise everyone this quarter 👀",
            f"Unpopular opinion about {topic}: most people are looking at the wrong metrics 📊",
            f"Been deep in {topic} research today. Some fascinating patterns emerging...",
        ]
        return random.choice(templates)

    def generate_tweet(self) -> str:
        """Generate a single tweet."""
        topic = random.choice(self.niche)
        prompt_template = random.choice(TWEET_PROMPTS)
        prompt = prompt_template.format(topic=topic)
        return self._generate(prompt, max_tokens=120)

    def generate_reply(self, tweet_text: str) -> str:
        """Generate a reply to a given tweet."""
        prompt = REPLY_PROMPT.format(
            tweet=tweet_text[:200],
            niche=", ".join(self.niche),
        )
        return self._generate(prompt, max_tokens=100)

    def generate_thread(self, topic: str = None, count: int = 5) -> list[str]:
        """Generate a tweet thread."""
        topic = topic or random.choice(self.niche)
        prompt = THREAD_PROMPT.format(topic=topic, count=count)
        text = self._generate(prompt, max_tokens=500)

        try:
            import json
            tweets = json.loads(text)
            return [t[:280] for t in tweets[:count]]
        except:
            # Fallback: split into sentences
            return [s.strip()[:280] for s in text.split(".") if s.strip()][:count]


# Singleton
generator = ContentGenerator()
