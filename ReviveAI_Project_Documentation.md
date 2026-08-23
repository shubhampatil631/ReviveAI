# ReviveAI — Autonomous Revenue Recovery Agent

## Complete Project Documentation (Pre-Build Specification)

**Version:** 1.0
**Document Type:** Technical Design & Build Specification
**Prepared for:** Hackathon / Buildathon Delivery
**Status:** Pre-Development — Ready for Sprint Planning

---

## Table of Contents

1. Executive Summary
2. Project Objectives & Success Criteria
3. System Architecture Overview
4. Module Breakdown (with Submodules)
   - 4.1 Ingestion Module
   - 4.2 Detection Module
   - 4.3 Diagnosis Module
   - 4.4 Strategy / Decision Module
   - 4.5 Compliance & Guardrail Module (MCP)
   - 4.6 Execution Module
   - 4.7 Audit & Logging Module
   - 4.8 Promise-to-Pay Module
   - 4.9 RAG / Knowledge Module
   - 4.10 Dashboard & Reporting Module
   - 4.11 Backend API Module
   - 4.12 LLM Routing Module
5. Data Architecture & Schemas
   5A. Storage & Infrastructure Architecture (Deep Dive)
6. API Specification
7. Workflow & State Machine Design
8. Technology Stack
9. Non-Functional Requirements
10. Security, Privacy & Compliance
11. Folder / Repository Structure
12. Environment Configuration
13. Testing Strategy
14. Deployment Plan
15. Demo Script & Evaluation Mapping
16. Build Timeline (Sprint Plan)
17. Risk Register
18. Appendix — Glossary

---

## 1. Executive Summary

ReviveAI is a multi-agent, tool-calling system that autonomously detects revenue leakage events (failed payments, checkout abandonment, subscription dunning, overdue B2B invoices), diagnoses the root cause, selects a **bounded** recovery action, executes it, verifies the outcome, and stops — all while writing an immutable audit trail. It is built on a LangGraph state machine with CrewAI-defined agent roles, guarded by a deterministic (non-LLM) compliance layer exposed as an MCP server.

The system is designed to answer one judging question directly: **"How much money did the agent actually recover, and can you prove every action it took was compliant?"**

This document specifies every module, submodule, data contract, and API needed to build the system without re-deriving architecture decisions mid-build.

---

## 2. Project Objectives & Success Criteria

### 2.1 Primary Objectives

| #  | Objective                                                     | Measurable Target                                              |
| -- | ------------------------------------------------------------- | -------------------------------------------------------------- |
| O1 | Detect at-risk revenue events from a transaction/event stream | 100% of ingested events classified within 2s                   |
| O2 | Diagnose root cause with explainable reasoning                | ≥85% cause classification accuracy on test set                |
| O3 | Select and execute a bounded recovery action                  | 0 out-of-policy actions executed                               |
| O4 | Enforce stopping rules / compliance                           | 100% of actions pass through Compliance Guard before execution |
| O5 | Produce measurable recovered revenue                          | Dashboard shows ₹ recovered, recovery rate %, live            |
| O6 | Full auditability                                             | Every case has a complete, timestamped action trail            |

### 2.2 Out of Scope (explicitly, to prevent scope creep)

- Real payment processing (sandbox/mock Razorpay only)
- Real SMS/WhatsApp delivery (stubbed provider interface)
- Multi-tenant auth/RBAC (single demo tenant only)
- Production-grade horizontal scaling

### 2.3 Definition of Done

A batch of 50–100 synthetic transactions can be ingested, processed end-to-end through all six agents, and the dashboard displays accurate recovered-revenue metrics with a drillable, exportable audit log — including at least one case where a stopping rule visibly blocks an action.

---

## 3. System Architecture Overview

### 3.1 High-Level Diagram (textual)

```
                    ┌────────────────────────┐
                    │   Event Sources         │
                    │ (webhook / CSV / mock)  │
                    └───────────┬─────────────┘
                                ▼
                    ┌────────────────────────┐
                    │  Ingestion Module        │
                    └───────────┬─────────────┘
                                ▼
        ┌───────────────────────────────────────────┐
        │        LangGraph State Machine              │
        │                                             │
        │  Detector → Diagnosis → Strategy →           │
        │  Compliance Guard → Execution →              │
        │  Outcome Verify → Audit → Close/Loop/Escalate│
        └───────────────────┬───────────────────────┘
                             ▼
              ┌───────────────────────────┐
              │   MongoDB (system of record)│
              └───────────────┬─────────────┘
                               ▼
              ┌───────────────────────────┐
              │  FastAPI Backend (REST)     │
              └───────────────┬─────────────┘
                               ▼
              ┌───────────────────────────┐
              │  React Dashboard (frontend) │
              └───────────────────────────┘
```

### 3.2 Architectural Principles

1. **Deterministic guardrails, probabilistic reasoning** — compliance/stopping logic is plain code (MCP server), never delegated to an LLM.
2. **Bounded action space** — agents choose from a fixed enum of tools; no free-text/open-ended agent actions.
3. **Everything is auditable** — every state transition writes to `AuditLog` before proceeding.
4. **Idempotent execution** — every executed action is tied to a `case_id` + `attempt_number` to prevent duplicate retries.
5. **LLM routing by task shape** — fast/cheap model for classification, stronger model for nuanced reasoning and message generation.

---

## 4. Module Breakdown (with Submodules)

### 4.1 Ingestion Module

**Purpose:** Normalize incoming raw events from any source (Razorpay webhooks, Stripe webhooks, Batch CSV uploads, subscription engines, checkout systems, B2B invoices) into a single canonical `Event` schema.

**Submodules:**

- **4.1.1 Webhook Receiver (`backend/app/ingestion/webhook_receiver.py`)** — Accepts Razorpay (`payment.failed`, `order.paid`, `subscription.halted`) and Stripe (`payment_intent.payment_failed`, `charge.failed`, `invoice.payment_failed`) webhook payloads with HMAC signature verification helper support.
- **4.1.2 Batch CSV Loader (`backend/app/routers/events.py`)** — Accepts CSV of synthetic/production transactions (`transaction_id`, `customer_id`, `event_type`, `amount`, `currency`, `failure_reason`), validates schemas, and processes batch events in synchronous or queued mode.
- **4.1.3 Event Normalizer (`backend/app/ingestion/normalizer.py`)** — Pure normalization layer converting heterogenous provider payloads into the canonical `Event` schema (§5.1), handling currency unit conversions (paise/cents to INR/USD) and failure reason taxonomy mapping.
- **4.1.4 Event Queue (`backend/app/ingestion/queue.py`)** — In-memory thread-safe `asyncio.Queue` with background worker management, async processing via `run_recovery_workflow`, and live queue health metrics.

**Exposed Interfaces:**

- `POST /events/ingest` (Ingest generic/custom raw payload with optional `async_mode=true` query param)
- `POST /events/webhook/razorpay` (Dedicated Razorpay webhook receiver)
- `POST /events/webhook/stripe` (Dedicated Stripe webhook receiver)
- `POST /events/batch-upload` (CSV synthetic transaction batch uploader)
- `GET /events/queue/status` (Event Queue metrics: queue size, processed count, failed count, worker health)

---

### 4.2 Detection Module (Detector Agent)

**Purpose:** Classify each normalized event by risk type and severity, calculate recovery probability, and instantiate the recovery case in MongoDB.

**Submodules:**

- **4.2.1 Event Classifier (`EventClassifier` in `backend/app/agents/detector.py`)** — Performs keyword rule pre-filtering + 3-tier hybrid LLM failover (`Groq` Llama-70b -> `Gemini Pro` -> `Ollama` small model) to categorize raw events strictly into: `payment_failure`, `checkout_abandonment`, `subscription_dunning`, `overdue_invoice`.
- **4.2.2 Risk Scorer (`RiskScorer` in `backend/app/agents/detector.py`)** — Evaluates transaction amount, customer history from MongoDB (`past_failures`, `past_recoveries`, `lifetime_value`, `opt_out`), payment method type (`card`, `upi`, `e_mandate`), and event type to calculate `risk_score` (0.05–0.95), `recovery_probability` (0.05–0.95), and risk label (`LOW`, `MEDIUM`, `HIGH`).
- **4.2.3 Case Creator (`CaseCreator` in `backend/app/agents/detector.py`)** — Generates formatted case IDs (`CASE_*`), retrieves customer metadata, inserts `RecoveryCase` document into MongoDB with status `detected`, and returns Section 4.2 JSON contract.

**Output contract:**

```json
{
  "case_id": "string",
  "customer_id": "string",
  "event_type": "payment_failure | checkout_abandonment | subscription_dunning | overdue_invoice",
  "amount": 2499,
  "risk": "LOW | MEDIUM | HIGH",
  "risk_score": 0.35,
  "recovery_probability": 0.87,
  "reasoning_summary": "string",
  "status": "detected"
}
```

---

### 4.3 Diagnosis Module (Root-Cause Agent)

**Purpose:** Determine *why* the revenue event happened, compute confidence, and summarize reasoning for audit logs.

**Submodules:**

- **4.3.1 Rule Engine (`DiagnosisRuleEngine` in `backend/app/agents/diagnosis.py`)** — Deterministic decline code and error status mapping (`BAD_REQUEST_ERROR`, `CARD_EXPIRED`, `GATEWAY_ERROR`, `MANDATE_EXPIRED`, etc.) to instantly determine root cause without latency or API costs.
- **4.3.2 LLM Reasoner (`LLMReasoner` in `backend/app/agents/diagnosis.py`)** — Invokes 3-tier hybrid LLM failover (`Gemini Pro` -> `Groq` Llama-70b -> `Ollama` small model) for ambiguous cases (e.g. missing decline code, unstructured error text, B2B net-terms contract nuances).
- **4.3.3 Cause Taxonomy (`CauseTaxonomy` in `backend/app/agents/diagnosis.py`)** — Strictly enforces 9 primary root cause categories: `insufficient_funds`, `expired_card`, `bank_decline`, `gateway_timeout`, `mandate_lapse`, `cart_abandoned_shipping`, `cart_abandoned_payment`, `invoice_terms_breach`, `customer_churned`.
- **4.3.4 Confidence Scorer (`ConfidenceScorer` in `backend/app/agents/diagnosis.py`)** — Calculates confidence score (0.50–0.99). Cases below threshold (< 0.80) are flagged with `requires_collaborative_reasoning = true` for joint resolution.

**Output contract:**

```json
{
  "case_id": "string",
  "root_cause": "bank_decline",
  "confidence": 0.91,
  "reasoning_summary": "string (LLM-generated, 1-2 sentences)",
  "requires_collaborative_reasoning": false,
  "status": "diagnosed"
}
```

---

### 4.4 Strategy / Decision Module (Strategy Agent)

**Purpose:** Select the lowest-cost effective intervention from a bounded action set, informed by RAG over historical outcomes and company policies.

**Submodules:**

- **4.4.1 Action Catalog (`ActionCatalog` in `backend/app/agents/strategy.py`)** — Fixed, immutable list of allowed recovery interventions. Enforces strict validation guaranteeing no un-whitelisted action can ever be selected.
- **4.4.2 Bounded Action Set & Decision Matrix (`DecisionMatrix` in `backend/app/agents/strategy.py`)** — Primary and fallback intervention mapping for all 9 root causes. Evaluates retry attempt limits (`attempts >= 3` shifts to fallback or escalation) and low recovery probability (`< 0.15` and `< ₹500` shifts to `CLOSE_NO_ACTION`).
- **4.4.3 RAG Retriever (`StrategyRAGRetriever` in `backend/app/agents/strategy.py`)** — Queries ChromaDB vector store (`resolved_cases` and `policy_kb`) for top-k historical outcomes and company policy rules matching `event_type + root_cause + amount_bucket`.
- **4.4.4 Decision Composer (`DecisionComposer` in `backend/app/agents/strategy.py`)** — Invokes 3-tier hybrid LLM failover (`Gemini Pro` -> `Groq` Llama-70b -> `Ollama` small model) to combine baseline rules and RAG context into a crisp, grounded decision rationale.

**Bounded Action Set:**

```
RETRY_PAYMENT
SEND_PAYMENT_METHOD_UPDATE_REQUEST
SEND_RECOVERY_MESSAGE
GENERATE_CHECKOUT_RECOVERY_LINK
SEND_INVOICE_REMINDER
ESCALATE_TO_HUMAN
CLOSE_NO_ACTION
```

**Decision Mapping Matrix:**

| Root Cause                     | Primary Action                     | Fallback Action       |
| ------------------------------ | ---------------------------------- | --------------------- |
| bank_decline / gateway_timeout | RETRY_PAYMENT                      | SEND_RECOVERY_MESSAGE |
| expired_card                   | SEND_PAYMENT_METHOD_UPDATE_REQUEST | ESCALATE_TO_HUMAN     |
| insufficient_funds             | RETRY_PAYMENT                      | SEND_RECOVERY_MESSAGE |
| cart_abandoned_*               | GENERATE_CHECKOUT_RECOVERY_LINK    | CLOSE_NO_ACTION       |
| invoice_terms_breach           | SEND_INVOICE_REMINDER              | ESCALATE_TO_HUMAN     |
| mandate_lapse                  | SEND_PAYMENT_METHOD_UPDATE_REQUEST | ESCALATE_TO_HUMAN     |
| customer_churned               | CLOSE_NO_ACTION                    | ESCALATE_TO_HUMAN     |

---

### 4.5 Compliance & Guardrail Module (MCP Server) — **Critical Module**

**Purpose:** Deterministically gate every action before execution. Never LLM-decided. Hard non-LLM policy guardrails ensuring zero out-of-policy agent actions.

**Submodules:**

- **4.5.1 Retry Limiter (`check_retry_allowed`)** — Max N retries per case (config default: 3), enforced against `RecoveryCase.attempts`.
- **4.5.2 Cooldown Enforcer (`check_retry_allowed` / `check_contact_allowed`)** — Enforces minimum time gaps (30m retry cooldown, 24h message cooldown).
- **4.5.3 Opt-Out / DND Registry (`check_contact_allowed`)** — Checks customer `opt_out` flag in MongoDB before any `SEND_*` action; hard-blocks with `BLOCK` if set.
- **4.5.4 Escalation Tier Manager (`check_escalation_tier`)** — Caps escalation at defined tiers (Tier 1 Auto -> Tier 2 Team Lead -> Tier 3 Manager); prevents infinite escalation loops.
- **4.5.5 Blackout Window Checker (`check_contact_allowed`)** — Blocks customer communications during compliance blackout hours (22:00–08:00 local time).
- **4.5.6 Decision Logger (`log_compliance_decision`)** — Logs every ALLOW / BLOCK / ESCALATE decision in MongoDB `compliance_decisions` with the exact rule fired.

**Exposed MCP Tool Endpoints (`backend/app/routers/compliance.py`):**

- `POST /compliance/check-retry` $\rightarrow$ `check_retry_allowed(case_id)` $\rightarrow$ `{ allowed: bool, decision: string, reason: string }`
- `POST /compliance/check-contact` $\rightarrow$ `check_contact_allowed(customer_id, case_id)` $\rightarrow$ `{ allowed: bool, decision: string, reason: string }`
- `GET /compliance/escalation-tier/{case_id}` $\rightarrow$ `check_escalation_tier(case_id)` $\rightarrow$ `{ current_tier: int, max_tier: int, can_escalate: bool }`
- `POST /compliance/evaluate` $\rightarrow$ `evaluate_action(case_id, customer_id, action)` $\rightarrow$ `{ allowed: bool, decision: string, rule_fired: string, reason: string }`
- `GET /compliance/logs` $\rightarrow$ Returns compliance decision audit trail (filterable by ALLOW / BLOCK / ESCALATE).

**Frontend Integration (`frontend/src/components/CompliancePanel.jsx` & `client.js`):**

- Features an interactive **"MCP Server Live Tool Evaluator"** simulator allowing live testing of hard policy gates with real-time rule evaluation and visual decision badges.

---

### 4.6 Execution Module (Execution Agent)

**Purpose:** Carry out approved actions via tool calling against sandbox/mock provider APIs, personalize customer communications in English and Hinglish, and enforce idempotency locks.

**Submodules:**

- **4.6.1 Payment Retry Tool (`mock_retry_payment` in `backend/app/tools/mock_razorpay.py`)** — Calls mock Razorpay retry endpoint; returns success/failed + decline reason if failed.
- **4.6.2 Messaging Tool (`mock_send_message` in `backend/app/tools/mock_messaging.py`)** — Generates and delivers stubbed Email / SMS / WhatsApp messages using personalized LLM copy (`Gemini Pro` -> `Groq` -> `Ollama`) with natural Indian Hinglish support.
- **4.6.3 Link Generator Tool (`mock_generate_checkout_link` in `backend/app/tools/mock_link.py`)** — Creates a mock personalized checkout-recovery URL with incentive token.
- **4.6.4 Invoice Reminder Tool (`mock_send_invoice_reminder` in `backend/app/tools/mock_invoice.py`)** — Generates B2B overdue invoice notice document & payment commitment link.
- **4.6.5 Escalation Tool (`mock_escalate_human` in `backend/app/tools/mock_escalation.py`)** — Creates human-assigned support task/ticket (mock Zendesk/Jira).
- **4.6.6 Idempotency Guard (`IdempotencyGuard` in `backend/app/agents/execution.py`)** — Checks MongoDB audit logs to ensure the exact same action isn't executed twice for the same `case_id` + `attempt_number`.

**Output contract:**

```json
{
  "case_id": "string",
  "action": "RETRY_PAYMENT",
  "result": "success | failed | pending",
  "amount_recovered": 4999,
  "recovered_amount": 4999,
  "provider_response": { "...": "..." },
  "attempts": 1,
  "final_status": "recovered"
}
```

**Backend & Frontend Mapping:**

- Backend Endpoint: `POST /cases/{case_id}/actions` routes manual action triggers through `mcp_compliance_server` and `execution_agent`.
- Frontend Mapping: `CaseTable.jsx` includes an interactive **"⚡ Retry Action"** button per row; `TimelineDrawer.jsx` renders delivered copy, recovery links, and ticket IDs.

---

---

### 4.7 Audit & Logging Module (Audit Agent)

**Purpose:** Immutable, structured, exportable record of every decision, state transition, and tool call across the multi-agent orchestration pipeline.

**Submodules:**

- **4.7.1 Audit Writer (`AuditWriter` in `backend/app/agents/audit.py`)** — Writes structured immutable records to MongoDB `audit_logs` collection on every state transition (`detect`, `diagnose`, `decide`, `guard`, `execute`, `outcome`). Indexes resolved case summaries into ChromaDB vector store for RAG grounding.
- **4.7.2 Export Service (`ExportService` in `backend/app/agents/audit.py`)** — Generates downloadable CSV exports for individual case audit histories and full batch report summaries.
- **4.7.3 Case Timeline Builder (`CaseTimelineBuilder` in `backend/app/agents/audit.py`)** — Assembles a human-readable, chronologically ordered timeline view per case enriched with agent system prompts, model metadata, rule justifications, and tool invocation provider responses.

**Backend REST Endpoints (`backend/app/routers/cases.py`):**

- `GET /cases/{case_id}/timeline` $\rightarrow$ Returns case detail and enriched timeline.
- `GET /cases/{case_id}/export/csv` $\rightarrow$ Downloads `reviveai_audit_{case_id}.csv`.
- `GET /cases/export/batch/csv?status=all` $\rightarrow$ Downloads `reviveai_batch_report_{status}.csv`.

**Frontend Integration (`TimelineDrawer.jsx` & `Dashboard.jsx`):**

- `TimelineDrawer.jsx` features an **"📥 Export Case CSV"** button in the case header.
- `Dashboard.jsx` top action bar features an **"📥 Export Batch Report CSV"** button.

---

### 4.8 Promise-to-Pay Module

**Purpose:** Track verbal/written payment commitments from B2B customers separate from the main case state machine.

**Submodules:**

- **4.8.1 Promise State Machine (`backend/app/routers/promises.py`)** — Full lifecycle: `promised -> due_date -> paid | broken`. Manages promise commitments separate from case states, updating case status to `promised_to_pay` on creation and `recovered` on payment completion.
- **4.8.2 Deadline Watcher (`deadline_watcher` in `backend/app/routers/promises.py`)** — Scheduled scanner checking all active commitments where `due_date < current_time` and marking overdue commitments as `broken`.
- **4.8.3 Re-Queue Handler (`backend/app/routers/promises.py`)** — Broken promises automatically re-enter the LangGraph Detector pipeline (`run_recovery_workflow`) as high-priority `broken_promise_to_pay` events.

**Backend REST Endpoints (`backend/app/routers/promises.py`):**

- `POST /promises/create` $\rightarrow$ Registers a payment commitment (`case_id`, `promised_amount`, `days_due`).
- `GET /promises?status=all` $\rightarrow$ Lists commitments filterable by status (`promised`, `paid`, `broken`).
- `POST /promises/{promise_id}/mark-paid` $\rightarrow$ State transition `promised` $\rightarrow$ `paid`, updates case to `recovered`.
- `POST /promises/{promise_id}/mark-broken` $\rightarrow$ State transition `promised` $\rightarrow$ `broken`, invokes Re-Queue Handler into Detector agent.
- `POST /promises/check-deadlines` $\rightarrow$ Scans all commitments, transitions overdue to `broken`, and re-queues into Detector pipeline.

**Frontend Integration (`PromiseManager.jsx` & `client.js`):**

- Interactive **"➕ Register New Promise-to-Pay"** form allowing custom commitment entry.
- State filter tabs (`ALL`, `PROMISED`, `PAID`, `BROKEN`) and row action buttons (**"✅ Mark Paid"** / **"❌ Mark Broken"**).
- **"⏰ Run Deadline Watcher Scan"** button triggering automated scan and re-queue pipeline.

---

### 4.9 RAG / Knowledge Module

**Purpose:** Provide historical case outcomes and policy contextual grounding to the Strategy Agent.

**Submodules:**

- **4.9.1 Embedding Pipeline (`RAGVectorStore` in `backend/app/rag/embeddings.py`)** — Hugging Face `all-MiniLM-L6-v2` sentence-transformers encode resolved case summaries into 384-dim dense vectors.
- **4.9.2 Vector Store (`RAGVectorStore` in `backend/app/rag/embeddings.py`)** — ChromaDB PersistentClient collection: `resolved_cases` (with in-memory word match fallback).
- **4.9.3 Policy Knowledge Base (`RAGVectorStore` in `backend/app/rag/embeddings.py`)** — Separate collection `policy_kb` storing retry rules, communication rules, DND guidelines, and escalation caps as retrievable text chunks.
- **4.9.4 Retriever Interface (`retrieve_similar_cases` & `retrieve_relevant_policies` in `backend/app/rag/retriever.py` & `backend/app/routers/rag.py`)** — Top-k similarity search callable by Strategy Agent and exposed via REST API (`GET /rag/query`).
- **4.9.5 Seed Loader (`scripts/seed_chroma.py`)** — Populates `resolved_cases` and `policy_kb` from `data/seed_resolved_cases.json` and `data/policy_kb.json` on first boot, solving the cold-start problem.

---

### 4.10 Dashboard & Reporting Module (React Frontend)

**Purpose:** Demonstrate measurable business impact and full agent orchestration transparency.

**Submodules:**

- **4.10.1 Summary Cards (`SummaryCards.jsx`)** — 5 high-impact metric cards displaying:
  1. Total Revenue at Risk (₹)
  2. Autonomously Recovered (₹)
  3. Recovery Rate %
  4. Total Cases Processed
  5. MCP Compliance Blocked count
- **4.10.2 Case Table / Filter View (`CaseTable.jsx`)** — Real-time filterable case view with search bar, event type filters, status filters (`recovered`, `blocked`, `escalated`, `detected`), and interactive **"⚡ Retry Action"** trigger buttons.
- **4.10.3 Case Detail Drawer (`TimelineDrawer.jsx`)** — Full audit timeline drawer per case (`detect` -> `diagnose` -> `decide` -> `guard` -> `execute` -> `outcome`) rendering delivered Hinglish/English copy, personalized checkout recovery links, escalation ticket IDs, and tool execution tags.
- **4.10.4 Intervention Breakdown Chart (`InterventionChart.jsx`)** — Visual progress bars showing executed action distribution, case resolution status distribution, and benchmarked success rate % per bounded action type.
- **4.10.5 Compliance Panel (`CompliancePanel.jsx`)** — Hard Non-LLM Policy Gates view + Live MCP Tool Evaluator simulator demonstrating real-time stopping rules (`check_retry_allowed`, `check_contact_allowed`, `check_escalation_tier`, `evaluate_action`).
- **4.10.6 Export Button (`exportBatchAuditCSV` / `exportCaseAuditCSV`)** — Triggers individual case CSV audit trail exports (`GET /cases/{case_id}/export/csv`) and full batch report CSV exports (`GET /cases/export/batch/csv`).

---

### 4.11 Backend API Module (FastAPI)

**Purpose:** Enterprise FastAPI application exposing production REST & Server-Sent Event (SSE) endpoints.

**Submodules:**

- **4.11.1 Events Router (`backend/app/routers/events.py`)** — `/events/*` (`/ingest`, `/webhook/razorpay`, `/webhook/stripe`, `/batch-upload`, `/queue/status`).
- **4.11.2 Cases Router (`backend/app/routers/cases.py`)** — `/cases/*` (`GET /cases`, `GET /cases/{case_id}`, `GET /cases/{case_id}/timeline`, `POST /cases/{case_id}/actions`, CSV export endpoints).
- **4.11.3 Batch/Reporting Router (`backend/app/routers/batch.py`)** — `/batch/*` (`/run-batch-recovery`, `/metrics`, `/system-health`).
- **4.11.4 Compliance Router (`backend/app/routers/compliance.py`)** — `/compliance/*` (MCP tool wrappers: `/check-retry`, `/check-contact`, `/escalation-tier`, `/evaluate`, `/logs`).
- **4.11.5 Auth Middleware (`APIKeyAuthMiddleware` in `backend/app/middleware/auth.py`)** — API Key authentication (`X-API-Key`) with route-based bypass rules for health checks and webhook receivers.
- **4.11.6 Streaming Live Event Channel (`backend/app/routers/stream.py`)** — Native FastAPI `StreamingResponse` Server-Sent Events (SSE) channel (`GET /events/stream`) live-streaming case updates and total count syncs to the React dashboard.

---

### 4.12 LLM Routing Module

**Purpose:** Intelligent multi-model routing and 3-tier hybrid failover across Groq, Gemini Pro, and Ollama.

**Submodules:**

- **4.12.1 Task Router (`LLMRouter` in `backend/app/llm/router.py`)** — Evaluates incoming tasks (`task_type="classification"` vs. `task_type="reasoning"`/`generation`) and directs requests to the optimal primary model adapter.
- **4.12.2 Groq Adapter (`GroqAdapter` in `backend/app/llm/groq_adapter.py`)** — Ultra-low latency model adapter with internal candidate failover (`llama-3.3-70b-versatile` -> `llama-3.1-8b-instant` -> `mixtral-8x7b-32768`) for event classification and fast taxonomy pre-filtering.
- **4.12.3 Gemini Adapter (`GeminiAdapter` in `backend/app/llm/gemini_adapter.py`)** — Deep reasoning model adapter with internal candidate failover (`gemini-1.5-flash` -> `gemini-2.0-flash` -> `gemini-1.5-pro`) for ambiguous root cause diagnosis and personalized Hinglish/English copy generation.
- **4.12.4 Hybrid Failover Handler (`LLMRouter` in `backend/app/llm/router.py`)** — 3-tier resilient failover architecture:
  - *Classification*: `Groq (Llama-70b)` $\rightarrow$ `Gemini Pro` $\rightarrow$ `Ollama (Small Model)`.
  - *Reasoning & Generation*: `Gemini Pro` $\rightarrow$ `Groq (Llama-70b)` $\rightarrow$ `Ollama (Small Model)`.

---

## 5A. Storage & Infrastructure Architecture (Deep Dive)

### 5A.1 Storage Map (at a glance)

| Data                                                           | Store                                  | Local Dev                             | Demo/Cloud                     | Persisted?         |
| :------------------------------------------------------------- | :------------------------------------- | :------------------------------------ | :----------------------------- | :----------------- |
| Transactions, Customers, RecoveryCases, PromiseToPay, AuditLog | MongoDB                                | Motor Async Client / In-Memory Mock   | MongoDB Atlas (free tier)      | Yes — permanent   |
| Resolved-case embeddings (RAG)                                 | ChromaDB                               | Local disk (`./chroma_data`)        | Persistent disk / Chroma Cloud | Yes — permanent   |
| Policy knowledge base embeddings                               | ChromaDB (separate collection)         | Same instance, different collection   | Same instance                  | Yes — permanent   |
| Audit CSV/PDF exports                                          | Local filesystem, generated on request | `./backend/exports/`                | Streamed to client in-memory   | No — on demand    |
| Synthetic seed data                                            | Flat CSV file                          | `./data/synthetic_transactions.csv` | Bundled in image               | Yes — source file |

### 5A.2 MongoDB — Detailed Design (`backend/app/db/mongo.py`)

- **Database name:** `reviveai`
- **Driver:** `motor` async driver with fallback to thread-safe `InMemoryCollection`.
- **Collections & Indexes (`setup_indexes`)**:
  - `customers`: `{customer_id: 1}` unique, `{opt_out: 1}`
  - `transactions`: `{transaction_id: 1}` unique, `{customer_id: 1}`, `{status: 1}`
  - `recovery_cases`: `{case_id: 1}` unique, `{status: 1}`, `{event_type: 1}`, `{created_at: -1}`
  - `promises`: `{case_id: 1}`, `{due_date: 1, status: 1}`
  - `audit_logs`: `{case_id: 1, timestamp: 1}`
  - `compliance_decisions`: `{case_id: 1}`

### 5A.10 Backup & Disaster Recovery

| Store                                     | Backup mechanism                                 | Recovery path                                                               |
| :---------------------------------------- | :----------------------------------------------- | :-------------------------------------------------------------------------- |
| **MongoDB Atlas**                   | Automated snapshot (included on free/M0 tier)    | Point-in-time restore via Atlas console                                     |
| **ChromaDB**                        | Fully regenerable vector store                   | Re-run`rebuild_embeddings.py` from MongoDB `recovery_cases` + seed JSON |
| **Seed / Config Files (`data/`)** | Version-controlled in git repository             | `git checkout`                                                            |
| **Secrets (API Keys)**              | Environment variables / Platform secrets manager | Re-entered manually via platform environment settings                       |

### 5A.11 Rough Storage Sizing (Sanity-Check Against Free Tiers)

| Store                                 | Est. volume at 1,000 cases           | Free Tier Capacity           | Fits?               |
| :------------------------------------ | :----------------------------------- | :--------------------------- | :------------------ |
| **MongoDB** (all 6 collections) | ~5,000 docs (< 50MB)                 | Atlas M0 free tier (512MB)   | ✅ Fits comfortably |
| **ChromaDB** `resolved_cases` | ~1,000 vectors x 384 dims (a few MB) | Local disk / Render 1GB disk | ✅ Fits comfortably |
| **ChromaDB** `policy_kb`      | Static, < 100 chunks (< 1MB)         | Local disk / Render 1GB disk | ✅ Negligible       |

---

## 5. Data Architecture & Schemas

### 5.1 Event (canonical, post-ingestion)

```json
{
  "event_id": "string",
  "source": "razorpay | checkout | subscription | invoice_system",
  "customer_id": "string",
  "amount": "number",
  "currency": "INR",
  "raw_payload": "object",
  "received_at": "ISO8601"
}
```

### 5.2 Customer

```json
{
  "customer_id": "string",
  "name": "string",
  "email": "string",
  "phone": "string",
  "payment_methods": ["array"],
  "opt_out": "boolean",
  "history": {
    "past_recoveries": "number",
    "past_failures": "number",
    "lifetime_value": "number"
  }
}
```

### 5.3 Transaction

```json
{
  "transaction_id": "string",
  "customer_id": "string",
  "amount": "number",
  "status": "failed | pending | succeeded",
  "failure_reason": "string | null",
  "timestamp": "ISO8601"
}
```

### 5.4 RecoveryCase

```json
{
  "case_id": "string",
  "transaction_id": "string",
  "event_type": "payment_failure | checkout_abandonment | subscription_dunning | overdue_invoice",
  "risk_score": "number",
  "recovery_probability": "number",
  "root_cause": "string",
  "selected_action": "string",
  "attempts": "number",
  "recovered_amount": "number",
  "status": "detected | diagnosing | deciding | guarded | executing | recovered | escalated | closed | blocked",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### 5.5 PromiseToPay

```json
{
  "promise_id": "string",
  "case_id": "string",
  "promised_amount": "number",
  "due_date": "ISO8601",
  "status": "promised | paid | broken"
}
```

### 5.6 AuditLog

```json
{
  "log_id": "string",
  "case_id": "string",
  "agent": "Detector | Diagnosis | Strategy | ComplianceGuard | Execution | Audit",
  "decision": "string",
  "reason": "string",
  "tool_called": "string | null",
  "timestamp": "ISO8601",
  "result": "object"
}
```

---

## 5A. Storage & Infrastructure Architecture (Deep Dive)

This section answers, concretely, **where every piece of data physically lives**, in both local dev and demo/cloud deployment — so there's no ambiguity when building.

### 5A.1 Storage Map (at a glance)

| Data                                                           | Store                                  | Local Dev                             | Demo/Cloud                                              | Persisted?                           |
| -------------------------------------------------------------- | -------------------------------------- | ------------------------------------- | ------------------------------------------------------- | ------------------------------------ |
| Transactions, Customers, RecoveryCases, PromiseToPay, AuditLog | MongoDB                                | Docker container, volume-mounted      | MongoDB Atlas (free tier)                               | Yes — permanent                     |
| Resolved-case embeddings (RAG)                                 | ChromaDB                               | Local disk (`./chroma_data`)        | Persistent disk on Render, or Chroma Cloud              | Yes — permanent                     |
| Policy knowledge base embeddings                               | ChromaDB (separate collection)         | Same instance, different collection   | Same instance                                           | Yes — permanent                     |
| LLM response cache (optional)                                  | Redis                                  | Docker container                      | Render Redis add-on / Upstash                           | No — TTL-based, ephemeral           |
| Audit CSV/PDF exports                                          | Local filesystem, generated on request | `./backend/exports/` (gitignored)   | Generated in-memory, streamed to client (no disk write) | No — regenerated on demand          |
| Synthetic seed data                                            | Flat CSV file                          | `./data/synthetic_transactions.csv` | Bundled into container image, loaded on first boot      | Yes — source file, not runtime data |
| Secrets / API keys                                             | Environment variables                  | `.env` file (gitignored)            | Platform secrets manager (Render/Vercel env vars)       | N/A                                  |

**Golden rule:** MongoDB is the single source of truth for all transactional/business state. ChromaDB only stores *derived* embeddings that can be regenerated from MongoDB if lost. Nothing should exist in ChromaDB that isn't traceable back to a MongoDB document.

---

### 5A.2 MongoDB — Detailed Design

**Database name:** `reviveai`

**Driver:** `motor` (async MongoDB driver, pairs with FastAPI's async routes)

**Connection:**

```python
# db/mongo.py
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(MONGODB_URI)
db = client["reviveai"]

customers = db["customers"]
transactions = db["transactions"]
recovery_cases = db["recovery_cases"]
promises = db["promises"]
audit_logs = db["audit_logs"]
compliance_decisions = db["compliance_decisions"]
```

**Collections, with indexes:**

| Collection               | Key Fields                                                  | Indexes                                                                             | Why                                                 |
| ------------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------- |
| `customers`            | `customer_id` (unique)                                    | `{customer_id: 1}` unique, `{opt_out: 1}`                                       | Fast opt-out check before every contact action      |
| `transactions`         | `transaction_id`, `customer_id`, `status`             | `{transaction_id: 1}` unique, `{customer_id: 1}`, `{status: 1}`               | Lookup by customer, filter failed txns              |
| `recovery_cases`       | `case_id`, `transaction_id`, `status`, `event_type` | `{case_id: 1}` unique, `{status: 1}`, `{event_type: 1}`, `{created_at: -1}` | Dashboard filtering + sorting by recency            |
| `promises`             | `promise_id`, `case_id`, `due_date`, `status`       | `{case_id: 1}`, `{due_date: 1, status: 1}`                                      | Deadline Watcher scans overdue promises efficiently |
| `audit_logs`           | `case_id`, `timestamp`                                  | `{case_id: 1, timestamp: 1}`                                                      | Case timeline reconstruction in chronological order |
| `compliance_decisions` | `case_id`, `decision`, `timestamp`                    | `{case_id: 1}`                                                                    | Compliance panel drill-down                         |

**Local dev setup (docker-compose):**

```yaml
mongodb:
  image: mongo:7
  ports:
    - "27017:27017"
  volumes:
    - mongo_data:/data/db   # persists across container restarts
volumes:
  mongo_data:
```

**Demo/cloud setup:** MongoDB Atlas free (M0) cluster — `MONGODB_URI` becomes the Atlas connection string in the platform's environment variables. No code changes needed since the driver is URI-agnostic.

**Retention policy (hackathon scope):** No TTL indexes needed — all data kept for the demo lifetime. If long-running, add a TTL index on `audit_logs.timestamp` (e.g., 90 days) for production hygiene, not required now.

---

### 5A.3 ChromaDB — Detailed Design

**Persistence mode:** Local persistent client (no separate server needed for hackathon scale).

```python
# rag/embeddings.py
import chromadb
from chromadb.utils import embedding_functions

client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)  # e.g. "./chroma_data"

embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"   # small, fast, good enough for case similarity
)

resolved_cases = client.get_or_create_collection(
    name="resolved_cases",
    embedding_function=embed_fn
)

policy_kb = client.get_or_create_collection(
    name="policy_kb",
    embedding_function=embed_fn
)
```

**Two collections, clearly separated:**

| Collection         | What's embedded                                                                                                  | Metadata stored alongside                                           | Used by                                                     |
| ------------------ | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------- |
| `resolved_cases` | Text summary:`"{event_type} caused by {root_cause}, amount {amount}, action taken {action}, outcome {result}"` | `case_id, event_type, root_cause, action, outcome, amount_bucket` | Strategy Agent — retrieves top-k similar past cases        |
| `policy_kb`      | Chunked policy text (retry rules, communication rules, escalation rules, refund rules)                           | `policy_type, section`                                            | Strategy Agent — retrieves relevant policy before deciding |

**Write path:** Every time a `RecoveryCase` reaches `status: recovered | closed | escalated`, the Audit Agent writes a summary embedding into `resolved_cases`. This means ChromaDB is always populated from real MongoDB outcomes — it grows as the demo runs, improving future RAG retrieval live during the demo (a good talking point for judges).

**Read path (Strategy Agent):**

```python
results = resolved_cases.query(
    query_texts=[f"{event_type} caused by {root_cause}, amount ~{amount}"],
    n_results=3
)
```

**Local dev:** `./chroma_data/` directory, gitignored, created on first run.
**Demo/cloud:** Mount a persistent disk volume on Render (or use Chroma Cloud if avoiding disk-persistence concerns); path stays the same via `CHROMA_PERSIST_DIR` env var.

**Rebuild strategy:** Since embeddings are derived from MongoDB, a seed script (`scripts/rebuild_embeddings.py`) can re-populate ChromaDB from `recovery_cases` + a static `policy_kb.json` at any time — useful if the vector store is wiped or moved.

---

### 5A.4 Redis — Optional Caching Layer

Not required for MVP, but recommended if LLM latency becomes a demo risk.

**What it caches:**

- LLM classification responses for identical/near-identical inputs (dedupe repeated demo runs)
- Compliance check results within a short TTL (e.g., 60s) to avoid redundant Mongo reads during a retry loop

**Setup:**

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
```

**Not used for:** any data that needs to survive — Redis is purely a speed layer, never a source of truth.

---

### 5A.5 File Exports (Audit CSV/PDF)

- Generated **on-demand** in the `/batch/report/export` and `/cases/{id}/export` endpoints.
- Built in-memory using `pandas` (CSV) or `reportlab`/`weasyprint` (PDF), then streamed directly as an HTTP response (`StreamingResponse`) — **not written to disk in the cloud deployment**, avoiding filesystem persistence issues on ephemeral hosts like Render/Vercel.
- In local dev, an optional `./backend/exports/` folder can be used for debugging generated files, but this is gitignored and not relied upon for correctness.

---

### 5A.6 Environment-Specific Storage Matrix

| Environment             | MongoDB                                       | ChromaDB                                                        | Redis                               | Exports                |
| ----------------------- | --------------------------------------------- | --------------------------------------------------------------- | ----------------------------------- | ---------------------- |
| **Local Dev**     | Docker container + volume                     | Local disk`./chroma_data`                                     | Docker container (optional)         | Streamed or local file |
| **Demo (hosted)** | MongoDB Atlas M0 (free)                       | Persistent disk on Render                                       | Upstash Redis (free tier, optional) | Streamed only          |
| **CI/Test**       | Ephemeral Mongo (mongomock or test container) | In-memory Chroma client (`chromadb.Client()`, no persistence) | Not used                            | Not tested             |

---

### 5A.7 Data Flow Summary (who writes what, when)

```
Detector      → writes RecoveryCase (status: detected) to MongoDB
Diagnosis     → updates RecoveryCase.root_cause in MongoDB
Strategy      → reads ChromaDB (resolved_cases + policy_kb) for context
              → writes RecoveryCase.selected_action to MongoDB
ComplianceGuard → reads Customer.opt_out, RecoveryCase.attempts from MongoDB
                → writes decision to compliance_decisions in MongoDB
Execution     → calls mock provider → writes execution result to MongoDB
Audit         → writes every transition to audit_logs in MongoDB
              → on case close, writes a new embedding into ChromaDB.resolved_cases
```

This makes MongoDB the append-and-update system of record throughout, and ChromaDB a strictly downstream, regenerable index.

---

### 5A.8 Cold-Start Seeding Strategy (the gap in the original plan)

**Problem:** `resolved_cases` in ChromaDB only gets populated when a real case closes (§5A.3 write path). On a fresh boot, that collection is empty — so the Strategy Agent has nothing to retrieve for the first several demo cases, which quietly undercuts the "RAG-informed decision" story right when judges are watching.

**Fix:** ship a small seed dataset of ~30–50 synthetic *already-resolved* cases spanning the common root causes, and load it before any live traffic runs.

- `data/seed_resolved_cases.json` — synthetic resolved-case summaries + outcomes, same shape as the text embedded at runtime (§5A.3)
- `data/policy_kb.json` — retry/communication/escalation/refund rules as text chunks (this collection is static and never grows from live outcomes, so it's *only* ever loaded from this file)
- `scripts/seed_chroma.py` — idempotent: checks each collection's count before inserting, no-ops if already seeded

**Boot order (docker-compose / deployment entrypoint):**

```
1. Mongo up, indexes created
2. scripts/seed_chroma.py     → seeds resolved_cases + policy_kb (skips if already populated)
3. scripts/seed_mongo.py      → loads synthetic_transactions.csv (skips if transactions collection non-empty)
4. Start FastAPI
```

---

### 5A.9 Embedding Consistency

Pin the embedding model as an env var — `EMBEDDING_MODEL=all-MiniLM-L6-v2` — rather than hardcoding it, so it can't silently drift between local/demo environments. If it's ever changed, `resolved_cases` and `policy_kb` must be **fully re-embedded**: vectors from one model aren't compatible with another model's vector space. The rebuild script from §5A.3 (`rebuild_embeddings.py`) already handles this — wipe both collections and re-insert from MongoDB + seed JSON.

---

### 5A.10 Backup & Disaster Recovery

| Store                         | Backup mechanism                                                             | Recovery path                                                               |
| ----------------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| MongoDB Atlas                 | Automated snapshot, included on the free/M0 tier within its retention window | Point-in-time restore via Atlas console                                     |
| ChromaDB                      | None needed — treated as fully regenerable, by design                       | Re-run`rebuild_embeddings.py` from MongoDB `recovery_cases` + seed JSON |
| Seed/config files (`data/`) | Version-controlled in the repo                                               | `git checkout`                                                            |
| Secrets (API keys)            | Platform secrets manager only, never committed                               | Re-entered manually — intentionally not recoverable from any backup        |

---

### 5A.11 Rough Storage Sizing (sanity-check against free tiers)

| Store                      | Est. volume at 1,000 cases                      | Fits in                                |
| -------------------------- | ----------------------------------------------- | -------------------------------------- |
| MongoDB (all collections)  | ~5,000 documents, well under 50MB               | Atlas M0 free tier (512MB) comfortably |
| ChromaDB`resolved_cases` | ~1,000 vectors × 384 dims (MiniLM) — a few MB | Local disk, or a 1GB Render disk       |
| ChromaDB`policy_kb`      | Static, <100 chunks                             | Negligible                             |

At hackathon scale, none of this comes close to needing a paid tier on any store — the free tiers listed in §5A.1 are sufficient for the full build and demo.

---

## 6. API Specification

| Method | Endpoint                  | Purpose                                                                 |
| ------ | ------------------------- | ----------------------------------------------------------------------- |
| POST   | `/events/ingest`        | Ingest single event (webhook)                                           |
| POST   | `/events/batch-upload`  | Upload CSV of synthetic events                                          |
| GET    | `/cases`                | List cases (filterable by status, type, action)                         |
| GET    | `/cases/{id}`           | Full case detail + timeline                                             |
| POST   | `/cases/{id}/actions`   | Manually trigger/override an action (demo control)                      |
| GET    | `/batch/report`         | Aggregate metrics: at-risk ₹, recovered ₹, recovery rate %, breakdown |
| GET    | `/batch/report/export`  | CSV/PDF audit export                                                    |
| GET    | `/compliance/{case_id}` | Compliance decision trail for a case                                    |
| GET    | `/health`               | Service health check                                                    |

---

## 7. Workflow & State Machine Design (LangGraph)

**Nodes:** `detect → diagnose → decide → guard → execute → verify → audit → close`

**Conditional edges:**

- `verify` fails + `attempts < max_retries` → back to `decide` (retry loop)
- `guard` returns `BLOCK` → straight to `audit` → `close` (no execution)
- `guard` returns `ESCALATE` → `execute(ESCALATE_TO_HUMAN)` → `audit` → `close`
- `verify` succeeds → `audit` → `close` (recovered)

**State object passed through graph:**

```json
{
  "case_id": "string",
  "event": {...},
  "diagnosis": {...},
  "decision": {...},
  "guard_result": {...},
  "execution_result": {...},
  "attempts": 0
}
```

---

## 8. Technology Stack

| Layer                   | Technology                                                                              |
| ----------------------- | --------------------------------------------------------------------------------------- |
| Agent Orchestration     | LangGraph (state graph) + CrewAI (agent roles)                                          |
| Tool/Function Calling   | MCP (Model Context Protocol)                                                            |
| LLMs                    | Groq (Llama, fast classification), Gemini Pro (reasoning/generation), OpenAI (failover) |
| RAG                     | ChromaDB / FAISS + Hugging Face Sentence Transformers                                   |
| Backend                 | FastAPI (async), Uvicorn                                                                |
| Database                | MongoDB                                                                                 |
| Cache (optional)        | Redis — see §5A.4                                                                     |
| Frontend                | React                                                                                   |
| Payments (sandbox)      | Razorpay API/Webhooks                                                                   |
| Notifications (stubbed) | Email / SMS / WhatsApp provider interface                                               |
| Infra                   | Docker, GitHub Actions                                                                  |
| Deployment              | Render / Hugging Face Spaces / Vercel                                                   |

---

## 9. Non-Functional Requirements

| Category      | Requirement                                                                                          |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| Latency       | Event classification < 2s; end-to-end case processing < 10s (excluding cooldowns)                    |
| Throughput    | Handle batch of 100+ events without blocking                                                         |
| Reliability   | LLM failover chain (Groq → Gemini → OpenAI) prevents single-provider outage from stopping pipeline |
| Auditability  | 100% of state transitions logged; no silent actions                                                  |
| Idempotency   | No duplicate executions for same case + attempt                                                      |
| Observability | Structured logs per agent; dashboard reflects live state                                             |

---

## 10. Security, Privacy & Compliance

- API-key auth on all ingest endpoints (demo-grade, not production RBAC)
- Customer PII (email/phone) stored in MongoDB only — never sent to LLM prompts unless required for message generation, and even then minimized
- Opt-out/DND flag is a hard block, checked before every customer-facing action
- All secrets (API keys) via environment variables, never hardcoded
- Sandbox-only payment integration — no real financial transactions in the hackathon build

---

## 11. Folder / Repository Structure

```
reviveai/
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── routers/
│   │   │   ├── events.py
│   │   │   ├── cases.py
│   │   │   ├── batch.py
│   │   │   └── compliance.py
│   │   ├── agents/
│   │   │   ├── detector.py
│   │   │   ├── diagnosis.py
│   │   │   ├── strategy.py
│   │   │   ├── execution.py
│   │   │   └── audit.py
│   │   ├── graph/
│   │   │   └── workflow.py        # LangGraph state machine definition
│   │   ├── mcp/
│   │   │   └── compliance_server.py
│   │   ├── rag/
│   │   │   ├── embeddings.py
│   │   │   └── retriever.py
│   │   ├── llm/
│   │   │   ├── router.py
│   │   │   ├── groq_adapter.py
│   │   │   └── gemini_adapter.py
│   │   ├── models/                # Pydantic schemas
│   │   ├── db/
│   │   │   └── mongo.py
│   │   └── tools/                 # mock provider integrations
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── App.jsx
│   ├── package.json
│   └── Dockerfile
├── data/
│   ├── synthetic_transactions.csv
│   ├── seed_resolved_cases.json    # cold-start seed for ChromaDB resolved_cases (§5A.8)
│   └── policy_kb.json              # static policy chunks for ChromaDB policy_kb (§5A.8)
├── scripts/
│   ├── seed_mongo.py                # loads synthetic_transactions.csv, skips if non-empty
│   ├── seed_chroma.py                # loads both seed JSON files, skips if already seeded
│   └── rebuild_embeddings.py         # wipes + re-embeds Chroma from Mongo + seed files (§5A.3, §5A.9)
├── docker-compose.yml
└── README.md
```

---

## 12. Environment Configuration

```
# LLM Providers
GROQ_API_KEY=
GEMINI_API_KEY=
OPENAI_API_KEY=

# Database
MONGODB_URI=

# Vector Store
CHROMA_PERSIST_DIR=./chroma_data
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Cache (optional — see §5A.4)
REDIS_URL=

# Payment Sandbox
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# Notifications (stub)
TWILIO_SID=
TWILIO_AUTH_TOKEN=
SENDGRID_API_KEY=

# Compliance Config
MAX_RETRY_ATTEMPTS=3
RETRY_COOLDOWN_MINUTES=30
MESSAGE_COOLDOWN_HOURS=24
MAX_ESCALATION_TIER=3

# App
API_KEY_SECRET=
ENV=development
```

---

## 13. Testing Strategy

| Test Type         | Coverage                                                                                                          |
| ----------------- | ----------------------------------------------------------------------------------------------------------------- |
| Unit tests        | Each agent's decision logic (Detector classification, Diagnosis cause mapping, Strategy action selection)         |
| Compliance tests  | Verify Compliance Guard blocks over-limit retries, respects cooldowns and opt-outs — highest priority test suite |
| Integration tests | Full LangGraph run: event in → audit log out, for each of the 3 MVP scenarios                                    |
| Load test (light) | Batch of 100 synthetic events processed without errors                                                            |
| Demo rehearsal    | Scripted run-through of both demo journeys (§15) before presenting                                               |

---

## 14. Deployment Plan

1. Local dev: `docker-compose up` (MongoDB + backend + frontend)
2. Backend → Render or Hugging Face Spaces
3. Frontend → Vercel
4. Environment variables set via platform secrets manager
5. On first boot: `seed_chroma.py` (resolved_cases + policy_kb) runs before `seed_mongo.py` (synthetic_transactions.csv) — both idempotent, per the boot order in §5A.8
6. Smoke test all endpoints post-deploy before demo

---

## 15. Demo Script & Evaluation Mapping

| Judging Criterion        | Where It's Shown                                                       |
| ------------------------ | ---------------------------------------------------------------------- |
| Root-cause diagnosis     | Case detail drawer → Diagnosis reasoning summary                      |
| Bounded execution        | Action Catalog (fixed enum) + Compliance Guard logs                    |
| Measured money recovered | Dashboard summary cards                                                |
| Compliant escalation     | Journey 2 (B2B promise-to-pay → broken → escalation)                 |
| Stopping rules           | Journey 3 (3rd retry blocked by Compliance Guard, case auto-escalates) |
| Audit trail              | Export CSV/PDF from any case                                           |

**Journey 1 — Clean recovery:** ₹4,999 subscription fails → bank decline → 87% recovery probability → retry 1/3 allowed → success → recovered → case closed.

**Journey 2 — Escalation:** ₹25,000 B2B invoice overdue → reminder sent → promise-to-pay logged → deadline missed → auto-escalated.

**Journey 3 — Stopping rule fires:** repeated retry attempt blocked by Compliance Guard after max attempts reached → case auto-escalates instead of looping.

---

## 16. Build Timeline (24–48h Sprint Plan)

| Phase                          | Hours   | Deliverable                                                                       |
| ------------------------------ | ------- | --------------------------------------------------------------------------------- |
| 1. Foundation                  | 0–4h   | Mongo schema, FastAPI skeleton, Docker, seed data                                 |
| 2. Detect + Diagnose           | 4–10h  | LangGraph nodes for Detector + Diagnosis working on mock feed                     |
| 3. Strategy + Compliance       | 10–16h | Strategy Agent + MCP Compliance Guard wired together, bounded action set enforced |
| 4. Execution + Audit           | 16–22h | Execution Agent (mock tools) + Audit logging complete                             |
| 5. RAG layer                   | 22–28h | ChromaDB similarity retrieval feeding Strategy Agent                              |
| 6. Dashboard                   | 28–36h | React dashboard: summary cards, case table, detail drawer                         |
| 7. Promise-to-Pay + Escalation | 36–40h | B2B journey complete end-to-end                                                   |
| 8. Polish + Export             | 40–44h | CSV/PDF export, compliance panel, styling                                         |
| 9. Demo rehearsal              | 44–48h | Run all 3 journeys, fix breakages, prep pitch                                     |

---

## 17. Risk Register

| Risk                                               | Impact | Mitigation                                                                                                                         |
| -------------------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| LLM provider rate limits/outage during demo        | High   | Groq→Gemini→OpenAI failover chain; cache demo responses as fallback                                                              |
| Compliance Guard bypassed accidentally by an agent | High   | Guard is a hard architectural gate (MCP server), not a suggestion — execution node cannot be reached without a passed guard check |
| RAG retrieval adds unnecessary latency             | Medium | Cap top-k to 3, run retrieval async with 1s timeout fallback to rule-based mapping                                                 |
| Scope creep (building all 4 example directions)    | High   | MVP locked to 3 scenarios (§2.2, §15)                                                                                            |
| Demo data looks synthetic/unconvincing             | Medium | Use realistic INR amounts, varied customer histories, real decline-code taxonomy                                                   |

---

## 18. Appendix — Glossary

- **Bounded action set:** A fixed, enumerable list of actions an agent may choose from — prevents open-ended/unsafe agent behavior.
- **Compliance Guard:** Deterministic rule layer that approves/blocks/escalates actions before execution.
- **Root cause:** The diagnosed reason a revenue event occurred (e.g., expired card).
- **Recovery probability:** Model-estimated likelihood that a given case can be successfully recovered.
- **Promise-to-pay:** A logged customer commitment to pay by a future date, tracked independently of the main case state.
- **Stopping rule:** A hard limit (retry count, cooldown, opt-out) that halts further automated action on a case.

---

## 19. Tracked Implementation & Built Features Log

| Date       | Module                   | Built Component                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Summary of Implementation                                                                                                                                                                                                                                      |
| ---------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-08-22 | 4.1 Ingestion            | **4.1.3 Event Normalizer** ([`normalizer.py`](file:///d:/agents/ReviveAI/backend/app/ingestion/normalizer.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Normalizes raw events from Razorpay, Stripe, Batch CSV, and generic JSON payloads into canonical`EventSchema`. Auto-converts currency units (paise/cents to INR/USD) and maps gateway error codes to taxonomy.                                               |
| 2026-08-22 | 4.1 Ingestion            | **4.1.1 Webhook Receiver** ([`webhook_receiver.py`](file:///d:/agents/ReviveAI/backend/app/ingestion/webhook_receiver.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Handlers for Razorpay (`payment.failed`, `order.paid`, `subscription.halted`) and Stripe (`payment_intent.payment_failed`, `charge.failed`) webhooks with HMAC signature verification helper methods.                                                |
| 2026-08-22 | 4.1 Ingestion            | **4.1.4 Event Queue** ([`queue.py`](file:///d:/agents/ReviveAI/backend/app/ingestion/queue.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Async thread-safe`asyncio.Queue` with background worker management, async event consumption, and `/events/queue/status` health monitoring.                                                                                                                 |
| 2026-08-22 | 4.1 Ingestion            | **4.1.2 Batch CSV Loader & Router** ([`events.py`](file:///d:/agents/ReviveAI/backend/app/routers/events.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Refactored`/events/ingest`, added `/events/webhook/razorpay`, `/events/webhook/stripe`, `/events/batch-upload`, and `/events/queue/status` endpoints.                                                                                                |
| 2026-08-22 | Agent Architecture       | **System Prompts & Rules** ([`prompts.py`](file:///d:/agents/ReviveAI/backend/app/agents/prompts.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Centralized operating system prompts, decision matrices, and rules for Detector, Diagnosis, Strategy, Execution, and Audit agents.                                                                                                                             |
| 2026-08-22 | Agents                   | **Agent Integration** ([`detector.py`](file:///d:/agents/ReviveAI/backend/app/agents/detector.py), [`diagnosis.py`](file:///d:/agents/ReviveAI/backend/app/agents/diagnosis.py), [`strategy.py`](file:///d:/agents/ReviveAI/backend/app/agents/strategy.py), [`execution.py`](file:///d:/agents/ReviveAI/backend/app/agents/execution.py), [`audit.py`](file:///d:/agents/ReviveAI/backend/app/agents/audit.py))                                                                                                                                                                                           | Updated agents with roles, system prompts, LLM classification/reasoning failover (`Groq` -> `Gemini Pro` -> `Ollama`), and Hinglish personalized message generation.                                                                                     |
| 2026-08-22 | Testing                  | **Unit Test Suite** ([`test_ingestion.py`](file:///d:/agents/ReviveAI/backend/tests/test_ingestion.py), [`test_agents.py`](file:///d:/agents/ReviveAI/backend/tests/test_agents.py))                                                                                                                                                                                                                                                                                                                                                                                                                          | Automated pytest test suite covering normalizer, webhooks, queue, agent prompts, detector, diagnosis, strategy, compliance, and workflow (100% pass rate).                                                                                                     |
| 2026-08-22 | 4.2 Detection            | **4.2.1 Event Classifier** ([`detector.py`](file:///d:/agents/ReviveAI/backend/app/agents/detector.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Keyword rule pre-filter + 3-tier hybrid LLM failover (`Groq` Llama-70b -> `Gemini Pro` -> `Ollama` small model) classifying raw events into 4 standard categories.                                                                                       |
| 2026-08-22 | 4.2 Detection            | **4.2.2 Risk Scorer** ([`detector.py`](file:///d:/agents/ReviveAI/backend/app/agents/detector.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Dynamic risk scoring (0.05–0.95) & recovery probability calculation using customer MongoDB history (`past_failures`, `past_recoveries`, `lifetime_value`, `opt_out`), amount, and payment method type.                                                |
| 2026-08-22 | 4.2 Detection            | **4.2.3 Case Creator** ([`detector.py`](file:///d:/agents/ReviveAI/backend/app/agents/detector.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Case ID formatting, MongoDB`recovery_cases` instantiation with initial status `detected`, and exact Section 4.2 contract JSON output.                                                                                                                      |
| 2026-08-22 | 4.3 Diagnosis            | **4.3.1 Rule Engine** ([`diagnosis.py`](file:///d:/agents/ReviveAI/backend/app/agents/diagnosis.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Deterministic decline code and error status mapping (`BAD_REQUEST_ERROR`, `CARD_EXPIRED`, `GATEWAY_ERROR`, `MANDATE_EXPIRED`, etc.) to instantly determine root cause without latency or API costs.                                                    |
| 2026-08-22 | 4.3 Diagnosis            | **4.3.2 LLM Reasoner** ([`diagnosis.py`](file:///d:/agents/ReviveAI/backend/app/agents/diagnosis.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Multi-tier hybrid LLM reasoning (`Gemini Pro` -> `Groq` Llama-70b -> `Ollama` small model) for ambiguous payment failures and B2B contract nuances.                                                                                                      |
| 2026-08-22 | 4.3 Diagnosis            | **4.3.3 Cause Taxonomy** ([`diagnosis.py`](file:///d:/agents/ReviveAI/backend/app/agents/diagnosis.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Enforces 9 primary root cause categories (`insufficient_funds`, `expired_card`, `bank_decline`, `gateway_timeout`, `mandate_lapse`, `cart_abandoned_shipping`, `cart_abandoned_payment`, `invoice_terms_breach`, `customer_churned`).        |
| 2026-08-22 | 4.3 Diagnosis            | **4.3.4 Confidence Scorer** ([`diagnosis.py`](file:///d:/agents/ReviveAI/backend/app/agents/diagnosis.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Dynamic confidence scoring (0.50–0.99) and collaborative reasoning flagging (`requires_collaborative_reasoning = true`) for low-confidence cases (< 0.80).                                                                                                  |
| 2026-08-22 | 4.4 Strategy             | **4.4.1 Action Catalog** ([`strategy.py`](file:///d:/agents/ReviveAI/backend/app/agents/strategy.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Immutable list of 7 allowed interventions with strict validation preventing un-whitelisted agent actions.                                                                                                                                                      |
| 2026-08-22 | 4.4 Strategy             | **4.4.2 Bounded Decision Matrix** ([`strategy.py`](file:///d:/agents/ReviveAI/backend/app/agents/strategy.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Primary & fallback action matrix rules for all 9 root cause categories, enforcing retry attempt thresholds (`attempts >= 3`) and low probability pruning (`< 15%`).                                                                                        |
| 2026-08-22 | 4.4 Strategy             | **4.4.3 RAG Retriever** ([`strategy.py`](file:///d:/agents/ReviveAI/backend/app/agents/strategy.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Queries ChromaDB vector store (`resolved_cases` + `policy_kb`) for top-k similar historical case outcomes and policy constraints.                                                                                                                          |
| 2026-08-22 | 4.4 Strategy             | **4.4.4 Decision Composer** ([`strategy.py`](file:///d:/agents/ReviveAI/backend/app/agents/strategy.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | 3-tier hybrid LLM failover (`Gemini Pro` -> `Groq` Llama-70b -> `Ollama` small model) combining rules and RAG context into a grounded decision rationale.                                                                                                |
| 2026-08-22 | 4.5 Compliance           | **4.5 MCP Server Submodules** ([`compliance_server.py`](file:///d:/agents/ReviveAI/backend/app/mcp/compliance_server.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Implemented 4.5.1 Retry Limiter, 4.5.2 Cooldown Enforcer, 4.5.3 DND Registry, 4.5.4 Escalation Tier Manager, 4.5.5 Blackout Window Checker, and 4.5.6 Decision Logger.                                                                                         |
| 2026-08-22 | 4.5 Compliance           | **Exposed MCP Tool Endpoints** ([`compliance.py`](file:///d:/agents/ReviveAI/backend/app/routers/compliance.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Added REST API endpoints for`check_retry_allowed`, `check_contact_allowed`, `check_escalation_tier`, and `evaluate_action`.                                                                                                                            |
| 2026-08-22 | Frontend Mapping         | **MCP Live Tool Evaluator** ([`CompliancePanel.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/CompliancePanel.jsx), [`client.js`](file:///d:/agents/ReviveAI/frontend/src/api/client.js))                                                                                                                                                                                                                                                                                                                                                                                                           | Integrated API client functions and an interactive live simulator tab enabling users to evaluate hard non-LLM policy gates in real-time.                                                                                                                       |
| 2026-08-22 | 4.6 Execution            | **4.6 Tool Submodules** ([`execution.py`](file:///d:/agents/ReviveAI/backend/app/agents/execution.py), [`mock_link.py`](file:///d:/agents/ReviveAI/backend/app/tools/mock_link.py))                                                                                                                                                                                                                                                                                                                                                                                                                           | Implemented 4.6.1 Payment Retry Tool, 4.6.2 Messaging Tool (Hinglish/English LLM copy), 4.6.3 Link Generator Tool, 4.6.4 Invoice Reminder Tool, 4.6.5 Escalation Tool, and 4.6.6 Idempotency Guard.                                                            |
| 2026-08-22 | Backend/Frontend Mapping | **Manual Action Execution** ([`cases.py`](file:///d:/agents/ReviveAI/backend/app/routers/cases.py), [`CaseTable.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/CaseTable.jsx), [`TimelineDrawer.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/TimelineDrawer.jsx))                                                                                                                                                                                                                                                                                                                      | Routed`POST /cases/{case_id}/actions` through compliance guard & execution agent; added interactive "⚡ Retry Action" buttons and provider response rendering in dashboard UI.                                                                               |
| 2026-08-22 | 4.7 Audit                | **4.7 Audit Submodules** ([`audit.py`](file:///d:/agents/ReviveAI/backend/app/agents/audit.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Implemented 4.7.1 Audit Writer (RAG vector indexing), 4.7.2 Export Service (CSV generator), and 4.7.3 Case Timeline Builder (enriched timeline).                                                                                                               |
| 2026-08-22 | Backend/Frontend Mapping | **CSV Audit Export & Timeline** ([`cases.py`](file:///d:/agents/ReviveAI/backend/app/routers/cases.py), [`TimelineDrawer.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/TimelineDrawer.jsx), [`Dashboard.jsx`](file:///d:/agents/ReviveAI/frontend/src/pages/Dashboard.jsx))                                                                                                                                                                                                                                                                                                                       | Added`GET /cases/{case_id}/export/csv` & `GET /cases/export/batch/csv` REST endpoints; added "📥 Export Case CSV" & "📥 Export Batch Report CSV" buttons in UI.                                                                                            |
| 2026-08-22 | 4.8 Promise-to-Pay       | **4.8 Promise Submodules** ([`promises.py`](file:///d:/agents/ReviveAI/backend/app/routers/promises.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Implemented 4.8.1 Promise State Machine (`promised` -> `due_date` -> `paid` \| `broken`), 4.8.2 Deadline Watcher scan, and 4.8.3 Re-Queue Handler into Detector workflow.                                                                              |
| 2026-08-22 | Backend/Frontend Mapping | **Promise-to-Pay Tracker UI** ([`PromiseManager.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/PromiseManager.jsx), [`client.js`](file:///d:/agents/ReviveAI/frontend/src/api/client.js))                                                                                                                                                                                                                                                                                                                                                                                                           | Integrated interactive registration form, state filter tabs (`ALL`, `PROMISED`, `PAID`, `BROKEN`), row action buttons ("✅ Mark Paid" / "❌ Mark Broken"), and deadline watcher scan button.                                                           |
| 2026-08-22 | 4.9 RAG Knowledge        | **4.9 RAG Submodules** ([`embeddings.py`](file:///d:/agents/ReviveAI/backend/app/rag/embeddings.py), [`retriever.py`](file:///d:/agents/ReviveAI/backend/app/rag/retriever.py), [`rag.py`](file:///d:/agents/ReviveAI/backend/app/routers/rag.py), [`seed_chroma.py`](file:///d:/agents/ReviveAI/scripts/seed_chroma.py))                                                                                                                                                                                                                                                                                   | Implemented 4.9.1 Embedding Pipeline, 4.9.2 Vector Store (`resolved_cases`), 4.9.3 Policy KB (`policy_kb`), 4.9.4 Retriever REST API (`GET /rag/query`), and 4.9.5 Seed Loader.                                                                          |
| 2026-08-22 | 4.10 Dashboard           | **4.10 React Dashboard Submodules** ([`Dashboard.jsx`](file:///d:/agents/ReviveAI/frontend/src/pages/Dashboard.jsx), [`SummaryCards.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/SummaryCards.jsx), [`CaseTable.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/CaseTable.jsx), [`TimelineDrawer.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/TimelineDrawer.jsx), [`InterventionChart.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/InterventionChart.jsx), [`CompliancePanel.jsx`](file:///d:/agents/ReviveAI/frontend/src/components/CompliancePanel.jsx)) | Built 4.10.1 Summary Cards, 4.10.2 Case Table / Filter View, 4.10.3 Case Detail Drawer, 4.10.4 Intervention Breakdown Chart, 4.10.5 Compliance Panel (MCP simulator), and 4.10.6 Export CSV buttons.                                                           |
| 2026-08-22 | 4.11 Backend API         | **4.11 FastAPI Routers & Middleware** ([`main.py`](file:///d:/agents/ReviveAI/backend/app/main.py), [`auth.py`](file:///d:/agents/ReviveAI/backend/app/middleware/auth.py), [`stream.py`](file:///d:/agents/ReviveAI/backend/app/routers/stream.py))                                                                                                                                                                                                                                                                                                                                                         | Registered 4.11.1 Events Router, 4.11.2 Cases Router, 4.11.3 Batch Router, 4.11.4 Compliance Router, 4.11.5 API Key Auth Middleware, and 4.11.6 SSE Live-Stream Channel (`GET /events/stream`).                                                              |
| 2026-08-22 | 4.12 LLM Routing         | **4.12 Hybrid LLM Router** ([`router.py`](file:///d:/agents/ReviveAI/backend/app/llm/router.py), [`groq_adapter.py`](file:///d:/agents/ReviveAI/backend/app/llm/groq_adapter.py), [`gemini_adapter.py`](file:///d:/agents/ReviveAI/backend/app/llm/gemini_adapter.py), [`ollama_adapter.py`](file:///d:/agents/ReviveAI/backend/app/llm/ollama_adapter.py))                                                                                                                                                                                                                                                 | Implemented 4.12.1 Task Router (`classification` vs `reasoning`), 4.12.2 Groq Adapter (multi-model candidate failover), 4.12.3 Gemini Adapter (Hinglish copy & reasoning), and 4.12.4 3-tier hybrid failover chain (`Groq` -> `Gemini` -> `Ollama`). |
| 2026-08-22 | 5A Storage Architecture  | **5A Storage & Infrastructure** ([`mongo.py`](file:///d:/agents/ReviveAI/backend/app/db/mongo.py), [`rebuild_embeddings.py`](file:///d:/agents/ReviveAI/scripts/rebuild_embeddings.py))                                                                                                                                                                                                                                                                                                                                                                                                                       | Configured 5A.1 Storage Map, 5A.2 MongoDB indexes (`setup_indexes` for customers, txns, recovery_cases, promises, audit_logs, compliance_decisions), 5A.3 ChromaDB rebuild script, 5A.10 Backup & Disaster Recovery, and 5A.11 Storage Sizing sanity checks. |
| 2026-08-22 | Section 6 API Spec       | **Section 6 REST API Endpoints** ([`events.py`](file:///d:/agents/ReviveAI/backend/app/routers/events.py), [`cases.py`](file:///d:/agents/ReviveAI/backend/app/routers/cases.py), [`batch.py`](file:///d:/agents/ReviveAI/backend/app/routers/batch.py), [`compliance.py`](file:///d:/agents/ReviveAI/backend/app/routers/compliance.py), [`main.py`](file:///d:/agents/ReviveAI/backend/app/main.py))                                                                                                                                                                                                     | Validated 9 core endpoints:`POST /events/ingest`, `POST /events/batch-upload`, `GET /cases`, `GET /cases/{id}`, `POST /cases/{id}/actions`, `GET /batch/report`, `GET /batch/report/export`, `GET /compliance/{case_id}`, and `GET /health`. |
| 2026-08-22 | Section 7 Workflow       | **Section 7 LangGraph Workflow** ([`workflow.py`](file:///d:/agents/ReviveAI/backend/app/graph/workflow.py))                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Implemented 8-node state machine (`detect` -> `diagnose` -> `decide` -> `guard` -> `execute` -> `verify` -> `audit_close` -> `END`) with conditional retry edge back to `decide` on failed verification when `attempts < 3`.               |

---

*End of documentation. Tracked build log verified. All system modules 4.1 to 4.12, Section 5A Storage Architecture, Section 6 API Specification, and Section 7 LangGraph Workflow complete, fully integrated, tested, and verified.*
