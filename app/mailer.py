"""Send replies via Resend's HTTPS API if RESEND_API_KEY is set, else via SMTP."""
import json
import os
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr

from . import config  # loads .env

FAKE_DOMAINS = ("example.com", "example.org", "example.net", "test.com")


def _subject(s: str) -> str:
    return s if s.lower().startswith("re:") else f"Re: {s}"


def _send_resend(to, subject, body):
    key = os.getenv("RESEND_API_KEY", "")
    sender = os.getenv("RESEND_FROM", "onboarding@resend.dev")
    name = os.getenv("FROM_NAME", "HelpDesk AI")
    payload = {
        "from": f"{name} <{sender}>",
        "to": [to],
        "subject": _subject(subject),
        "text": body,
        "headers": {"X-Support-Agent": "1"},
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "helpdesk-ai/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Resend error {e.code}: {e.read().decode()[:300]}")
    return True


def _send_smtp(to, subject, body):
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_APP_PASSWORD", "").replace(" ", "")
    if not user or not password:
        print("[mailer] no email provider configured, skipping send")
        return False
    msg = EmailMessage()
    msg["From"] = formataddr((os.getenv("FROM_NAME", "HelpDesk AI"), user))
    msg["To"] = to
    msg["Subject"] = _subject(subject)
    msg["X-Support-Agent"] = "1"
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, password)
        s.send_message(msg)
    return True


def send_reply(to: str, subject: str, body: str) -> bool:
    if not to or "@" not in to or to.lower().endswith(FAKE_DOMAINS):
        print(f"[mailer] skipping fake/invalid address: {to}")
        return False
    if os.getenv("RESEND_API_KEY"):
        ok = _send_resend(to, subject, body)
    else:
        ok = _send_smtp(to, subject, body)
    if ok:
        print(f"[mailer] sent reply to {to}")
    return ok