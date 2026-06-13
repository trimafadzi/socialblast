#!/bin/bash
# SocialBlast — One-command setup
set -e

echo "🚀 SocialBlast Setup"
echo "===================="

cd "$(dirname "$0")/.."

# 1. Check Node.js
if ! command -v node &>/dev/null; then
    echo "❌ Node.js not found. Install: curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt install -y nodejs"
    exit 1
fi

# 2. Install npm deps
echo ""
echo "📦 Installing XActions..."
npm install xactions 2>&1 | tail -3

# 3. Install Python deps
echo ""
echo "🐍 Installing Python packages..."
pip install openai python-dotenv schedule rich 2>&1 | tail -3

# 4. Install Agent-Reach (from source)
if ! command -v agent-reach &>/dev/null; then
    echo ""
    echo "🌐 Installing Agent-Reach..."
    if [ ! -d /tmp/agent-reach ]; then
        git clone https://github.com/supersonic13/agent-reach.git /tmp/agent-reach
    fi
    pip install -e /tmp/agent-reach 2>&1 | tail -3
fi

# 5. Setup .env
if [ ! -f .env ]; then
    echo ""
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
    echo "   Edit .env with your X credentials and OpenAI key"
fi

# 6. Create XActions workflows
echo ""
echo "🔧 Creating XActions workflows..."
mkdir -p data

# Post workflow
cat > data/workflow-post.json << 'WORKFLOW'
{
  "name": "post-tweet",
  "description": "Post a single tweet",
  "steps": [
    {
      "action": "postTweet",
      "params": { "text": "{{content}}" }
    }
  ]
}
WORKFLOW

# Reply workflow
cat > data/workflow-reply.json << 'WORKFLOW'
{
  "name": "reply-tweet",
  "description": "Reply to a tweet",
  "steps": [
    {
      "action": "reply",
      "params": { 
        "tweetUrl": "{{url}}",
        "text": "{{content}}"
      }
    }
  ]
}
WORKFLOW

# Engage workflow (search + like + reply)
cat > data/workflow-engage.json << 'WORKFLOW'
{
  "name": "engage",
  "description": "Search and engage with tweets",
  "steps": [
    {
      "action": "searchTweets",
      "params": { "query": "{{query}}", "limit": 5 }
    },
    {
      "action": "like",
      "params": { "tweetUrl": "{{item.url}}" }
    },
    {
      "action": "delay",
      "params": { "ms": 5000 }
    }
  ]
}
WORKFLOW

echo ""
echo "✅ Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env file with your credentials"
echo "  2. Run: python3 src/orchestrator.py --setup"
echo "  3. Run: python3 src/orchestrator.py --cycle"
echo "  4. Add cron: */120 * * * * cd /root/socialblast && python3 src/orchestrator.py --cycle"
