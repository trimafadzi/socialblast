#!/usr/bin/env python3
"""Cron wrapper — runs orchestrator, silent output unless error"""
import subprocess, sys
from pathlib import Path

result = subprocess.run(
    [sys.executable, str(Path(__file__).parent / 'orchestrator.py')],
    capture_output=True, text=True, timeout=60
)

if result.returncode != 0:
    print(f"ERROR (exit {result.returncode}): {result.stderr[:500]}", file=sys.stderr)
    print(result.stdout, file=sys.stdout)
    sys.exit(1)
# else: silent — stdout goes to log file, nothing to deliver
