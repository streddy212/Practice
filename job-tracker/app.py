import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, url_for

DB_PATH = Path(__file__).parent / "tracker.db"
STATUSES = ["New Lead", "Applied", "OA / Assessment", "Interview", "Offer", "Rejected", "Ghosted"]

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                source TEXT,
                sponsors_visa TEXT NOT NULL DEFAULT 'unknown',
                status TEXT NOT NULL DEFAULT 'Applied',
                date_applied TEXT,
                follow_up_date TEXT,
                notes TEXT,
                url TEXT
            )
            """
        )
        # Migration for anyone who ran Stage 1 before the `url` column existed.
        try:
            db.execute("ALTER TABLE applications ADD COLUMN url TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists


@app.route("/")
def index():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM applications ORDER BY date_applied DESC, id DESC"
    ).fetchall()
    today = date.today().isoformat()
    return render_template(
        "index.html", applications=rows, statuses=STATUSES, today=today
    )


@app.route("/add", methods=["POST"])
def add():
    db = get_db()
    db.execute(
        """
        INSERT INTO applications
            (company, role, source, sponsors_visa, status, date_applied, follow_up_date, notes, url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request.form["company"].strip(),
            request.form["role"].strip(),
            request.form.get("source", "").strip(),
            request.form.get("sponsors_visa", "unknown"),
            request.form.get("status", "Applied"),
            request.form.get("date_applied") or date.today().isoformat(),
            request.form.get("follow_up_date") or None,
            request.form.get("notes", "").strip(),
            request.form.get("url", "").strip() or None,
        ),
    )
    db.commit()
    return redirect(url_for("index"))


@app.route("/update_status/<int:app_id>", methods=["POST"])
def update_status(app_id):
    db = get_db()
    db.execute(
        "UPDATE applications SET status = ? WHERE id = ?",
        (request.form["status"], app_id),
    )
    db.commit()
    return redirect(url_for("index"))


@app.route("/delete/<int:app_id>", methods=["POST"])
def delete(app_id):
    db = get_db()
    db.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    db.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
