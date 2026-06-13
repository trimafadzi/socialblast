#!/bin/bash
# Cron wrapper: Generate reply drafts — OpenAI → pending_replies.json
cd /root/socialblast && python3 scripts/3_reply_helper.py --draft
