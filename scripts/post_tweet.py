"""Post tweet to X via Playwright + auth_token cookie
   
WORKING METHOD (after many iterations):
- Uses x.com/compose/post (dedicated compose page)
- keyboard.insert_text() — bypasses Draft.js issues
- Verifies via URL redirect to home
"""
import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright

token = json.loads(Path.home().joinpath('.xactions','auth.json').read_text())['auth_token']
tweet = sys.argv[1] if len(sys.argv) > 1 else 'gm ☕️'

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=['--no-sandbox'])
    ctx = b.new_context()
    ctx.add_cookies([{
        'name': 'auth_token', 'value': token,
        'domain': '.x.com', 'path': '/',
        'httpOnly': True, 'secure': True, 'sameSite': 'Lax'
    }])
    page = ctx.new_page()
    
    page.goto('https://x.com/compose/post', wait_until='domcontentloaded', timeout=20000)
    page.wait_for_timeout(2000)
    
    textarea = page.locator('[data-testid="tweetTextarea_0"]')
    if textarea.count() == 0:
        print('ERROR: no textarea'); b.close(); sys.exit(1)
    
    textarea.first.click()
    page.wait_for_timeout(200)
    page.keyboard.insert_text(tweet)
    page.wait_for_timeout(300)
    
    page.locator('[data-testid="tweetButton"]').first.click()
    page.wait_for_timeout(5000)
    
    if 'home' in page.url:
        print(f'OK: {tweet[:60]}...')
    else:
        print(f'WARN: still on {page.url}')
    
    b.close()
