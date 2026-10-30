import json
import pandas as pd
import streamlit as st
from app import db, kb
from app.pipeline import process_ticket

st.set_page_config(page_title="Support Triage Agent", layout="wide")
st.title("Support Ticket Triage Agent")

if "kb_ready" not in st.session_state:
    st.session_state.kb_ready = kb.ingest()

tab_metrics, tab_queue, tab_new = st.tabs(["Metrics", "Review queue", "Submit test ticket"])

with tab_metrics:
    m = db.metrics()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total tickets", m["total"])
    c2.metric("Auto-resolved", f'{m["auto_resolved_pct"]}%')
    c3.metric("Avg response time (s)", m["avg_response_seconds"] or "-")
    if m["by_category"]:
        st.subheader("Tickets by category")
        st.bar_chart(pd.Series(m["by_category"]))
    if m["by_status"]:
        st.subheader("Tickets by status")
        st.bar_chart(pd.Series(m["by_status"]))

with tab_queue:
    pending = db.list_tickets("needs_approval") + db.list_tickets("escalated")
    if not pending:
        st.info("Nothing waiting for review.")
    for t in pending:
        label = f'#{t["id"]} [{t["status"]}] {t["subject"]} ({t["category"]}, {t["urgency"]}, {t["sentiment"]})'
        with st.expander(label):
            st.write("**Customer:**", t["customer"])
            st.write("**Message:**", t["body"])
            st.write("**Summary:**", t["summary"])
            st.write("**Sources:**", ", ".join(json.loads(t["sources"] or "[]")) or "none")
            reply = st.text_area("Reply", t["draft"], key=f'reply{t["id"]}', height=160)
            if st.button("Approve & send", key=f'ok{t["id"]}'):
                db.approve(t["id"], reply)
                st.rerun()

with tab_new:
    with st.form("new"):
        customer = st.text_input("Customer email", "test@example.com")
        subject = st.text_input("Subject")
        body = st.text_area("Message")
        if st.form_submit_button("Process ticket") and subject and body:
            with st.spinner("Triaging..."):
                r = process_ticket(customer, subject, body)
            st.success(f'Ticket #{r["id"]}: {r["status"]} ({r["category"]}, {r["urgency"]})')
            if r["draft"]:
                st.write("**Draft reply:**")
                st.write(r["draft"])
