import os
import random
import sys
import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

EMAIL = os.getenv("ELECROW_EMAIL")
PASSWORD = os.getenv("ELECROW_PASSWORD")

if not EMAIL or not PASSWORD:
    print("[ERROR] Set ELECROW_EMAIL and ELECROW_PASSWORD in .env file")
    sys.exit(1)

LOGIN_URL = "https://www.elecrow.com/customer/account/login/"
PROJECTS_URL = "https://www.elecrow.com/share-projects.html"
LATEST_URL = "https://www.elecrow.com/share/sharepj/lists?type=latest"
CHECKIN_API = "https://www.elecrow.com/rewardpoints/redemption/ajaxCheckIn"
COINS_URL = "https://www.elecrow.com/rewardpoints/coins/"
DAILY_LIKE_LIMIT = 5
LIKE_PAGE_LIMIT = 10
LIKE_DELAY_MIN = 8
LIKE_DELAY_MAX = 20

HEADLESS = "--headless" in sys.argv or "--scheduled" in sys.argv
SKIP_LIKES = "--skip-likes" in sys.argv


def read_coin_status(page):
    page.goto(COINS_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    rows = page.eval_on_selector_all(
        "table tr",
        "els => els.map(e => Array.from(e.querySelectorAll('td,th')).map(c => c.innerText.trim()))",
    )
    balance = 0
    likes_today = 0
    today = datetime.date.today()
    for row in rows:
        if len(row) == 4 and row[0].isdigit():
            balance = int(row[0])
        if len(row) >= 4 and "Like a Project" in row[0]:
            try:
                entry_date = datetime.datetime.strptime(row[3], "%m/%d/%y").date()
            except ValueError:
                continue
            if entry_date == today:
                likes_today += 1
    return balance, likes_today


def candidate_project_ids(page):
    seen = set()
    urls = [PROJECTS_URL] + [f"{LATEST_URL}&page={page_num}" for page_num in range(1, LIKE_PAGE_LIMIT + 1)]
    for url in urls:
        print(f"[SCAN] {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)
        items = page.eval_on_selector_all(
            ".item_icon_collect",
            """
            els => els.map(e => {
                const card = e.closest('.latest_item') || e.closest('li');
                const link = card ? card.querySelector('a[href*="/sharepj/"]') : null;
                return {id: e.getAttribute('data-id'), liked: e.getAttribute('data-like'), href: link ? link.href : null};
            })
            """,
        )
        fresh = []
        for item in items:
            share_id = item.get("id")
            href = item.get("href")
            if not share_id or not href or item.get("liked") == "1" or share_id in seen:
                continue
            seen.add(share_id)
            fresh.append((share_id, href))
        random.shuffle(fresh)
        for share_id, href in fresh:
            yield share_id, href


def like_projects(page):
    balance_before, likes_today = read_coin_status(page)
    remaining = DAILY_LIKE_LIMIT - likes_today
    print(f"[LIKES] Balance: {balance_before} coins, likes credited today: {likes_today}")

    if remaining <= 0:
        print("[INFO] Daily like coin limit already reached.")
        return balance_before

    coins_gained = 0
    balance_after = balance_before
    for share_id, href in candidate_project_ids(page):
        if coins_gained >= remaining:
            break

        try:
            page.goto(href, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(1500)
            state = page.locator(".overview_collect").get_attribute("data-like")
            verified_id = page.locator("#detailsView").get_attribute("data-id")
            if verified_id:
                share_id = verified_id
            if state == "1":
                print(f"[SKIP] Project {share_id} is already liked.")
                continue
        except Exception as e:
            print(f"[WARN] Could not verify project {share_id}: {e}")
            continue

        delay = random.randint(LIKE_DELAY_MIN * 1000, LIKE_DELAY_MAX * 1000)
        print(f"[WAIT] {delay / 1000:.1f}s before liking project {share_id}")
        page.wait_for_timeout(delay)

        try:
            response = page.evaluate(
                """
                async (shareId) => {
                    const res = await fetch('/share/like/save/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        credentials: 'include',
                        body: 'share_id=' + encodeURIComponent(shareId)
                    });
                    return await res.text();
                }
                """,
                share_id,
            )
        except Exception as e:
            print(f"[WARN] Like request failed for {share_id}: {e}")
            continue

        balance_now, likes_now = read_coin_status(page)
        balance_after = balance_now
        if balance_now > balance_before + coins_gained:
            coins_gained = balance_now - balance_before
            print(f"[LIKE] Project {share_id} liked (+1 coin), balance: {balance_now}")
        else:
            print(f"[WARN] No coin awarded for project {share_id}: {response}")
            if likes_now >= DAILY_LIKE_LIMIT:
                print("[INFO] Daily like coin limit reached.")
                break

    print(f"[LIKES] Gained {coins_gained} coin(s) today, balance: {balance_after}")
    return balance_after


def run():
    print(f"\n[START] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=300 if not HEADLESS else 0)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        print("[1/5] Navigating to login page...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        print("[2/5] Logging in...")
        page.fill("#email", EMAIL)
        page.fill("#pass", PASSWORD)
        page.click("#send2")
        page.wait_for_load_state("networkidle", timeout=60000)
        page.wait_for_timeout(3000)

        if "customer/account" in page.url and "login" not in page.url:
            print("[OK] Login successful!")
        else:
            current = page.url
            if "login" in current:
                print("[ERROR] Login failed. Check credentials.")
                browser.close()
                sys.exit(1)
            print(f"[INFO] Redirected to: {current}")

        print("[3/5] Navigating to projects page...")
        page.goto(PROJECTS_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        print("[4/5] Performing daily check-in...")
        checkin_btn = page.locator("img.check-in-img").first
        checked_btn = page.locator("img.checked-in-img").first

        already_checked = False
        try:
            if checked_btn.is_visible(timeout=3000):
                already_checked = True
        except Exception:
            pass

        if already_checked:
            print("[INFO] Already checked in today! No coins to collect.")
        else:
            try:
                response = page.evaluate("""
                    () => {
                        return new Promise((resolve, reject) => {
                            fetch('/rewardpoints/redemption/ajaxCheckIn', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                    'X-Requested-With': 'XMLHttpRequest'
                                },
                                credentials: 'include'
                            })
                            .then(r => r.json())
                            .then(data => resolve(data))
                            .catch(err => reject(err.toString()));
                        });
                    }
                """)
                print(f"[API Response] {response}")
                if isinstance(response, dict) and response.get("success") == "yes":
                    msg = response.get("msg", {})
                    title = msg.get("title", "")
                    content = msg.get("content", "")
                    print(f"[SUCCESS] {title}")
                    print(f"[COINS] {content}")
                else:
                    print("[INFO] Check-in response:", response)
            except Exception as e:
                print(f"[WARN] API call failed ({e}), trying button click...")
                try:
                    if checkin_btn.is_visible(timeout=5000):
                        checkin_btn.click()
                        page.wait_for_timeout(3000)
                        print("[OK] Check-in button clicked!")
                    else:
                        print("[INFO] Check-in button not found. May have already checked in.")
                except Exception as e2:
                    print(f"[ERROR] Could not check in: {e2}")

        page.wait_for_timeout(3000)
        screenshot_path = os.getenv("ELECROW_SCREENSHOT_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkin_result.png"))
        page.screenshot(path=screenshot_path, full_page=False)
        print(f"[SCREENSHOT] Saved to {screenshot_path}")

        print("[5/5] Liking projects for extra coins...")
        final_balance = None
        if SKIP_LIKES:
            print("[INFO] Like automation skipped (--skip-likes).")
        else:
            try:
                final_balance = like_projects(page)
            except Exception as e:
                print(f"[WARN] Like automation failed: {e}")

        if final_balance is None:
            try:
                final_balance, _ = read_coin_status(page)
            except Exception as e:
                print(f"[WARN] Could not read coin balance: {e}")

        if final_balance is not None:
            print(f"[COIN BALANCE] {final_balance} coins")

        print("\n[DONE] Daily check-in automation complete!")
        browser.close()


if __name__ == "__main__":
    run()
