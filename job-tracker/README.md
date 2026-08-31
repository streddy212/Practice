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

`SOURCES` currently watches 26 real companies across four functions:
- **Finance/trading:** Addepar, iCapital, Wealthfront (wealth-tech); YipitData (alt-data);
  Messari, Alpaca, Coinbase, Gemini, Kraken, Anchorage Digital, FalconX (crypto/trading);
  DRW (literal trading-internship program); Plaid, Brex, Mercury, Carta, Public (fintech infra)
- **Marketing:** Chime, Webflow, Attentive, Allbirds, Warby Parker
- **Operations:** Flexport, Faire, Robinhood
- **Product:** Airtable, Robinhood

(Some companies span more than one list — Robinhood posts both product and
ops roles, for example.) Add more the same way — visit a company's careers
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

### CPT/OPT/visa sponsorship — what's actually verified

Every new lead lands with a note in its Notes column about what's known
regarding sponsorship, not just the job title:

- **Plaid** — F-1 CPT/OPT explicitly accepted for the internship; the
  company states no immigration (H-1B) sponsorship is promised beyond that
- **Brex** — F-1 CPT/OPT explicitly accepted, international students
  encouraged to apply; verified H-1B sponsor for full-time roles
- **Coinbase** — internship visa sponsorship available for some roles,
  subject to approval, covers the internship duration only
- **Everyone else** — not verified. Web search could not surface reliable,
  company-specific statements for the rest of this list (it mostly returns
  generic OPT/CPT explainer articles, not each company's actual hiring
  page). Absence of a note does **not** mean confirmed sponsor-friendly —
  it means no explicit exclusion was found, so per the "avoid only on an
  explicit no" rule it stayed in the list. Confirm directly before
  investing real time in an application.

One company was removed entirely: **Flow Traders** explicitly states on
its own careers site that interns must already have the right to work in
the internship's country — no visa sponsorship for interns (their
full-time graduate program is different and does sponsor). That's a
confirmed exclusion, not a guess.

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

## Scoring and the email digest (Stage 3)

Every lead `fetch_jobs.py` inserts gets a numeric `score` so the best
matches surface first — the tracker sorts New Leads to the top, best
score first, automatically.

The formula is deliberately simple and readable in `score_posting()`
(`fetch_jobs.py`): the title is checked against three keyword tiers, each
match adds points (higher tier = closer to what you actually want),
plus a bonus if the company has a *verified* positive sponsorship
finding:
- High priority (+3 each): `trading`, `trader`, `quant`, `sales`
- Medium priority (+2 each): `product manager`, `marketing`, `operations`, `research`, `strategy`, `growth`, `brand`
- Low priority (+1 each): `analyst`, `intern`, `associate`
- Verified sponsorship bonus: +3 (Plaid, Brex) or +2 (Coinbase) — see the sponsorship section above

A title can match more than one tier and stack (e.g. "Quantitative
Trading Analyst Intern" scores 3+1+1 = 5), and the weights are just
numbers in the source — change them if a different function should
outrank the rest for you.

`send_digest.py` emails yourself the leads that showed up since your last
digest, best score first, then marks them so tomorrow's digest doesn't
repeat them. Set it up:

1. Turn on 2-Step Verification on your Google account, then generate an
   App Password at https://myaccount.google.com/apppasswords
2. Copy `.env.example` to `.env` and fill in your Gmail address and that
   app password. `.env` is gitignored — never commit it.
3. Run it: `python send_digest.py`

`run_fetch.sh` already calls both `fetch_jobs.py` and `send_digest.py` in
sequence, so once it's scheduled (see above) you get the full loop for
free: pull new postings → score them → email yourself the new ones →
mark them sent, with zero manual steps once it's running. No `.env`? It
prints a clear message and skips the email rather than failing the whole
run.

## How it's built

- `app.py` — the Flask server: routes for viewing, adding, updating status, and deleting applications; sorts New Leads to the top by score
- `templates/index.html` — the page itself (a form + a table), using Jinja2 to loop over your data
- `fetch_jobs.py` — fetches postings, scores them, inserts new leads
- `send_digest.py` — emails a digest of leads not yet notified about, then marks them sent
- `run_fetch.sh` — wrapper for scheduled runs; runs both scripts, logs each run to `fetch_log.txt`
- `.env` / `.env.example` — your email credentials (never committed) / the template for them
- `tracker.db` / `fetch_log.txt` — your data and run history, stored locally (not committed to git)

## What's next

Ideas for a Stage 4, if you want to keep going: a "sponsor confidence"
badge computed automatically instead of hand-written per company, a
weekly summary instead of (or alongside) the daily digest, or letting
the score weights be edited from the web UI instead of the source file.
