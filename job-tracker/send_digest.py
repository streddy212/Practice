"""Stage 3: email yourself a digest of new leads since the last digest,
best matches first, then mark them as sent so tomorrow's digest doesn't
repeat them.

Needs two settings, read from environment variables (or a local `.env`
file -- see `.env.example`, copy it to `.env` and fill in your own
values; `.env` is gitignored, never commit real credentials):

  DIGEST_EMAIL_ADDRESS       -- your Gmail address (sends to itself)
  DIGEST_EMAIL_APP_PASSWORD  -- a Gmail App Password, NOT your normal
                                 password. Generate one at
                                 https://myaccount.google.com/apppasswords
                                 (requires 2-Step Verification to be on).
"""
import os
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

from app import DB_PATH, init_db

MAX_LEADS_IN_DIGEST = 20
ENV_PATH = Path(__file__).parent / ".env"


def load_env_file(path: Path = ENV_PATH) -> None:
    """Minimal .env loader -- this is all `python-dotenv` does under the
    hood, small enough to not need the dependency."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def fetch_pending_leads(db: sqlite3.Connection) -> list[sqlite3.Row]:
    return db.execute(
        """
        SELECT id, company, role, score, notes, url
        FROM applications
        WHERE status = 'New Lead' AND notified_at IS NULL
        ORDER BY score DESC, id DESC
        LIMIT ?
        """,
        (MAX_LEADS_IN_DIGEST,),
    ).fetchall()


def format_digest(leads: list[sqlite3.Row]) -> str:
    lines = [f"{len(leads)} new lead(s) since your last digest, best match first:\n"]
    for lead in leads:
        lines.append(f"[score {lead['score']}] {lead['company']} -- {lead['role']}")
        lines.append(f"  {lead['url']}")
        lines.append(f"  {lead['notes']}")
        lines.append("")
    return "\n".join(lines)


def send_email(address: str, app_password: str, body: str, lead_count: int) -> None:
    msg = MIMEText(body)
    msg["Subject"] = f"Job Tracker: {lead_count} new lead(s)"
    msg["From"] = address
    msg["To"] = address

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
        server.starttls()
        server.login(address, app_password)
        server.send_message(msg)


def main() -> None:
    load_env_file()
    address = os.environ.get("DIGEST_EMAIL_ADDRESS")
    app_password = os.environ.get("DIGEST_EMAIL_APP_PASSWORD")
    if not address or not app_password:
        print("DIGEST_EMAIL_ADDRESS / DIGEST_EMAIL_APP_PASSWORD not set -- copy .env.example to .env and fill it in. Skipping digest.")
        return

    init_db()
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    leads = fetch_pending_leads(db)

    if not leads:
        print("No new leads to send.")
        db.close()
        return

    body = format_digest(leads)
    try:
        send_email(address, app_password, body, len(leads))
    except (smtplib.SMTPException, OSError) as exc:
        print(f"Could not send digest email ({exc}). Leads stay unmarked, will retry next run.")
        db.close()
        return

    now = datetime.now(timezone.utc).isoformat()
    db.executemany(
        "UPDATE applications SET notified_at = ? WHERE id = ?",
        [(now, lead["id"]) for lead in leads],
    )
    db.commit()
    db.close()
    print(f"Sent digest with {len(leads)} lead(s) to {address}.")


if __name__ == "__main__":
    main()
