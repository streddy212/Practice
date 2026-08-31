# Job Tracker

A personal job-search tool: track every application in one place, and
auto-pull new postings from company job boards so you stop manually
checking sites.

## Run the tracker (Stage 1)

```bash
cd job-tracker
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

The first run creates `tracker.db` (a local SQLite database file) automatically.

## Pull in new leads (Stage 2)

`fetch_jobs.py` checks a list of companies' public job boards (Greenhouse
and Lever both publish free, no-login JSON APIs) and drops anything
matching your keywords into the tracker as a "New Lead" row, highlighted
in blue.

`SOURCES` currently watches 18 real companies picked for fit with a
finance/data background — wealth-tech (Addepar, iCapital, Wealthfront),
alt-data (YipitData), fintech infra (Plaid, Brex, Mercury, Carta), and
crypto/trading (Messari, Alpaca, Coinbase, Gemini, Kraken, Anchorage
Digital, FalconX), plus two firms that run literal trading internships
(DRW, Flow Traders). Add more the same way — visit a company's careers
page, and if the URL looks like:
- Greenhouse: `https://boards.greenhouse.io/<token>`
- Lever: `https://jobs.lever.co/<token>`
the last part is the token.

Run it:
```bash
python fetch_jobs.py
```
Refresh the tracker page — new matches show up as blue "New Lead" rows.
Running it again never creates duplicates (it checks the posting URL
first).

This sandbox's network is locked to package registries only, so every
token above was verified via web search against the company's real
Greenhouse/Lever job-board URLs, and the fetch/parse/dedupe logic was
verified against mocked responses shaped like the real API — but the live
pull has to run from your own machine, where you have full internet
access.

## Make it run on its own

`fetch_jobs.py` needs real internet access, so "proactive" here means
scheduling it on your own computer (not this sandbox, which can't reach
Greenhouse/Lever directly) — the same way any personal automation runs
when you're not watching. `run_fetch.sh` wraps the script and appends a
timestamped result to `fetch_log.txt`, so you can check what happened
without opening a terminal.

**macOS / Linux (cron):**
```bash
crontab -e
```
Add a line (runs daily at 9am — adjust the path to where you cloned this repo):
```
0 9 * * * /full/path/to/job-tracker/run_fetch.sh
```

**Windows (Task Scheduler):**
```powershell
schtasks /create /tn "JobTrackerFetch" /tr "C:\path\to\job-tracker\run_fetch.sh" /sc daily /st 09:00
```
(or use the Task Scheduler GUI: Create Basic Task → Daily → set the action to run `run_fetch.sh` via WSL or Git Bash)

Once it's scheduled, check `fetch_log.txt` any time to see the last run's
results, or just open the tracker — new leads will already be waiting as
blue rows.

If you want this to keep running even when your laptop is off, the next
step up is a scheduled GitHub Actions workflow — worth doing once this
version has been running reliably for you locally.

## How it's built

- `app.py` — the Flask server: routes for viewing, adding, updating status, and deleting applications
- `templates/index.html` — the page itself (a form + a table), using Jinja2 to loop over your data
- `fetch_jobs.py` — standalone script that fetches postings and inserts new leads
- `run_fetch.sh` — wrapper for scheduled runs; logs each run to `fetch_log.txt`
- `tracker.db` / `fetch_log.txt` — your data and run history, stored locally (not committed to git)

## What's next (Stage 3)

Score incoming leads by how well they match your criteria, and email
yourself a daily digest of just the top matches.
