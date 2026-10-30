# Support Ticket Triage & Auto-Reply Agent

An AI-powered customer support triage and auto-response service powered by Groq, ChromaDB, and FastAPI.

---

## ⚡ Quick Start (Local)

### 1. Environment & Dependencies
```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Install requirements (already installed in venv)
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Ensure your `.env` file contains your Groq API key:
```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
AUTO_RESOLVE_CONFIDENCE=0.85
MAX_RETRIEVAL_DISTANCE=0.65
```

### 3. Run the API Server & Web UI
```powershell
uvicorn app.api:app --reload --port 8000
```
- **Web UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 4. Run the Streamlit Dashboard (Optional)
```powershell
streamlit run dashboard.py
```

---

## 🧪 Testing

### Automated API Test Suite
Tests all endpoints (`/`, `/metrics`, `/tickets`, `/tickets/{id}/approve`, `/inbox/poll`, error handling):
```powershell
python test_all_apis.py
```

### Evaluation Benchmark
Evaluates categorization and decision accuracy against labelled tickets:
```powershell
python eval/run_eval.py
```

---

## 📡 API Reference

| Method | Endpoint | Auth Required | Description |
|---|---|---|---|
| `GET` | `/` | No | Web UI with Login / Signup & Dashboard |
| `POST` | `/auth/signup` | No | Register new user with email & password |
| `POST` | `/auth/login` | No | Log in with email & password, receives token |
| `POST` | `/auth/logout` | No | Log out & invalidate active session |
| `GET` | `/auth/me` | Yes | Get currently authenticated user profile |
| `GET` | `/metrics` | Yes | Ticket statistics and response times |
| `POST` | `/tickets` | Yes | Submit new ticket for triage & auto-resolution |
| `GET` | `/tickets` | Yes | List tickets (supports `?status=...` filter) |
| `POST` | `/tickets/{id}/approve` | Yes | Approve a pending ticket and send email reply |
| `POST` | `/inbox/poll` | Yes | Manually poll Gmail inbox for new emails |

### Example: Submit a Ticket
```bash
curl -X POST "http://127.0.0.1:8000/tickets" \
     -H "Content-Type: application/json" \
     -d '{"customer": "user@example.com", "subject": "Forgot password", "body": "How do I reset my password?"}'
```

---

## 🚀 Deployment

### Option 1: Docker / Docker Compose
Run with persistent SQLite and vector database storage:
```bash
docker compose up --build -d
```

### Option 2: Cloud Deployment (Render / Railway / Fly.io)
1. Push this repository to GitHub.
2. In Render / Railway:
   - Create a new **Web Service**.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.api:app --host 0.0.0.0 --port $PORT`
   - Set Environment Variables: `GROQ_API_KEY`, `GROQ_MODEL`, etc.
   - Attach a persistent disk for `/app/tickets.db` and `/app/chroma_db` if you want ticket history to persist across redeployments.

### Option 3: VPS (Ubuntu / Linux)
1. Clone repo onto server.
2. Setup systemd service or run via `docker compose up -d`.
3. Configure Nginx reverse proxy with SSL (Let's Encrypt / Certbot).
