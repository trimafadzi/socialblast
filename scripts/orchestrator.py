#!/usr/bin/env python3
"""SocialBlast Auto-Poster — Trending-first 🎯
Flow: Search trending → pick hottest topic → generate tweet → Pexels image → post
"""
import os, sys, json, random, subprocess, re
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

ROOT = Path('/root/socialblast')
LOG_FILE = ROOT / 'logs' / 'poster.log'
STATE_FILE = ROOT / 'data' / 'poster_state.json'
LOG_FILE.parent.mkdir(exist_ok=True)
STATE_FILE.parent.mkdir(exist_ok=True)

# ========== FALLBACK TOPICS (if trending fails) ==========
FALLBACK_TOPICS = [
    'crypto trading', 'AI breakthrough', 'blockchain technology',
    'machine learning', 'DeFi yield', 'neural network', 'quantum computing',
    'bull market signal', 'tech startup', 'candlestick pattern',
    'data science', 'cyber security', 'digital finance', 'robot automation',
]

# ========== TEMPLATE POOLS ==========
# Pool A: Curiosity hooks — bikin penasaran, ngajak mikir
CURIOSITY_TEMPLATES = [
    "the {topic} situation is getting crazy. am i the only one seeing this pattern? 👀",
    "ok {topic} is trending but nobody's talking about the REAL signal here... 🧵",
    "i found something weird about {topic} today. either i'm early or i'm wrong. you decide 🤔",
    "the data on {topic} is telling a story most people aren't ready to hear yet 📊",
    "5 years from now, {topic} will either be everywhere or nowhere. here's why i'm betting on the first one...",
    "just dug into {topic} numbers and... wait, is nobody else seeing this? 🔍",
]

# Pool B: Controversial/contrarian — provokasi diskusi
CONTROVERSIAL_TEMPLATES = [
    "hot take: everyone's wrong about {topic} and here's the one chart that proves it 📉",
    "unpopular opinion — {topic} is about to flip everything you thought you knew. fight me in the replies 👇",
    "the {topic} crowd is gonna hate this but... the numbers don't lie",
    "i'm calling it now: {topic} will be the biggest rug pull of 2026. change my mind 💀",
    "every 'expert' talking about {topic} right now is missing the most obvious thing...",
    "controversial? maybe. but {topic} is NOT what you think it is. let me explain...",
]

# Pool C: Engagement bait — ngajak reply, vote, share
ENGAGEMENT_TEMPLATES = [
    "drop your honest opinion on {topic} — i'll RT the best takes 🔥",
    "rate {topic} from 1-10 right now. i'll start: 8.5. your turn 👇",
    "which side are you on? {topic} 🟢 bullish or 🔴 bearish? reply with your reasoning",
    "{topic} just broke a key level. what's your next move? i'll go first in the replies...",
    "if you had to explain {topic} to a 5-year-old, what would you say? best answer gets a follow 🎓",
    "{topic} believers assemble 👇 drop a 🚀 if you're holding through the noise",
]

# Pool D: Alpha/foresight — bikin FOMO, "gw udah duluan"
ALPHA_TEMPLATES = [
    "real ones are already positioned in {topic}. the window isn't closed yet but it's closing ⏳",
    "been quietly accumulating {topic} plays. here's the thesis nobody's talking about... 🧠",
    "3 reasons {topic} is about to explode and why the smart money is already in: 1/",
    "while everyone's distracted by noise, {topic} is quietly building. don't be late 🚀",
    "{topic} alpha you won't find on the timeline. bookmarked this for later? 📌",
]

# Pool E: Question-based — polling style
QUESTION_TEMPLATES = [
    "honest question: is {topic} actually undervalued or are we all just coping? 🤷",
    "{topic} is everywhere rn. bullish signal or top signal? genuinely curious what you think",
    "how many of you are actually paying attention to {topic} vs just scrolling past? be real",
    "what's the ONE thing about {topic} that you wish more people understood? educate me 👇",
    "if {topic} does a 10x from here, will you be the one laughing or the one coping? 😂",
]

# Combined pool — pick randomly across all styles
TEMPLATES = (
    CURIOSITY_TEMPLATES + CONTROVERSIAL_TEMPLATES + 
    ENGAGEMENT_TEMPLATES + ALPHA_TEMPLATES + QUESTION_TEMPLATES
)

# ========== UTILS ==========
def log(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {'used_templates': [], 'total_posts': 0, 'recent_hashtags': []}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def xurl(*args) -> tuple[bool, dict]:
    cmd = ['xurl'] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        stdout = result.stdout.strip()
        if not stdout:
            return False, {'error': 'empty output'}
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            brace_start = stdout.find('{')
            if brace_start >= 0:
                depth = 0
                for i in range(brace_start, len(stdout)):
                    if stdout[i] == '{': depth += 1
                    elif stdout[i] == '}':
                        depth -= 1
                        if depth == 0:
                            data = json.loads(stdout[brace_start:i+1])
                            break
                else:
                    return False, {'error': 'unclosed JSON'}
            else:
                return False, {'error': 'no JSON'}
        if result.returncode != 0 or 'errors' in data:
            error = data.get('errors', [{}])[0].get('detail', data.get('title', 'unknown'))
            return False, {'error': error}
        return True, data
    except Exception as e:
        return False, {'error': str(e)}


# ========== TRENDING DETECTION ==========
def get_trending_topic(state: dict) -> str:
    """
    Search X for trending tweets → extract hottest topic.
    Returns a clean topic string like 'AI agents', 'Solana DeFi', etc.
    """
    # Search for trending crypto/AI/tech tweets
    search_queries = [
        'crypto OR ai OR tech lang:en -is:retweet',
        'blockchain OR defi OR nft lang:en -is:retweet',
        'machine learning OR artificial intelligence lang:en -is:retweet',
    ]
    
    # Spam/gambling words to filter
    SPAM_PATTERNS = re.compile(r'bet|casino|gambling|slot|poker|开云|博彩|体育|世界杯|预测|下注|bet\d+|roll|jackpot', re.IGNORECASE)
    NON_ENGLISH = re.compile(r'[\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af]')  # CJK characters
    
    all_words = []
    all_hashtags = []
    
    for query in search_queries:
        ok, data = xurl('search', query, '-n', '10')
        if not ok:
            continue
        
        tweets = data.get('data', [])
        for t in tweets:
            text = t.get('text', '')
            
            # Skip spam/non-English tweets
            if SPAM_PATTERNS.search(text) or NON_ENGLISH.search(text):
                continue
            
            # Extract hashtags
            hashtags = re.findall(r'#(\w+)', text)
            all_hashtags.extend([h.lower() for h in hashtags])
            
            # Extract $TICKERS (crypto)
            tickers = re.findall(r'\$([A-Z]{2,6})', text)
            all_hashtags.extend([t.lower() for t in tickers])
            
            # Extract key terms (capitalized or meaningful words)
            words = re.findall(r'\b[A-Z][a-z]{2,12}\b', text)
            all_words.extend(w.lower() for w in words)
            
            # Also grab 2-3 word phrases
            phrases = re.findall(r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){1,2})\b', text)
            all_hashtags.extend(p.lower() for p in phrases)
    
    # Count & filter
    stop_words = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'are', 'was', 'not', 'but'}
    
    # Count hashtags/tickers
    tag_counts = Counter([h for h in all_hashtags if h not in stop_words and len(h) > 2])
    
    # Count key words
    word_counts = Counter([w for w in all_words if w not in stop_words and len(w) > 3])
    
    # Merge: prefer hashtags/tickers, fall back to frequent words
    candidates = []
    
    for tag, count in tag_counts.most_common(5):
        if count >= 1:
            candidates.append((tag, count * 3))  # Hashtags weighted higher
    
    for word, count in word_counts.most_common(5):
        candidates.append((word, count))
    
    # Filter recently used topics
    recent = state.get('recent_topics', [])
    candidates = [(topic, score) for topic, score in candidates if topic not in recent[-5:]]
    
    if not candidates:
        log("⚠️ No trending topics found, using fallback")
        return random.choice(FALLBACK_TOPICS)
    
    # Pick the highest scoring topic
    topic, score = candidates[0]
    
    # Track in state to avoid repetition
    if 'recent_topics' not in state:
        state['recent_topics'] = []
    state['recent_topics'].append(topic)
    if len(state['recent_topics']) > 10:
        state['recent_topics'] = state['recent_topics'][-10:]
    
    log(f"🔍 Trending: '{topic}' (score: {score}, from {len(all_hashtags)} tags + {len(all_words)} words)")
    return topic


# ========== CONTENT GENERATION ==========
def generate_hashtags(topic: str) -> str:
    """Generate 1-2 relevant hashtags from trending topic."""
    # Extract key words, remove common words
    stop = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'have', 'are', 'was', 'not', 'but', 'its', 'his', 'her'}
    words = re.findall(r'\b[a-zA-Z]{4,}\b', topic)
    keywords = [w.lower() for w in words if w.lower() not in stop]
    
    # Map to common crypto/tech hashtags
    tag_map = {
        'bitcoin': ['#Bitcoin', '#BTC'],
        'ethereum': ['#Ethereum', '#ETH'],
        'solana': ['#Solana', '#SOL'],
        'defi': ['#DeFi', '#Web3'],
        'ai': ['#AI', '#ArtificialIntelligence'],
        'artificial': ['#AI', '#MachineLearning'],
        'intelligence': ['#AI', '#TechTrends'],
        'crypto': ['#Crypto', '#Bullish'],
        'blockchain': ['#Blockchain', '#Web3'],
        'nft': ['#NFT', '#DigitalArt'],
        'trading': ['#Trading', '#Markets'],
        'market': ['#Markets', '#Finance'],
        'tech': ['#Tech', '#Innovation'],
        'data': ['#Data', '#Analytics'],
        'robot': ['#Robotics', '#Automation'],
        'neural': ['#NeuralNetwork', '#DeepLearning'],
        'quantum': ['#QuantumComputing', '#Tech'],
        'security': ['#CyberSecurity', '#Infosec'],
        'finance': ['#Finance', '#Fintech'],
        'yield': ['#Yield', '#DeFi'],
        'bull': ['#BullMarket', '#Crypto'],
        'bear': ['#BearMarket', '#Trading'],
    }
    
    tags = []
    for kw in keywords:
        if kw in tag_map:
            tags.extend(tag_map[kw])
    
    # Deduplicate, pick 1-2
    seen = set()
    result = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            result.append(t)
        if len(result) >= 2:
            break
    
    if not result:
        result = ['#Crypto', '#Trending'] if 'crypto' in topic.lower() else ['#Tech', '#Trending']
    
    return ' '.join(result[:2])


def generate_tweet(topic: str, state: dict) -> str:
    """Generate tweet about a trending topic — engaging, curiosity-driven."""
    used = state.get('used_templates', [])
    available = [t for t in TEMPLATES if t not in used]
    if not available:
        available = TEMPLATES[:]
        used = []
    
    template = random.choice(available)
    used.append(template)
    state['used_templates'] = used
    
    tweet = template.format(topic=topic)
    
    # Add hashtags for discoverability (skip if template already has one)
    if '#' not in tweet:
        hashtags = generate_hashtags(topic)
        tweet = f"{tweet}\n\n{hashtags}"
    
    return tweet[:280]


# ========== IMAGE ==========
def fetch_pexels_image(topic: str) -> Path | None:
    """Get Pexels photo matching the trending topic. Returns local file path (no upload)."""
    try:
        sys.path.insert(0, str(ROOT))
        from src.image_gen import get_image
        
        # Pass trending topic as search query
        img_path = get_image(topic=topic, slot=0)
        
        if not img_path:
            log("IMG: No Pexels photo found")
            return None
        
        log(f"IMG fetched: {img_path}")
        return img_path
    except Exception as e:
        log(f"IMG FAIL: {e}")
        return None


# ========== POSTING ==========
PLAYWRIGHT_POSTER = Path('/root/.hermes/scripts/playwright_poster.py')

def post_tweet(tweet_text: str, image_path: Path | None = None) -> str | None:
    """Post tweet via Playwright (no API credits). Returns tweet ID on success."""
    cmd = [sys.executable, str(PLAYWRIGHT_POSTER), tweet_text]
    if image_path and image_path.exists():
        cmd.append(str(image_path))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=45, cwd='/root')
        if result.returncode == 0:
            # Silent success = posted
            log(f"POSTED {'📸' if image_path else '📝'}: {tweet_text[:60]}")
            return f"pw_{int(datetime.now().timestamp())}"  # synthetic ID
        else:
            error = result.stderr.strip() or result.stdout.strip() or 'unknown'
            log(f"FAIL: {error}")
            return None
    except subprocess.TimeoutExpired:
        log("FAIL: Playwright timeout (45s)")
        return None
    except Exception as e:
        log(f"FAIL: {e}")
        return None


# ========== MAIN CYCLE ==========
def run_cycle():
    log("═" * 40)
    state = load_state()
    state['total_posts'] += 1
    
    # 1. Get trending topic
    topic = get_trending_topic(state)
    log(f"Topic: {topic}")
    
    # 2. Generate tweet
    tweet = generate_tweet(topic, state)
    if not tweet or len(tweet) < 20:
        log("ERROR: Failed to generate tweet")
        return
    
    log(f"Tweet ({len(tweet)}c): {tweet[:80]}")
    
    # 3. Get matching image from Pexels
    img_path = fetch_pexels_image(topic)
    
    # 4. Post via Playwright
    tid = post_tweet(tweet, image_path=img_path)
    state['last_post'] = datetime.now().isoformat()
    if tid:
        state['last_tweet_id'] = tid
    save_state(state)
    
    log(f"DONE {'✅' if tid else '❌'} Total: {state['total_posts']} | {'📸 img' if img_path else '📝 text'}")


if __name__ == '__main__':
    run_cycle()
