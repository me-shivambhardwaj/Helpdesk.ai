"""Read new support emails from Gmail (IMAP) and turn them into tickets."""
import email
import imaplib
import threading
import time
from email.header import decode_header, make_header
from email.utils import parseaddr

from .config import (ENABLE_INBOX_POLLING, INBOX_SUBJECT_FILTER, POLL_SECONDS,
                     SMTP_APP_PASSWORD, SMTP_USER)
from .pipeline import process_ticket

SKIP_SENDERS = ("no-reply", "noreply", "donotreply", "mailer-daemon", "postmaster")


def _body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            disp = str(part.get("Content-Disposition", ""))
            if part.get_content_type() == "text/plain" and "attachment" not in disp:
                return part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", errors="replace")
        return ""
    payload = msg.get_payload(decode=True)
    return payload.decode(msg.get_content_charset() or "utf-8", errors="replace") if payload else ""


def poll_once() -> int:
    """Check inbox once. Returns number of tickets created."""
    if not SMTP_USER or not SMTP_APP_PASSWORD:
        print("[inbox] Gmail not configured")
        return 0

    created = 0
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    try:
        imap.login(SMTP_USER, SMTP_APP_PASSWORD.replace(" ", ""))
        imap.select("INBOX")
        criteria = ["UNSEEN"]
        if INBOX_SUBJECT_FILTER:
            criteria += ["SUBJECT", f'"{INBOX_SUBJECT_FILTER}"']
        _, data = imap.search(None, *criteria)

        for num in data[0].split():
            _, parts = imap.fetch(num, "(BODY.PEEK[])")
            msg = email.message_from_bytes(parts[0][1])
            sender = parseaddr(msg.get("From", ""))[1]
            subject = str(make_header(decode_header(msg.get("Subject", "(no subject)"))))

            is_loop = (
                msg.get("X-Support-Agent")
                or subject.lower().startswith("re:")
                or any(s in sender.lower() for s in SKIP_SENDERS)
            )
            if not is_loop:
                body = _body(msg).strip()[:3000]
                if body:
                    process_ticket(sender, subject, body)
                    created += 1
            imap.store(num, "+FLAGS", "\\Seen")  # mark done so it is never processed twice
    finally:
        try:
            imap.logout()
        except Exception:
            pass
    return created


def start_background_polling():
    if not ENABLE_INBOX_POLLING:
        return

    def loop():
        while True:
            try:
                n = poll_once()
                if n:
                    print(f"[inbox] created {n} ticket(s)")
            except Exception as e:
                print("[inbox] error:", e)
            time.sleep(POLL_SECONDS)

    threading.Thread(target=loop, daemon=True).start()
    print(f"[inbox] polling every {POLL_SECONDS}s")
