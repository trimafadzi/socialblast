"""
Pexels Image Fetcher — Free stock photos for social media
Uses curl subprocess + key from .pk file
"""
import os
import random
import json
import subprocess
from pathlib import Path

# Load key from env var or .pk file
KEY = os.getenv('PEXELS_API_KEY', '')
if not KEY:
    kf = Path(__file__).parent.parent / '.pk'
    if kf.exists():
        KEY = kf.read_text().strip()

OUT_DIR = Path('/root/socialblast/data/images')
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_QUERIES = [
    # Crypto
    'crypto trading', 'blockchain technology', 'digital finance',
    'stock market chart', 'trading desk', 'bitcoin mining',
    'candlestick chart', 'bull market', 'financial markets',
    # AI / Tech
    'artificial intelligence', 'machine learning', 'neural network',
    'robot automation', 'data center server', 'futuristic technology',
    'tech startup office', 'abstract technology', 'quantum computing',
    'cyber security', 'coding programming', 'software development',
    'night city lights', 'dark office setup', 'data science',
]

def search_photos(query: str, count: int = 5) -> list[dict]:
    import urllib.parse
    encoded = urllib.parse.quote(query)
    url = f'https://api.pexels.com/v1/search?query={encoded}&per_page={count}&orientation=landscape'
    try:
        r = subprocess.run(['curl', '-s', '-H', f'Authorization: {KEY}', url],
                          capture_output=True, text=True, timeout=15)
        return json.loads(r.stdout).get('photos', [])
    except Exception as e:
        print(f"Pexels API error: {e}")
        return []

def download_photo(photo: dict, filename: str) -> Path | None:
    img_url = photo.get('src', {}).get('large') or photo.get('src', {}).get('original')
    if not img_url:
        return None
    filepath = OUT_DIR / filename
    try:
        subprocess.run(['curl', '-s', '-L', '-o', str(filepath), img_url],
                      capture_output=True, text=True, timeout=30)
        if filepath.exists() and filepath.stat().st_size > 1000:
            return filepath
        return None
    except Exception as e:
        print(f"Download error: {e}")
        return None

def get_image(topic: str = 'crypto', slot: int = 1) -> Path | None:
    """Get a Pexels photo for a tweet. Uses topic as search query."""
    if not KEY:
        return None
    
    # First try: exact trending topic as query
    photos = search_photos(topic, count=5)
    
    # Fallback: random query from pool
    if not photos:
        query = random.choice(SEARCH_QUERIES)
        photos = search_photos(query, count=5)
    
    if not photos:
        return None
    
    photo = random.choice(photos)
    photographer = photo.get('photographer', 'unknown').replace(' ', '_')[:20]
    filename = f"pexels_{photographer}_{photo['id']}.jpg"
    path = download_photo(photo, filename)
    if path:
        print(f"Photo by {photo.get('photographer', 'unknown')} on Pexels: {photo.get('url', '')}")
    return path

if __name__ == '__main__':
    path = get_image('crypto', slot=1)
    if path:
        print(f"OK: {path} ({path.stat().st_size // 1024}KB)")
    else:
        print("FAIL")
