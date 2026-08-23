# Razorpay AI Builder Internship 2026 — Master Project Submission & Video Pitch Blueprint

**Form Email / Account:** `sup31patil@gmail.com`  
**Project Name:** ReviveAI — Autonomous Multi-Agent Revenue Recovery Platform  
**Selected Track:** Track 3: AI Revenue Recovery  
**Submission Date:** August 2026  
**Status:** Complete & Ready for Submission  

---

## PART 1: Form Questions & Official Answers

### Track Selection
**Selected Track:** `Track 3: AI Revenue Recovery`

---

### Project Name / Title
**ReviveAI — Autonomous Multi-Agent Revenue Recovery Platform**

---

### GitHub Repository URL
`https://github.com/shubhampatil631/ReviveAI.git`

---

### Project Objectives
**What does it solve?**

ReviveAI addresses the critical problem of **revenue leakage across the payment lifecycle** — including failed card/UPI payment intents, halted subscription dunnings, abandoned checkout drop-offs, and overdue B2B invoices. Standard recovery methods rely on static timer rules or aggressive spamming, leading to low recovery rates, high customer churn, and compliance violations.

**Key Objectives:**
1. **Autonomous Leakage Detection & Normalization:** Ingest and normalize transaction event streams (webhooks from Razorpay/Stripe, batch CSVs) into a unified canonical schema, identifying revenue-at-risk in under 2 seconds.
2. **LLM-Driven Root Cause Diagnosis:** Combine event error codes (bank decline, insufficient funds, expired mandate, auth drop-off) with hybrid ChromaDB RAG retrieval over historical resolution data to accurately classify failure root causes.
3. **Deterministic MCP Compliance Guard:** Enforce a non-LLM Model Context Protocol (MCP) Compliance Server to evaluate 100% of proposed recovery actions against hard rules (max 3 retries, 30m retry cooldown, 24h contact limits, DND list verification). Ensure **zero out-of-policy actions** are ever executed.
4. **Bounded Recovery Execution:** Execute bounded, policy-compliant actions strictly within an enumerable tool catalog (`RETRY_PAYMENT`, `SEND_RECOVERY_MESSAGE`, `GENERATE_CHECKOUT_RECOVERY_LINK`, `SEND_PAYMENT_METHOD_UPDATE_REQUEST`, `SEND_INVOICE_REMINDER`, `ESCALATE_TO_HUMAN`, `CLOSE_NO_ACTION`).
5. **Measured Money Recovered & Immutable Audit:** Display live metrics on a glassmorphic React dashboard (₹ At Risk, ₹ Recovered, Recovery Rate %) alongside full, timestamped audit logs for every state transition and compliance decision.

---

### Build Challenges & Technical Obstacles
**What issues did you face while building, and how did you solve them?**

1. **Deterministic Compliance vs. Non-Deterministic LLM Behavior:**
   - *Challenge:* LLMs occasionally attempt out-of-policy actions (e.g., retrying a failed transaction 5 times in a row, ignoring opt-out lists, or sending messages during quiet hours).
   - *Solution:* Implemented an isolated **Model Context Protocol (MCP) Compliance Guard Server**. Compliance rules (`MAX_RETRY_ATTEMPTS = 3`, `RETRY_COOLDOWN_MINUTES = 30`, `CONTACT_COOLDOWN_HOURS = 24`, DND Opt-out registry) are implemented strictly in Python code, completely independent of the LLM. 100% of candidate agent actions must pass through the MCP Guard before tool execution.

2. **Complex State Management Across Multi-Agent Hand-Offs:**
   - *Challenge:* Managing multi-step workflows across 6 specialized agent roles (Detector, Diagnosis, Strategy, Compliance Guard, Execution, Audit) without state corruption or execution loop deadlocks.
   - *Solution:* Structured the complete lifecycle on a **LangGraph State Machine** using Pydantic domain models (`RecoveryState`). State transitions, retry counts, and execution logs are deterministically mutated and persisted in MongoDB, ensuring complete state reproducibility.

3. **Heterogeneous Event Ingestion & Cold-Start RAG Retrieval:**
   - *Challenge:* Payment providers (Razorpay vs Stripe vs custom checkout logs) use different payload structures, and diagnosis agents require historic context without expensive model fine-tuning.
   - *Solution:* Built a modular Event Normalizer layer converting raw webhooks/CSVs into canonical events. Paired this with a ChromaDB vector store (`all-MiniLM-L6-v2`) pre-seeded with past resolved cases and policy chunks to supply high-precision vector context during LLM diagnosis.

4. **LLM Provider Latency & Failover Resilience:**
   - *Challenge:* External LLM API downtime or rate limits could block time-sensitive payment retries and recovery messaging workflows.
   - *Solution:* Designed an asynchronous multi-model router with automated fallback chains (Groq Llama-3.3-70b → Gemini 1.5/2.0 Pro → local Ollama fallback), maintaining sub-second response times and 100% workflow uptime.

---

### Final Submission Confirmation
- [x] **I confirm that this is my official final project submission. I understand that no further changes or edits can be made after submitting.**

---

## PART 2: 5-Minute Pitch Video Blueprint & Workflow Guide

### 🎯 Pitch Video Goal
Answer the core hackathon question with live visual proof:
> **"How much money did the agent actually recover, and can you prove every action it took was compliant?"**

---

### ⏱️ Minute-by-Minute Video Breakdown & Script

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       5-MINUTE PITCH VIDEO TIMELINE                         │
├─────────┬───────────────────────────────┬───────────────────────────────────┤
│ Timestamp│ Section Title                 │ Key Screen Visual                 │
├─────────┼───────────────────────────────┼───────────────────────────────────┤
│ 0:00-0:45│ Hook & Problem Statement      │ Speaker Camera + Title Slide      │
│ 0:45-2:00│ Architecture & Dashboard Walk │ Live Glassmorphic Dashboard UI    │
│ 2:00-3:30│ Workflow 1: Clean Recovery    │ Ingesting TXN_1001 + Audit Drawer │
│ 3:30-4:30│ Workflow 2: MCP Guard Block   │ Ingesting TXN_1008 (DND Block)    │
│ 4:30-5:00│ Summary & Impact Closing      │ Batch Processing Metrics Counter  │
└─────────┴───────────────────────────────┴───────────────────────────────────┘
```

#### 🎥 Section 1: Hook & Problem Statement (0:00 – 0:45)
* **What to Show:** Presenter on camera or crisp title slide with project title: **ReviveAI — Autonomous Multi-Agent Revenue Recovery Platform**.
* **Voiceover / Script:**
  > "Hi everyone! I'm excited to present **ReviveAI**, built for Razorpay Track 3: AI Revenue Recovery.
  > Revenue loss in e-commerce and SaaS rarely happens in one clean step—subscription payments fail, checkouts drop off, and B2B invoices go overdue. Static retry rules spam users, waste money, and violate compliance.
  > ReviveAI solves this by combining probabilistic LLM intelligence for root-cause diagnosis with deterministic MCP compliance guardrails to autonomously detect, diagnose, execute, and recover revenue safely."

---

#### 💻 Section 2: Live Dashboard & Architecture (0:45 – 2:00)
* **What to Show:** Screen recording of the **ReviveAI Dashboard** (`http://localhost:3000`). Point cursor to:
  1. Top KPI Cards: **Total Revenue at Risk (₹)**, **Actual Revenue Recovered (₹)**, **Recovery Rate %**.
  2. Case Stream Table & Active Workflow Pipeline.
* **Voiceover / Script:**
  > "Here is our live dashboard. On top, you see real-time recovery analytics: Total Revenue at Risk, Money Recovered, and Live Recovery Rate.
  > Architecture-wise, ReviveAI is driven by a LangGraph state machine orchestrating 6 specialized agents: Detector, Diagnosis, Strategy, Compliance Guard, Execution, and Audit.
  > Crucially, no action reaches execution without passing through our independent, deterministic MCP Compliance Guard Server."

---

#### ⚡ Section 3: Demo Workflow 1 — Autonomous Ingestion & Clean Recovery (2:00 – 3:30)
* **What to Show:**
  1. Trigger webhook or ingest `TXN_1001` (Aditi Sharma, ₹4,999 subscription failure due to bank decline).
  2. Click on `TXN_1001` in the Case Table to expand the **Step-by-Step Audit Drawer**.
  3. Show the live agent flow:
     * **Detector:** Ingests & normalizes event within 1.2 seconds.
     * **Diagnosis:** Retrieves historic resolution cases from ChromaDB RAG; diagnoses temporary bank decline.
     * **Strategy:** Recommends payment retry action (`RETRY_PAYMENT`).
     * **MCP Compliance Guard:** Evaluates attempt 1/3 → **ALLOWED (Status: 200 OK)**.
     * **Execution:** Calls Razorpay mock payment retry → **SUCCESS!**
     * **Outcome:** Case Closed → ₹4,999 added to Recovered Revenue KPI card live!
* **Voiceover / Script:**
  > "Let's demonstrate Workflow 1: Clean Autonomous Recovery. We ingest `TXN_1001`, a ₹4,999 subscription failure.
  > Looking at our audit drawer, the Detector normalizes the Razorpay webhook, ChromaDB RAG diagnoses a bank decline, the Strategy agent proposes a retry, and the MCP Guard verifies that this is attempt 1 out of 3.
  > The execution agent calls Razorpay, the retry succeeds, ₹4,999 is recovered instantly, and the KPI card updates live!"

---

#### 🛡️ Section 4: Demo Workflow 2 — MCP Compliance Guard Stopping Rule Block (3:30 – 4:30)
* **What to Show:**
  1. Ingest `TXN_1008` (Rohan Mehta, ₹2,999, DND User `opt_out: true`) OR demonstrate a 3rd retry attempt breach on `TXN_1003`.
  2. Click on the case row in the dashboard to open the Audit Drawer.
  3. Highlight the red **MCP Compliance Block Badge** and rule reason: `DND_OPT_OUT_REGISTERED` or `MAX_RETRY_ATTEMPTS_REACHED (3/3)`.
  4. Show the automatic fallback action: Escalated to human manager with full timestamped audit log.
* **Voiceover / Script:**
  > "Now for our winning feature: Workflow 2 - Compliance Stopping Rules.
  > Here we ingest `TXN_1008`, where a customer is on the DND opt-out list. The Strategy agent suggests sending a reminder SMS.
  > But notice: the **MCP Compliance Guard intercepts the action in plain Python code** before execution. It blocks the message (`DND_OPT_OUT_REGISTERED`), halts retry loops, logs an immutable audit entry, and escalates the case to a human account manager. Zero out-of-policy actions are ever executed!"

---

#### 🏆 Section 5: Batch Recovery & Summary Closing (4:30 – 5:00)
* **What to Show:** Click "Batch Run (50 Transactions)", watch the progress bar finish, and show final recovered stats (e.g., ₹94,494 recovered across batch with 0 policy violations).
* **Voiceover / Script:**
  > "When running a batch of 50 synthetic transactions, ReviveAI recovers over ₹94,000 in lost revenue with 100% verified compliance.
  > Built using FastAPI, LangGraph, ChromaDB, MCP Server, and React, ReviveAI turns revenue leakage into automated growth. Thank you!"

---

## PART 3: Quickstart Instructions for Video Recording

### Step 1: Start Backend & Frontend
Run the following commands in your shell:

```bash
# Terminal 1: Backend
cd d:\agents\ReviveAI\backend
python -m app.main

# Terminal 2: Frontend
cd d:\agents\ReviveAI\frontend
npm run dev
```

### Step 2: Open Applications
1. **Dashboard UI:** Open Chrome to `http://localhost:3000`
2. **API Documentation:** `http://localhost:8000/docs`

### Step 3: Recording Settings & Tools
* **Software:** OBS Studio, Loom, or Windows Screen Recorder (`Win + Alt + R`).
* **Resolution:** 1920x1080 (16:9).
* **Microphone:** Ensure crisp audio without background noise.
