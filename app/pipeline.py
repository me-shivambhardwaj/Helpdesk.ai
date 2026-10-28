import json
import time
from . import db, kb
from .mailer import send_reply
from .config import AUTO_RESOLVE_CONFIDENCE, AUTO_RESOLVE_OK
from .reply import draft_reply
from .triage import triage_ticket


def decide(tri: dict, draft: dict) -> str:
    """Returns: escalated | auto_resolved | needs_approval"""
    if tri.get("needs_human") or tri["urgency"] == "high" or tri["sentiment"] == "angry":
        return "escalated"
    if (draft.get("answerable")
            and draft.get("confidence", 0) >= AUTO_RESOLVE_CONFIDENCE
            and tri["category"] in AUTO_RESOLVE_OK):
        return "auto_resolved"
    return "needs_approval"


def process_ticket(customer: str, subject: str, body: str) -> dict:
    created = time.time()
    tri = triage_ticket(subject, body)
    chunks = kb.retrieve(f"{subject}\n{body}")
    draft = draft_reply(subject, body, chunks)
    status = decide(tri, draft)
    auto = status == "auto_resolved"

    record = {
        "created_at": created,
        "responded_at": time.time() if auto else None,
        "customer": customer, "subject": subject, "body": body,
        "category": tri["category"], "urgency": tri["urgency"],
        "sentiment": tri["sentiment"], "summary": tri.get("summary", ""),
        "draft": draft.get("reply", ""), "confidence": draft.get("confidence", 0.0),
        "sources": json.dumps(draft.get("sources", [])),
        "status": status, "final_reply": draft.get("reply") if auto else None,
    }
    record["id"] = db.insert(record)
    if auto:
        try:
            send_reply(customer, subject, record["final_reply"])
        except Exception as e:  # never fail a ticket because email failed
            print("[mailer] error:", e)
    return record
