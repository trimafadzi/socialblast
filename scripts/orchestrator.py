#!/usr/bin/env python3
"""SocialBlast Auto-Poster — 4x/day smart topic rotation"""
import os, sys, json, random, subprocess, time
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).parent.parent
LOG_FILE = ROOT / 'logs' / 'poster.log'
STATE_FILE = ROOT / 'data' / 'poster_state.json'
LOG_FILE.parent.mkdir(exist_ok=True)
STATE_FILE.parent.mkdir(exist_ok=True)

# ========== TOPIC POOL ==========
TOPIC_SLOTS = {
    0: {
        'label': '🌅 Morning Alpha',
        'categories': [
            'morning crypto update',
            'fresh AI tool drop',
            'bold daily prediction',
            'contrarian market take',
            'overnight on-chain alpha',
        ]
    },
    1: {
        'label': '☀️ Midday Fire',
        'categories': [
            'chart pattern insight',
            'dev productivity hot take',
            'underrated project shout-out',
            'trading psychology tip',
            'alpha most people miss',
        ]
    },
    2: {
        'label': '🌤 Afternoon Insight',
        'categories': [
            'AI vs crypto intersection',
            'lesson from a failed trade',
            '6-month tech prediction',
            'data-driven observation',
            'crypto narrative analysis',
        ]
    },
    3: {
        'label': '🌙 Night Thought',
        'categories': [
            'building in public reflection',
            'market day recap',
            '"smart money" move',
            'unpopular crypto opinion',
            'deep thought on AI future',
        ]
    },
}

# Smart templates that feel human
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
    "just spent an hour deep-diving {topic}. here's my raw take — thread later 👇",
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
    log(f"Topic: [{slot_info['label']}] {topic}")
    return topic

def generate_tweet(topic: str, state: dict) -> str:
    """Try XActions AI first, fall back to smart templates."""
    
    # Try XActions AI
    try:
        result = subprocess.run(
            ['npx', 'xactions', 'ai', 'generate',
             f"Write a single tweet about {topic}. Natural voice, casual tone, no hashtags, no emoji spam. Just one sharp insight. Max 280 chars."],
            cwd=ROOT, capture_output=True, text=True, timeout=25
        )
        text = (result.stdout + result.stderr).strip()
        for line in text.split('\n'):
            line = line.strip()
            if line and 40 < len(line) < 280 and not line.startswith(('⚡','✔','✗','→','-','[')):
                if 'error' not in line.lower() and 'auth' not in line.lower():
                    return line[:280]
    except:
        pass
    
    # Smart fallback templates
    used = state.get('used_templates', [])
    available = [t for t in TEMPLATES if t not in used]
    if not available:
        available = TEMPLATES[:]
        used = []
    
    template = random.choice(available)
    used.append(template)
    state['used_templates'] = used
    
    tweet = template.format(topic=topic)
    
    # Add occasional newline for multi-line tweets (20% chance)
    if random.random() < 0.2 and len(tweet) > 120:
        mid = len(tweet) // 2
        punct = [i for i, c in enumerate(tweet[60:-60], 60) if c in '.!?']
        if punct:
            split = random.choice(punct) + 1
            tweet = tweet[:split] + '\n' + tweet[split:].strip()
    
    return tweet[:280]

def post_tweet(tweet: str):
    script = ROOT / 'scripts' / 'post_tweet.py'
    result = subprocess.run(
        ['python3', str(script), tweet],
        cwd=ROOT, capture_output=True, text=True, timeout=35
    )
    output = result.stdout.strip()
    if 'OK:' in output:
        log(f"POSTED: {output}")
        return True
    else:
        log(f"FAIL: {output[:200]}")
        return False

def run_cycle():
    log("═" * 40)
    state = load_state()
    state['total_posts'] += 1
    
    slot = get_current_slot()
    log(f"Slot {slot}: {TOPIC_SLOTS[slot]['label']}")
    
    topic = pick_topic(state, slot)
    tweet = generate_tweet(topic, state)
    
    if not tweet or len(tweet) < 20:
        log("ERROR: Failed to generate tweet")
        return
    
    log(f"Tweet ({len(tweet)}c): {tweet[:80]}...")
    
    success = post_tweet(tweet)
    state['last_slot'] = slot
    state['last_post'] = datetime.now().isoformat()
    save_state(state)
    
    if success:
        log(f"DONE ✅ Total: {state['total_posts']}")
    else:
        log("DONE ❌")

if __name__ == '__main__':
    run_cycle()
