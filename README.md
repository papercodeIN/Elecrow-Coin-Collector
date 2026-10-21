# Elecrow Daily Check-In Automation

Automated daily check-in for [Elecrow Project Community](https://www.elecrow.com/share-projects.html) to collect coins using Playwright (Python).

## What It Does

1. Logs into your Elecrow account
2. Navigates to the Projects page
3. Performs the daily check-in (POST to `/rewardpoints/redemption/ajaxCheckIn`)
4. Collects coins and logs the result
5. Likes up to 5 projects (1 coin per like, max 5 coins/day)
6. Saves a screenshot of the result

## Files

| File | Purpose |
|---|---|
| `elecrow_checkin.py` | Main automation script |
| `run_checkin.bat` | Batch launcher for Task Scheduler |
| `ElecrowCheckIn_Task.xml` | Windows Task Scheduler definition |
| `.env` | Credentials (email & password) |
| `checkin_log.txt` | Auto-generated log from scheduled runs |
| `checkin_result.png` | Screenshot from the last run |

## Setup

### Prerequisites

```
pip install playwright python-dotenv
python -m playwright install chromium
```

### Credentials

Edit `.env` in this folder:

```
ELECROW_EMAIL=your_email@example.com
ELECROW_PASSWORD=your_password
```

### Task Scheduler

The scheduled task `ElecrowDailyCheckIn` is already registered. To re-register or set up on another machine:

```
schtasks /Create /TN "ElecrowDailyCheckIn" /XML "C:\Users\Parrot\Desktop\Elecrow\ElecrowCheckIn_Task.xml" /F
```

To remove:

```
schtasks /Delete /TN "ElecrowDailyCheckIn" /F
```

## Task Scheduler Settings

| Setting | Value |
|---|---|
| Schedule | Daily at 9:00 AM |
| Missed run | Runs ASAP when system becomes available |
| On failure | Retries 3 times, 5 min apart |
| Network | Requires internet connection |
| Battery | Runs even on battery |
| Mode | Headless (no browser window) |
| Timeout | 10 minutes max |

## Manual Usage

Run with browser visible (for debugging):

```
python elecrow_checkin.py
```

Run headless (no window):

```
python elecrow_checkin.py --headless
```

Skip the project likes and only check in:

```
python elecrow_checkin.py --skip-likes
```

## Logs

Scheduled runs append output to `checkin_log.txt`. Check this file to verify daily runs:

```
type checkin_log.txt
```

Each multi-account run writes `multi_account/logs/<account>_<date>.log`. Every run ends with a `[COIN BALANCE] <n> coins` line so you can see the balance for each account.

## Multi-Account Safety

Run all accounts with randomized delays:

```
python multi_account/run_all.py --headless
```

Safety defaults:

- Likes are spaced **8-20 seconds** apart.
- Accounts are spaced **60-180 seconds** apart.
- Projects are shuffled for each account, so accounts do not all like the same projects.
- If all projects on the first page are already liked, it automatically scans further pages.

Options:

- `--account-delay-min 90 --account-delay-max 240` to slow down further
- `--shuffle` to randomize account order
- `--no-delay` to disable the wait (not recommended)

A full 11-account run now takes roughly 30-60 minutes.

## Coins System

- Daily check-in: **10 coins**
- Bonus for 7 consecutive days in a month: **50 coins**
- Like Project: **1 coin per like, max 5 coins/day** (5 different projects)
- Coins can be redeemed at [Elecrow Redemption Center](https://www.elecrow.com/redemption.html)

> Likes are state-based: if you unlike a project, the coin from that like is removed. The automation therefore likes 5 different projects and keeps them liked.

## GitHub Actions (no laptop needed)

Runs daily on GitHub at 9:00 UTC. Workflow file: `.github/workflows/Elecrow Daily Check-in.yml`.

1. Repo **Settings** → **Secrets and actions** → **New repository secret**
2. Add `ELECROW_EMAIL` and `ELECROW_PASSWORD`
3. **Actions** → **Elecrow Daily Check-in** → **Run workflow** to test
4. Logs and screenshot: open the run → **Artifacts** → `checkin-logs`

It keeps running every day after that. Public repo is fine.
