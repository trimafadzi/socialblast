#!/usr/bin/env python3
"""Cron wrapper — runs orchestrator with random jitter for anti-detection"""
import subprocess, sys, random, time
from pathlib import Path

# Jitter: random 0-30 menit before posting (anti-pattern detection)
JITTER_SECS = random.randint(0, 1800)
if JITTER_SECS > 0:
    print(f"Jitter: {JITTER_SECS}s ({JITTER_SECS//60}m {JITTER_SECS%60}s)")
    time.sleep(JITTER_SECS)

ORCHESTRATOR = Path('/root/socialblast/scripts/orchestrator.py')

result = subprocess.run(
    [sys.executable, str(ORCHESTRATOR)],
    capture_output=True, text=True, timeout=60, cwd='/root/socialblast'
)

if result.returncode != 0:
    print(f"ERROR (exit {result.returncode})")
    if result.stderr:
        print(result.stderr[:500])
    if result.stdout:
        print(result.stdout[:500])
    sys.exit(1)
# Silent on success
