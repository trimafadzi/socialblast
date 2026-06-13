#!/bin/bash
# Cron wrapper: Generate reply drafts — OpenRouter → pending_replies.json
cd /root/socialblast && source .env 2>/dev/null && python3 scripts/3_reply_helper.py --draft
