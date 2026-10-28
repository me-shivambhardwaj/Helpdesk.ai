"""Measure triage accuracy and auto-resolve behaviour on a labelled set."""
import sys
import pandas as pd

sys.path.insert(0, ".")
from app import kb
from app.pipeline import decide
from app.reply import draft_reply
from app.triage import triage_ticket

kb.ingest()
df = pd.read_csv("data/sample_tickets.csv")
rows = []
import time
for _, r in df.iterrows():
    time.sleep(2)
    tri = triage_ticket(r["subject"], r["body"])
    draft = draft_reply(r["subject"], r["body"], kb.retrieve(f'{r["subject"]}\n{r["body"]}'))
    rows.append({
        "subject": r["subject"],
        "expected": r["expected_category"], "got": tri["category"],
        "expected_decision": r["expected_decision"], "decision": decide(tri, draft),
    })

out = pd.DataFrame(rows)
print(out.to_string(index=False))
print(f'\nCategory accuracy: {(out.expected == out.got).mean():.0%}')
print(f'Decision accuracy: {(out.expected_decision == out.decision).mean():.0%}')
out.to_csv("eval/results.csv", index=False)
