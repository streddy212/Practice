"""Stage 2: pull open roles from company job boards and drop keyword matches
straight into the tracker as "New Lead" rows.

Uses the free, public JSON APIs that Greenhouse and Lever expose for every
company's careers page -- no API key, no scraping, no login.

How to find a company's token:
  Greenhouse -> visit their careers page. If the URL looks like
      https://boards.greenhouse.io/coinbase
  the token is the last part: "coinbase".
  Lever -> same idea:
      https://jobs.lever.co/ramp
  token is "ramp".

Some companies host their own careers page but still run it on Greenhouse
or Lever under the hood -- check the page's network requests, or just try
both platforms with the company's obvious token.
"""
import sqlite3

import requests

from app import DB_PATH, init_db

# Add the companies you actually want to watch. `platform` must be
# "greenhouse" or "lever"; `token` is found as described above.
SOURCES = [
    {"company": "Addepar", "platform": "greenhouse", "token": "addepar1"},
    {"company": "iCapital Network", "platform": "greenhouse", "token": "icapitalnetwork"},
    {"company": "YipitData", "platform": "greenhouse", "token": "yipitdata"},
    {"company": "Messari", "platform": "greenhouse", "token": "messari"},
    {"company": "Alpaca", "platform": "greenhouse", "token": "alpaca"},
    {"company": "Plaid", "platform": "lever", "token": "plaid"},
    {"company": "Brex", "platform": "greenhouse", "token": "brex"},
    {"company": "Public", "platform": "greenhouse", "token": "public"},
    {"company": "Mercury", "platform": "greenhouse", "token": "mercury"},
    {"company": "Wealthfront", "platform": "lever", "token": "wealthfront"},
    {"company": "Anchorage Digital", "platform": "lever", "token": "anchorage"},
    {"company": "Kraken", "platform": "lever", "token": "kraken"},
    {"company": "Gemini", "platform": "greenhouse", "token": "gemini"},
    {"company": "FalconX", "platform": "greenhouse", "token": "falconx"},
    {"company": "Carta", "platform": "greenhouse", "token": "carta"},
    {"company": "Coinbase", "platform": "greenhouse", "token": "coinbase"},
    {"company": "DRW", "platform": "greenhouse", "token": "drweng"},
    {"company": "Flow Traders", "platform": "greenhouse", "token": "flowtraders"},
    # Marketing / Operations / Product
    {"company": "Faire", "platform": "greenhouse", "token": "faire"},
    {"company": "Webflow", "platform": "greenhouse", "token": "webflow"},
    {"company": "Chime", "platform": "greenhouse", "token": "chime"},
    {"company": "Allbirds", "platform": "greenhouse", "token": "allbirds"},
    {"company": "Warby Parker", "platform": "greenhouse", "token": "warbyparker"},
    {"company": "Flexport", "platform": "greenhouse", "token": "flexport"},
    {"company": "Attentive", "platform": "greenhouse", "token": "attentive"},
    {"company": "Airtable", "platform": "greenhouse", "token": "airtable"},
    {"company": "Robinhood", "platform": "greenhouse", "token": "robinhood"},
]

# Matched case-insensitively against each posting's title.
KEYWORDS = [
    "trading", "trader", "sales", "quant", "analyst", "intern", "research", "associate",
    "marketing", "operations", "product manager", "growth", "strategy", "brand",
]

REQUEST_TIMEOUT = 15


def fetch_greenhouse(token: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return [
        {"title": job["title"], "url": job["absolute_url"]}
        for job in resp.json().get("jobs", [])
    ]


def fetch_lever(token: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return [
        {"title": posting["text"], "url": posting["hostedUrl"]}
        for posting in resp.json()
    ]


FETCHERS = {"greenhouse": fetch_greenhouse, "lever": fetch_lever}


def matches_keywords(title: str) -> bool:
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in KEYWORDS)


def already_tracked(db: sqlite3.Connection, url: str) -> bool:
    row = db.execute("SELECT 1 FROM applications WHERE url = ?", (url,)).fetchone()
    return row is not None


def main() -> None:
    if not SOURCES:
        print("No SOURCES configured yet -- edit fetch_jobs.py and add some companies.")
        return

    init_db()
    db = sqlite3.connect(DB_PATH)
    added = 0

    for source in SOURCES:
        fetch = FETCHERS[source["platform"]]
        try:
            postings = fetch(source["token"])
        except requests.RequestException as exc:
            print(f"[skip] {source['company']}: could not fetch ({exc})")
            continue

        matched = [p for p in postings if matches_keywords(p["title"])]
        print(f"{source['company']}: {len(postings)} open roles, {len(matched)} match your keywords")

        for posting in matched:
            if already_tracked(db, posting["url"]):
                continue
            db.execute(
                """
                INSERT INTO applications (company, role, source, status, url)
                VALUES (?, ?, ?, 'New Lead', ?)
                """,
                (source["company"], posting["title"], f"{source['company']} ({source['platform']})", posting["url"]),
            )
            added += 1

    db.commit()
    db.close()
    print(f"\nAdded {added} new lead(s). Open the app to see them highlighted in blue.")


if __name__ == "__main__":
    main()
