#!/usr/bin/env python3
"""SocialBlast Auto-Poster — xurl edition (X API v2)"""
import os, sys, json, random, subprocess
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path('/root/socialblast')
LOG_FILE = ROOT / 'logs' / 'poster.log'
STATE_FILE = ROOT / 'data' / 'poster_state.json'
LOG_FILE.parent.mkdir(exist_ok=True)
STATE_FILE.parent.mkdir(exist_ok=True)

# ========== TOPIC POOL ==========
TOPIC_SLOTS = {
    0: {
        'label': '🌅 Morning Alpha',
        'categories': [
            'morning crypto update', 'fresh AI tool drop', 'bold daily prediction',
            'contrarian market take', 'overnight on-chain alpha',
        ]
    },
    1: {
        'label': '☀️ Midday Fire',
        'categories': [
            'chart pattern insight', 'dev productivity hot take', 'underrated project shout-out',
            'trading psychology tip', 'alpha most people miss',
        ]
    },
    2: {
        'label': '🌤 Afternoon Insight',
        'categories': [
            'AI vs crypto intersection', 'lesson from a failed trade', '6-month tech prediction',
            'data-driven observation', 'crypto narrative analysis',
        ]
    },
    3: {
        'label': '🌙 Night Thought',
        'categories': [
            'building in public reflection', 'market day recap', 'smart money move',
            'unpopular crypto opinion', 'deep thought on AI future',
        ]
    },
}

TEMPLATES = [
    "thinking about {topic} and honestly... the signal is clearer than the noise rn",
    "unpopular take: {topic}. most people are looking in the wrong direction",
    "been tracking {topic} for months. the pattern is getting hard to ignore",
    "hot take on {topic} — we're gonna look back at this in 6 months and laugh",
    "{topic} is one of those things where waiting for confirmation = already late",
    "if you're not paying attention to {topic}, you're sleeping on free alpha",
    "real ones know {topic} isn't a trend — it's the inevitable outcome",
    "controversial but... {topic}. save this tweet, come back in december",
    "here's what nobody tells you about {topic}: the crowd is always 3 months behind",
    "just spent an hour deep-diving {topic}. here's my raw take",
    "{topic} — either you get it now, or you'll fomo into it at 10x",
    "daily reminder that {topic} doesn't care about your feelings. data > vibes",
]

def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'last_slot': -1, 'used_categories': {}, 'used_templates': [], 'total_posts': 0}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def get_current_slot() -> int:
    h = datetime.now().hour
    if 5 <= h < 10:    return 0
    elif 10 <= h < 14: return 1
    elif 14 <= h < 19: return 2
    else:              return 3

def pick_topic(state: dict, slot: int) -> str:
    slot_info = TOPIC_SLOTS[slot]
    cats = slot_info['categories']
    key = str(slot)
    used = state.get('used_categories', {}).get(key, [])
    available = [c for c in cats if c not in used]
    if not available:
        available = cats[:]
        used = []
    topic = random.choice(available)
    used.append(topic)
    state['used_categories'][key] = used
    return topic

def get_trending_context() -> str:
    """Get real trending topics from X search."""
    try:
        result = subprocess.run(
            ['xurl', 'search', 'crypto OR ai OR tech lang:en -is:retweet', '-n', '5'],
            capture_output=True, text=True, timeout=15
        )
        data = json.loads(result.stdout)
        tweets = data.get('data', [])
        texts = [t.get('text', '')[:60] for t in tweets[:3]]
        return ' | '.join(texts) if texts else ''
    except:
        return ''

def generate_tweet(topic: str, state: dict) -> str:
    """Generate tweet, optionally informed by trending context."""
    context = get_trending_context()
    if context:
        log(f"Trending context: {context[:120]}...")
    
    used = state.get('used_templates', [])
    available = [t for t in TEMPLATES if t not in used]
    if not available:
        available = TEMPLATES[:]
        used = []
    
    template = random.choice(available)
    used.append(template)
    state['used_templates'] = used
    
    tweet = template.format(topic=topic)
    return tweet[:280]

def xurl(*args) -> tuple[bool, dict]:
    """Run xurl command, return (success, parsed_json)."""
    cmd = ['xurl'] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        if result.returncode != 0 or 'errors' in data:
            error = data.get('errors', [{}])[0].get('detail', data.get('title', 'unknown'))
            return False, {'error': error}
        return True, data
    except Exception as e:
        return False, {'error': str(e)}

def post_tweet(tweet: str) -> str | None:
    """Post via xurl. Returns tweet ID or None."""
    ok, data = xurl('post', tweet)
    if ok:
        tid = data.get('data', {}).get('id', '')
        log(f"POSTED: {tid} — {tweet[:60]}")
        return tid
    else:
        log(f"FAIL: {data.get('error', 'unknown')}")
        return None

def run_cycle():
    log("═" * 40)
    state = load_state()
    state['total_posts'] += 1
    
    slot = get_current_slot()
    slot_info = TOPIC_SLOTS[slot]
    log(f"Slot {slot}: {slot_info['label']}")
    
    topic = pick_topic(state, slot)
    log(f"Topic: {topic}")
    
    tweet = generate_tweet(topic, state)
    if not tweet or len(tweet) < 20:
        log("ERROR: Failed to generate tweet")
        return
    
    log(f"Tweet ({len(tweet)}c): {tweet[:80]}")
    
    tid = post_tweet(tweet)
    state['last_slot'] = slot
    state['last_post'] = datetime.now().isoformat()
    if tid:
        state['last_tweet_id'] = tid
    save_state(state)
    
    log(f"DONE {'✅' if tid else '❌'} Total: {state['total_posts']}")

if __name__ == '__main__':
    run_cycle()
