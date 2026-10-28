import os
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
AUTO_RESOLVE_CONFIDENCE = float(os.getenv("AUTO_RESOLVE_CONFIDENCE", "0.85"))
MAX_RETRIEVAL_DISTANCE = float(os.getenv("MAX_RETRIEVAL_DISTANCE", "0.65"))
DB_PATH = "tickets.db"
CHROMA_DIR = "chroma_db"
KB_DIR = "data/kb"

CATEGORIES = ["billing", "refund", "bug", "how_to", "shipping",
              "account_access", "feature_request", "complaint", "other"]
# Only these categories may ever be auto-resolved. Money/legal topics always go to a human.
AUTO_RESOLVE_OK = {"how_to", "shipping", "account_access"}

# --- Email (Gmail) ---
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")
INBOX_SUBJECT_FILTER = os.getenv("INBOX_SUBJECT_FILTER", "SUPPORT")  # only mails with this word in the subject become tickets
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "60"))
ENABLE_INBOX_POLLING = os.getenv("ENABLE_INBOX_POLLING", "false").lower() == "true"
