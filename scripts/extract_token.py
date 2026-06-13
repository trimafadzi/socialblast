"""Extract X auth_token via Playwright — stealth edition"""
import sys, os, json
from pathlib import Path
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv('/root/socialblast/.env')

EMAIL = os.getenv('X_EMAIL')
USERNAME = os.getenv('X_USERNAME')
PASSWORD = os.getenv('X_PASSWORD')

if not all([EMAIL, USERNAME, PASSWORD]):
    print("❌ Missing credentials")
    print(f"   EMAIL={'✓' if EMAIL else '✗'}")
    print(f"   USERNAME={'✓' if USERNAME else '✗'}")
    print(f"   PASSWORD={'✓' if PASSWORD else '✗'}")
    sys.exit(1)

print(f"🔐 Logging in as @{USERNAME}...")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-blink-features=AutomationControlled', '--disable-dev-shm-usage']
    )
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        viewport={'width': 1280, 'height': 800},
        locale='en-US',
    )
    page = ctx.new_page()

    # Hide automation
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    """)

    # Step 1: Go to login page
    print("  → Loading login page...")
    page.goto("https://x.com/i/flow/login", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)

    # Step 2: Enter email
    print("  → Entering email...")
    selectors = [
        'input[autocomplete="username"]',
        'input[name="text"]',
    ]
    found = False
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=5000)
            page.fill(sel, EMAIL)
            page.keyboard.press("Enter")
            found = True
            print(f"     Used selector: {sel}")
            break
        except:
            continue

    if not found:
        page.screenshot(path="/tmp/x_step1_fail.png")
        print("  ❌ Could not find email field")
        print(f"     Current URL: {page.url}")
        print(f"     Screenshot: /tmp/x_step1_fail.png")
        ctx.close()
        browser.close()
        sys.exit(1)

    page.wait_for_timeout(3000)

    # Step 3: Handle username challenge
    try:
        uname = page.wait_for_selector('input[data-testid="ocfEnterTextTextInput"]', timeout=3000)
        if uname:
            print("  → X asked for username...")
            page.fill('input[data-testid="ocfEnterTextTextInput"]', USERNAME)
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)
    except:
        pass

    # Step 4: Enter password
    print("  → Entering password...")
    pw_selectors = [
        'input[autocomplete="current-password"]',
        'input[name="password"]',
    ]
    for sel in pw_selectors:
        try:
            page.wait_for_selector(sel, timeout=5000)
            page.fill(sel, PASSWORD)
            page.keyboard.press("Enter")
            print(f"     Used selector: {sel}")
            break
        except:
            continue

    # Step 5: Wait for redirect
    page.wait_for_timeout(6000)
    final_url = page.url
    print(f"  → Final URL: {final_url[:100]}")

    # Step 6: Get cookies
    cookies = ctx.cookies()
    auth_token = next((c['value'] for c in cookies if c['name'] == 'auth_token'), None)

    if auth_token:
        print(f"  ✅ SUCCESS! Token: {auth_token[:25]}...{auth_token[-10:]}")
        xdir = Path.home() / '.xactions'
        xdir.mkdir(exist_ok=True)
        (xdir / 'auth.json').write_text(json.dumps({"auth_token": auth_token}))
        print(f"  💾 Saved to ~/.xactions/auth.json")
    else:
        print("  ❌ No auth_token found in cookies")
        print(f"  Cookies: {[c['name'] for c in cookies]}")
        page.screenshot(path="/tmp/x_final.png")

    ctx.close()
    browser.close()
    print("Done!")
