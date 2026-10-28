from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
import traceback
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import db, inbox, kb
from .mailer import send_reply
from .pipeline import process_ticket

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    kb.ingest()                      # load knowledge base once at startup
    inbox.start_background_polling()  # only runs if ENABLE_INBOX_POLLING=true
    yield


app = FastAPI(title="HelpDesk AI", lifespan=lifespan)


class TicketIn(BaseModel):
    customer: str
    subject: str
    body: str


class ApproveIn(BaseModel):
    final_reply: str


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.post("/tickets")
def create_ticket(t: TicketIn):
    try:
        return process_ticket(t.customer, t.subject, t.body)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"{type(e).__name__}: {e}")


@app.get("/tickets")
def tickets(status: str | None = None):
    return db.list_tickets(status)


@app.post("/tickets/{ticket_id}/approve")
def approve(ticket_id: int, a: ApproveIn):
    t = db.get(ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    db.approve(ticket_id, a.final_reply)
    emailed = False
    try:
        emailed = send_reply(t["customer"], t["subject"], a.final_reply)
    except Exception as e:
        print("[mailer] error:", e)
    return {"ok": True, "emailed": emailed}


@app.post("/inbox/poll")
def poll_now():
    """Check the Gmail inbox immediately instead of waiting for the timer."""
    return {"tickets_created": inbox.poll_once()}


@app.get("/metrics")
def metrics():
    return db.metrics()
