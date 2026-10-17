# Elecrow Daily Check-In Automation

Automated daily check-in for [Elecrow Project Community](https://www.elecrow.com/share-projects.html) to collect coins using Playwright (Python).

## What It Does

1. Logs into your Elecrow account
2. Navigates to the Projects page
3. Performs the daily check-in (POST to `/rewardpoints/redemption/ajaxCheckIn`)
4. Collects coins and logs the result
5. Saves a screenshot of the result

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

## Logs

Scheduled runs append output to `checkin_log.txt`. Check this file to verify daily runs:

```
type checkin_log.txt
```

## Coins System

- Daily check-in: **10 coins**
- Bonus for 7 consecutive days in a month: **50 coins**
- Coins can be redeemed at [Elecrow Redemption Center](https://www.elecrow.com/redemption.html)

## GitHub Actions (no laptop needed)

Runs daily on GitHub at 9:00 UTC. Workflow file: `.github/workflows/Elecrow Daily Check-in.yml`.

1. Repo **Settings** → **Secrets and actions** → **New repository secret**
2. Add `ELECROW_EMAIL` and `ELECROW_PASSWORD`
3. **Actions** → **Elecrow Daily Check-in** → **Run workflow** to test
4. Logs and screenshot: open the run → **Artifacts** → `checkin-logs`

It keeps running every day after that. Public repo is fine.
