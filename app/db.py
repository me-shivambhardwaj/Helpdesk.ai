import sqlite3
import time
from .config import DB_PATH


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS tickets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at REAL, responded_at REAL,
        customer TEXT, subject TEXT, body TEXT,
        category TEXT, urgency TEXT, sentiment TEXT, summary TEXT,
        draft TEXT, confidence REAL, sources TEXT,
        status TEXT, final_reply TEXT)""")
    return c


def insert(t: dict) -> int:
    with conn() as c:
        cols = ", ".join(t.keys())
        marks = ", ".join("?" for _ in t)
        cur = c.execute(f"INSERT INTO tickets({cols}) VALUES({marks})", list(t.values()))
        return cur.lastrowid


def list_tickets(status=None):
    with conn() as c:
        if status:
            rows = c.execute("SELECT * FROM tickets WHERE status=? ORDER BY id DESC", (status,))
        else:
            rows = c.execute("SELECT * FROM tickets ORDER BY id DESC")
        return [dict(r) for r in rows.fetchall()]


def approve(ticket_id: int, final_reply: str):
    with conn() as c:
        c.execute("UPDATE tickets SET status='approved', final_reply=?, responded_at=? WHERE id=?",
                  (final_reply, time.time(), ticket_id))


def metrics() -> dict:
    rows = list_tickets()
    total = len(rows)
    auto = sum(r["status"] == "auto_resolved" for r in rows)
    times = [r["responded_at"] - r["created_at"] for r in rows if r["responded_at"]]
    by_status, by_cat = {}, {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    return {
        "total": total,
        "auto_resolved_pct": round(100 * auto / total, 1) if total else 0.0,
        "avg_response_seconds": round(sum(times) / len(times), 1) if times else None,
        "by_status": by_status,
        "by_category": by_cat,
    }


def get(ticket_id: int):
    with conn() as c:
        r = c.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
        return dict(r) if r else None
