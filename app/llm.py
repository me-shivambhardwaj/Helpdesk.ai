import json
import re
import time
from groq import Groq, RateLimitError
from .config import MODEL

_client = None


def client():
    global _client
    if _client is None:
        _client = Groq()  # reads GROQ_API_KEY from env
    return _client


def ask_json(system: str, user: str, max_tokens: int = 1500, retries: int = 4) -> dict:
    for attempt in range(retries):
        try:
            resp = client().chat.completions.create(
                model=MODEL,
                max_tokens=max_tokens,
                temperature=0.2,
                response_format={"type": "json_object"},  # forces valid JSON
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            text = resp.choices[0].message.content
            match = re.search(r"\{.*\}", text, re.S)
            if not match:
                raise ValueError(f"No JSON in model output: {text[:200]}")
            return json.loads(match.group(0))
        except RateLimitError:
            # Free tier has per-minute limits; wait and retry
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Groq rate limit hit repeatedly. Wait a minute and try again.")
