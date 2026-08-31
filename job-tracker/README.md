# Job Tracker (Stage 1)

A personal application tracker: log every internship/job opportunity you apply to,
see them all in one table, update status inline, and spot which ones need a follow-up.

## Run it

```bash
cd job-tracker
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

The first run creates `tracker.db` (a local SQLite database file) automatically.

## How it's built

- `app.py` — the Flask server: routes for viewing, adding, updating status, and deleting applications
- `templates/index.html` — the page itself (a form + a table), using Jinja2 to loop over your data
- `tracker.db` — your data, stored locally in SQLite (not committed to git)

## What's next (Stage 2)

A script that automatically pulls new listings from a few job sources and feeds
matches straight into this tracker, so you stop manually checking sites.
