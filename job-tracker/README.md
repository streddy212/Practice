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

1. Open `fetch_jobs.py` and add companies to `SOURCES`. To find a
   company's token, visit their careers page:
   - Greenhouse: `https://boards.greenhouse.io/<token>`
   - Lever: `https://jobs.lever.co/<token>`
   The last part of that URL is the token.
2. Adjust `KEYWORDS` to match what you're looking for.
3. Run it:
   ```bash
   python fetch_jobs.py
   ```
4. Refresh the tracker page — new matches show up as blue "New Lead" rows.
   Running it again never creates duplicates (it checks the posting URL
   first).

This sandbox's network is locked to package registries only, so the
Greenhouse/Lever calls were verified against mocked responses shaped like
the real API — run it for real from your own machine.

## How it's built

- `app.py` — the Flask server: routes for viewing, adding, updating status, and deleting applications
- `templates/index.html` — the page itself (a form + a table), using Jinja2 to loop over your data
- `fetch_jobs.py` — standalone script that fetches postings and inserts new leads
- `tracker.db` — your data, stored locally in SQLite (not committed to git)

## What's next (Stage 3)

Score incoming leads by how well they match your criteria, and email
yourself a daily digest of just the top matches.
