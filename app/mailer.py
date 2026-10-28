"""Send replies through Gmail SMTP using an App Password."""
import smtplib
from email.message import EmailMessage
from .config import SMTP_USER, SMTP_APP_PASSWORD

FAKE_DOMAINS = ("example.com", "example.org", "example.net", "test.com")


def send_reply(to: str, subject: str, body: str) -> bool:
    if not SMTP_USER or not SMTP_APP_PASSWORD:
        print("[mailer] SMTP not configured, skipping send")
        return False
    if not to or "@" not in to or to.lower().endswith(FAKE_DOMAINS):
        print(f"[mailer] skipping fake/invalid address: {to}")
        return False

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    msg["X-Support-Agent"] = "1"  # lets the inbox poller ignore our own mail (prevents loops)
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SMTP_USER, SMTP_APP_PASSWORD.replace(" ", ""))
        s.send_message(msg)
    print(f"[mailer] sent reply to {to}")
    return True
