from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import auth, db, inbox, kb
from .auth import (
    AuthPayload,
    get_current_user,
    hash_password,
    validate_email,
    validate_password,
    verify_password,
)
from .mailer import send_reply
from .pipeline import process_ticket

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    kb.ingest()                      # load knowledge base once at startup
    inbox.start_background_polling()  # only runs if ENABLE_INBOX_POLLING=true
    yield


app = FastAPI(title="Support Triage Agent", lifespan=lifespan)


class TicketIn(BaseModel):
    customer: str | None = None
    subject: str
    body: str


class ApproveIn(BaseModel):
    final_reply: str


# --- Public / Static Routes ---

@app.get("/", include_in_schema=False)
@app.get("/login", include_in_schema=False)
@app.get("/signup", include_in_schema=False)
@app.get("/register", include_in_schema=False)
def serve_ui():
    return FileResponse(
        STATIC / "index.html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


# --- Authentication Routes ---

@app.post("/auth/signup")
def signup(payload: AuthPayload, response: Response):
    email = validate_email(payload.email)
    password = validate_password(payload.password)

    if db.get_user_by_email(email):
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    password_hash = hash_password(password)
    user = db.create_user(email, password_hash)
    token = db.create_session(user["id"])

    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return {"ok": True, "token": token, "user": user}


@app.post("/auth/login")
def login(payload: AuthPayload, response: Response):
    email = validate_email(payload.email)
    password = validate_password(payload.password)

    user_row = db.get_user_by_email(email)
    if not user_row or not verify_password(password, user_row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = db.create_session(user_row["id"])
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 3600,
    )
    return {
        "ok": True,
        "token": token,
        "user": {"id": user_row["id"], "email": user_row["email"]},
    }


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    elif "session_token" in request.cookies:
        token = request.cookies["session_token"]
    elif "x-session-token" in request.headers:
        token = request.headers["x-session-token"]

    if token:
        db.delete_session(token)

    response.delete_cookie(key="session_token")
    return {"ok": True}


@app.get("/auth/me")
def me(current_user: dict = Depends(get_current_user)):
    return {"ok": True, "user": current_user}


# --- Protected Application Routes ---

@app.post("/tickets")
def create_ticket(t: TicketIn, current_user: dict = Depends(get_current_user)):
    customer_email = t.customer.strip() if t.customer and t.customer.strip() else current_user["email"]
    return process_ticket(customer_email, t.subject, t.body)


@app.get("/tickets")
def tickets(status: str | None = None, current_user: dict = Depends(get_current_user)):
    return db.list_tickets(status)


@app.post("/tickets/{ticket_id}/approve")
def approve(ticket_id: int, a: ApproveIn, current_user: dict = Depends(get_current_user)):
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
def poll_now(current_user: dict = Depends(get_current_user)):
    """Check the Gmail inbox immediately instead of waiting for the timer."""
    return {"tickets_created": inbox.poll_once()}


@app.get("/metrics")
def metrics(current_user: dict = Depends(get_current_user)):
    return db.metrics()
