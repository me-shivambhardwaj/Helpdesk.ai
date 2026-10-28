<<<<<<< HEAD
# HelpDesk AI & Auto-Reply Agent

## Setup
    python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    cp .env.example .env        # then paste your GROQ_API_KEY

## Run
    python -m uvicorn app.api:app --reload     # UI at http://127.0.0.1:8000  API docs at /docs
    python eval/run_eval.py                    # accuracy on labelled tickets

## Flow
ticket -> triage (category/urgency/sentiment) -> retrieve KB chunks -> draft reply
-> decide: auto_resolved | needs_approval | escalated -> log to SQLite -> web UI
=======
HelpDesk AI is an AI-powered customer support agent. It reads incoming tickets
and emails, classifies them by category, urgency and sentiment, searches a
knowledge base for the right answer, and drafts a reply. Low-risk questions are
resolved automatically, while refunds, angry customers and urgent issues go to
a human for approval.

## Features
- Ticket triage: category, urgency and sentiment detection
- RAG over help documents using ChromaDB, so replies come from real policies
- Safety-first routing: auto-resolve, needs approval, or escalate
- Prompt-injection defenses and retrieval checks to reduce wrong answers
- Review queue where agents edit and approve drafts
- Gmail integration for receiving tickets and sending replies
- Metrics dashboard: total tickets, auto-resolve rate, average response time

## Tech stack
Python, FastAPI, Groq (Llama), ChromaDB, SQLite, vanilla JS frontend, Docker
>>>>>>> 6e0d86915e4f54fa2aa45ca9ae4c7b2a99c5694e
>>>>>>>
>>>>>>> ---
title: HelpDesk AI
emoji: 🎧
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---
