# ReviveAI — Autonomous Revenue Recovery Agent

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/)
[![Architecture](<https://img.shields.io/badge/Architecture-LangGraph%20%2B%20MCP%20Guard-indigo.svg>)](https://github.com/)

ReviveAI is a multi-agent autonomous revenue recovery platform built on a **LangGraph state machine** and **CrewAI agent roles**, gated by a **deterministic (non-LLM) Model Context Protocol (MCP) Compliance Server**.

The system autonomously detects revenue leakage events (failed payments, subscription dunning, checkout abandonments, overdue B2B invoices), diagnoses root causes, selects bounded recovery interventions informed by ChromaDB RAG, passes strict compliance gates, executes tool calls, verifies outcomes, and writes immutable audit logs.

---

## Key Features

- **🛡️ Deterministic MCP Compliance Guard:** 100% of agent actions are evaluated against plain-code rules (Max 3 retries, 30m retry cooldown, 24h contact cooldown, DND opt-out registry) before tool calling. Zero out-of-policy actions executed.
- **⚡ Bounded Action Space:** Agents operate strictly within an enumerable action catalog (`RETRY_PAYMENT`, `SEND_RECOVERY_MESSAGE`, `SEND_PAYMENT_METHOD_UPDATE_REQUEST`, `GENERATE_CHECKOUT_RECOVERY_LINK`, `SEND_INVOICE_REMINDER`, `ESCALATE_TO_HUMAN`, `CLOSE_NO_ACTION`).
- **🧠 Hybrid RAG Grounding:** ChromaDB vector store (`all-MiniLM-L6-v2`) providing similarity search over historical resolved cases and static policy KB chunks.
- **🔀 Multi-Model LLM Routing:** Low-latency event classification via Groq (Llama-3.3-70b) → Gemini Pro reasoning → OpenAI fallback chain.
- **📊 Real-Time Glassmorphic Dashboard:** Interactive KPI cards (₹ At Risk, ₹ Recovered, Recovery Rate %), filterable case streams, step-by-step audit drawers, and dedicated MCP compliance panel.

---

## Directory Structure

```
reviveai/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── config.py              # Environment configuration
│   │   ├── db/mongo.py            # Motor async MongoDB driver & in-memory fallback
│   │   ├── models/schemas.py      # Pydantic domain models
│   │   ├── mcp/compliance_server.py # MCP Compliance Guard Server
│   │   ├── rag/ (embeddings, retriever)
│   │   ├── llm/ (router, groq_adapter, gemini_adapter)
│   │   ├── agents/ (detector, diagnosis, strategy, execution, audit)
│   │   ├── graph/workflow.py      # LangGraph state machine definition
│   │   ├── tools/ (mock_razorpay, mock_messaging, mock_escalation)
│   │   └── routers/ (events, cases, batch, compliance)
│   ├── tests/                     # Pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/            # SummaryCards, CaseTable, TimelineDrawer, CompliancePanel
│   │   ├── pages/Dashboard.jsx    # Primary glassmorphic dashboard view
│   │   ├── api/client.js          # REST API client
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── synthetic_transactions.csv  # 50+ realistic synthetic events
│   ├── seed_resolved_cases.json    # RAG cold-start seed
│   └── policy_kb.json              # RAG policy chunks
├── scripts/
│   ├── seed_mongo.py
│   ├── seed_chroma.py
│   └── rebuild_embeddings.py
├── docker-compose.yml
└── README.md
```

---

## Quickstart & Running Locally

### Option 1: Using Docker Compose

```bash
# Set optional LLM keys in your environment or .env file
export GROQ_API_KEY="your_groq_key"
export GEMINI_API_KEY="your_gemini_key"

# Start MongoDB, FastAPI backend, and React frontend
docker-compose up --build
```

Access the Dashboard at `http://localhost:3000` and API docs at `http://localhost:8000/docs`.

### Option 2: Running Backend & Frontend Directly

1. **Install Backend Dependencies:**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. **Start Backend Server:**

   ```bash
   python -m backend.app.main
   ```
3. **Start React Frontend:**

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## Demo Script & Judging Checklist

1. **Journey 1 — Clean Autonomous Recovery:** Ingest `TXN_1001` (₹4,999 subscription failure). Bank decline diagnosed → 87% recovery probability → Retry attempt 1/3 allowed by MCP Guard → Razorpay retry success → ₹4,999 recovered → Case closed.
2. **Journey 2 — B2B Promise-to-Pay & Escalation:** Ingest `TXN_1002` (₹25,000 overdue B2B invoice). Invoice reminder issued → auto-escalated to human account manager.
3. **Journey 3 — MCP Stopping Rule Block:** Ingest `TXN_1003` (repeated failure). On 3rd retry attempt, MCP Compliance Guard halts execution (`MAX_RETRY_ATTEMPTS` reached), preventing infinite retry loops and auto-escalating with full audit justification.
