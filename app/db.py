import secrets
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
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        created_at REAL NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS sessions(
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at REAL NOT NULL,
        expires_at REAL NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""")
    return c


def create_user(email: str, password_hash: str) -> dict:
    with conn() as c:
        cur = c.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email.strip().lower(), password_hash, time.time())
        )
        return {"id": cur.lastrowid, "email": email.strip().lower()}


def get_user_by_email(email: str) -> dict | None:
    with conn() as c:
        r = c.execute("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (email.strip().lower(),)).fetchone()
        return dict(r) if r else None


def get_user_by_id(user_id: int) -> dict | None:
    with conn() as c:
        r = c.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(r) if r else None


def create_session(user_id: int, duration_days: int = 7) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    expires_at = now + (duration_days * 86400)
    with conn() as c:
        c.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now, expires_at)
        )
    return token


def get_user_by_session(token: str) -> dict | None:
    if not token:
        return None
    now = time.time()
    with conn() as c:
        r = c.execute(
            """
            SELECT u.id, u.email, u.created_at, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
            """,
            (token,)
        ).fetchone()
        if not r:
            return None
        if r["expires_at"] < now:
            c.execute("DELETE FROM sessions WHERE token = ?", (token,))
            return None
        return {"id": r["id"], "email": r["email"], "created_at": r["created_at"]}


def delete_session(token: str):
    if not token:
        return
    with conn() as c:
        c.execute("DELETE FROM sessions WHERE token = ?", (token,))


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
