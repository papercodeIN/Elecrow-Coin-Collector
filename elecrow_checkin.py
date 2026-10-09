import os
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
CHECKIN_API = "https://www.elecrow.com/rewardpoints/redemption/ajaxCheckIn"

HEADLESS = "--headless" in sys.argv or "--scheduled" in sys.argv


def run():
    print(f"\n[START] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=300 if not HEADLESS else 0)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        print("[1/4] Navigating to login page...")
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(3000)

        print("[2/4] Logging in...")
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

        print("[3/4] Navigating to projects page...")
        page.goto(PROJECTS_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        print("[4/4] Performing daily check-in...")
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
        print("\n[DONE] Daily check-in automation complete!")
        page.screenshot(path="checkin_result.png", full_page=False)
        print("[SCREENSHOT] Saved to checkin_result.png")
        browser.close()


if __name__ == "__main__":
    run()
