#!/usr/bin/env python3
"""Daily SocialBlast report — posts, topics, stats"""
import json, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path('/root/socialblast')
LOG_FILE = ROOT / 'logs' / 'poster.log'
STATE_FILE = ROOT / 'data' / 'poster_state.json'

WIB = timezone(timedelta(hours=7))
today = datetime.now(WIB).strftime('%Y-%m-%d')

# Parse today's posts from log
posts_today = []
if LOG_FILE.exists():
    for line in LOG_FILE.read_text().splitlines():
        if today in line and 'POSTED:' in line:
            posts_today.append(line)

# Parse state
state = {}
if STATE_FILE.exists():
    state = json.loads(STATE_FILE.read_text())

total = state.get('total_posts', 0)
last_slot = state.get('last_slot', -1)

# Generate report
print(f"📊 *SocialBlast Daily Report*")
print(f"📅 {today}")
print(f"")
print(f"🚀 *Posts today:* {len(posts_today)}")
for i, post in enumerate(posts_today, 1):
    # Extract tweet text
    match = re.search(r'POSTED: OK: (.+)\.\.\.$', post)
    if match:
        print(f"  {i}. {match.group(1)[:80]}")
    else:
        print(f"  {i}. (posted)")

print(f"")
print(f"📈 *Total all-time:* {total} posts")
print(f"📂 *State:* slot={last_slot}")

# Topic usage
used = state.get('used_categories', {})
if used:
    print(f"🎯 *Topics used:*")
    for slot, topics in sorted(used.items()):
        topic_list = ', '.join(topics[-3:])  # last 3 per slot
        print(f"  Slot {slot}: {topic_list}")

print(f"")
print(f"🔗 https://x.com/QuantumFomo")
