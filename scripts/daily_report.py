#!/usr/bin/env python3
"""Daily SocialBlast report — xurl edition with real metrics"""
import json, re, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path('/root/socialblast')
LOG_FILE = ROOT / 'logs' / 'poster.log'
STATE_FILE = ROOT / 'data' / 'poster_state.json'

WIB = timezone(timedelta(hours=7))
today = datetime.now(WIB).strftime('%Y-%m-%d')

# Get real metrics from X API
def get_xdata() -> dict:
    try:
        r = subprocess.run(['xurl', 'whoami'], capture_output=True, text=True, timeout=10)
        return json.loads(r.stdout).get('data', {})
    except:
        return {}

# Parse today's posts
posts_today = []
if LOG_FILE.exists():
    for line in LOG_FILE.read_text().splitlines():
        if today in line and 'POSTED:' in line:
            posts_today.append(line)

# Load state
state = {}
if STATE_FILE.exists():
    state = json.loads(STATE_FILE.read_text())

# Get real metrics
xd = get_xdata()
metrics = xd.get('public_metrics', {})

# Build report
print(f"📊 *@QuantumFomo Daily Report*")
print(f"📅 {today}")
print(f"")

# Today's activity
print(f"🚀 *Posts today:* {len(posts_today)}")
for i, post in enumerate(posts_today[-8:], 1):
    # Extract tweet ID and text
    match = re.search(r'POSTED: (\d+) — (.+)$', post)
    if match:
        tid, text = match.group(1), match.group(2)
        print(f"  {i}. {text[:70]}")
        print(f"     https://x.com/QuantumFomo/status/{tid}")
    else:
        print(f"  {i}. (posted)")

print(f"")

# Account stats
print(f"📈 *Account Stats:*")
print(f"  Followers: {metrics.get('followers_count', '?')}")
print(f"  Following: {metrics.get('following_count', '?')}")
print(f"  Total tweets: {metrics.get('tweet_count', '?')}")
print(f"  Likes received: {metrics.get('like_count', '?')}")

# Topic summary
used = state.get('used_categories', {})
if used:
    print(f"")
    print(f"🎯 *Recent topics:*")
    for slot, topics in sorted(used.items()):
        for t in topics[-2:]:
            print(f"  • {t}")

print(f"")
print(f"🔗 https://x.com/QuantumFomo")
