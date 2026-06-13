"""Playwright Browser Automation — Login & Post to X/Twitter"""
import time
import random
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser
from .core import settings, log, state

# ─── Constants ───────────────────────────────────────────
X_URL = "https://x.com"
LOGIN_URL = "https://x.com/i/flow/login"
HOME_URL = "https://x.com/home"

# Human-like delays (ms)
TYPING_DELAY_MIN = 30
TYPING_DELAY_MAX = 120
ACTION_DELAY_MIN = 500
ACTION_DELAY_MAX = 2000


class XBrowser:
    """Handles Playwright browser, login, and posting to X."""

    def __init__(self):
        self.playwright = None
        self.browser: Browser | None = None
        self.page: Page | None = None
        self._logged_in = False

    def _random_delay(self, min_ms: int = None, max_ms: int = None):
        """Human-like random delay between actions."""
        time.sleep(random.uniform(
            min_ms or ACTION_DELAY_MIN,
            max_ms or ACTION_DELAY_MAX
        ) / 1000)

    def _human_type(self, selector: str, text: str):
        """Type text with human-like delays between keystrokes."""
        el = self.page.wait_for_selector(selector, timeout=10000)
        el.click()
        for char in text:
            el.type(char, delay=random.randint(TYPING_DELAY_MIN, TYPING_DELAY_MAX))
            if char in ".,!?\n":
                time.sleep(random.uniform(0.1, 0.3))  # Pause after punctuation

    def launch(self):
        """Launch browser with persistent context (saves cookies)."""
        log.info("Launching browser...")
        self.playwright = sync_playwright().start()

        # Persistent context — saves session to avoid re-login
        user_data = Path(settings.BROWSER_DATA_DIR)
        user_data.mkdir(parents=True, exist_ok=True)

        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data),
            headless=settings.HEADLESS,
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
        )
        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        log.info("Browser launched")

    def login(self) -> bool:
        """Login to X. Returns True if already logged in or login successful."""
        log.info("Checking login state...")
        self.page.goto(HOME_URL, wait_until="domcontentloaded")
        self._random_delay(2000, 4000)

        # Check if already logged in (home page has timeline)
        if self.page.url.startswith(HOME_URL) or "home" in self.page.url:
            log.info("✅ Already logged in (session cached)")
            self._logged_in = True
            return True

        # Need to login
        log.info("Not logged in — performing login...")
        if not settings.X_EMAIL or not settings.X_PASSWORD:
            log.error("Missing X_EMAIL or X_PASSWORD in .env")
            return False

        self.page.goto(LOGIN_URL, wait_until="domcontentloaded")
        self._random_delay(2000, 3000)

        # Step 1: Enter email/username
        try:
            self._human_type('input[autocomplete="username"]', settings.X_EMAIL)
            self._random_delay(500, 1000)
            # Click "Next"
            self.page.keyboard.press("Enter")
            self._random_delay(2000, 4000)
        except Exception as e:
            log.error(f"Failed at email step: {e}")
            return False

        # Step 2: Handle "unusual login" / verification — try username
        try:
            # Sometimes X asks for username after email
            username_field = self.page.query_selector('input[data-testid="ocfEnterTextTextInput"]')
            if username_field:
                log.info("X asked for username verification")
                self._human_type('input[data-testid="ocfEnterTextTextInput"]', settings.X_USERNAME)
                self._random_delay(500, 1000)
                self.page.keyboard.press("Enter")
                self._random_delay(2000, 4000)
        except:
            pass  # Not always required

        # Step 3: Enter password
        try:
            self._human_type('input[autocomplete="current-password"]', settings.X_PASSWORD)
            self._random_delay(500, 1000)
            self.page.keyboard.press("Enter")
            self._random_delay(3000, 6000)
        except Exception as e:
            log.error(f"Failed at password step: {e}")
            return False

        # Verify login
        self.page.wait_for_url(f"{X_URL}/home**", timeout=15000)
        if "home" in self.page.url:
            log.info("✅ Login successful")
            self._logged_in = True
            return True
        else:
            log.error(f"Login failed — current URL: {self.page.url}")
            return False

    def post_tweet(self, content: str) -> str | None:
        """Post a tweet. Returns tweet ID or None if failed."""
        if not self._logged_in:
            log.error("Not logged in — call login() first")
            return None

        if len(content) > 280:
            log.warning(f"Tweet too long ({len(content)} chars), truncating")
            content = content[:277] + "..."

        log.info(f"Posting tweet: {content[:80]}...")

        try:
            self.page.goto(HOME_URL, wait_until="domcontentloaded")
            self._random_delay(2000, 3000)

            # Click the tweet compose area
            compose_box = self.page.wait_for_selector(
                '[data-testid="tweetTextarea_0"], [aria-label="Post text"], [data-testid="tweetTextarea"]',
                timeout=10000
            )
            compose_box.click()
            self._random_delay(500, 1000)

            # Type the tweet
            self._human_type('[data-testid="tweetTextarea_0"], [aria-label="Post text"]', content)
            self._random_delay(1000, 2000)

            # Click "Post" button
            post_button = self.page.wait_for_selector(
                '[data-testid="tweetButton"], [data-testid="tweetButtonInline"]',
                timeout=5000
            )
            post_button.click()

            # Wait for post to complete
            self._random_delay(3000, 5000)

            # Extract tweet ID from URL or DOM
            tweet_id = self._extract_tweet_id()
            if tweet_id:
                log.info(f"✅ Tweet posted: {tweet_id}")
                return tweet_id
            else:
                log.warning("Tweet posted but couldn't extract ID")
                return "posted"

        except Exception as e:
            log.error(f"Failed to post tweet: {e}")
            return None

    def _extract_tweet_id(self) -> str | None:
        """Extract tweet ID from the newly posted tweet."""
        try:
            # Try to get the first tweet link (most recent)
            links = self.page.query_selector_all('a[href*="/status/"]')
            if links:
                href = links[0].get_attribute("href")
                if href and "/status/" in href:
                    return href.split("/status/")[-1].split("?")[0]
        except:
            pass
        return None

    def close(self):
        """Clean shutdown."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        log.info("Browser closed")
