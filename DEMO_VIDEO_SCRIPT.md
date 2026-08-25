# ReviveAI — Shortened & Punchy Video Demo Script (3.5 – 4 Min)

**Project:** ReviveAI — Autonomous Multi-Agent Revenue Recovery Platform  
**Track:** Razorpay AI Builder Internship 2026 — Track 3: AI Revenue Recovery  
**Target Duration:** ~3:30 - 4:00 Minutes (or relaxed 5 minutes)  
**Total Spoken Words:** ~346 Words (~85 - 100 Words/Min — Crisp, Ultra-Easy to Record)  
**Live CSV Demo Dataset File:** [`data/live_demo_test.csv`](file:///d:/agents/ReviveAI/data/live_demo_test.csv)  

---

## ⏱️ Reduced Word Count & Timing Matrix

| Section | Timestamp | Duration | Spoken Words | On-Screen Visual & Action Cues |
| :--- | :--- | :--- | :--- | :--- |
| **1. Hook & Problem** | `0:00 - 0:35` | 35s | 62 words | Speaker on camera / Title slide |
| **2. Dashboard & Architecture** | `0:35 - 1:25` | 50s | 58 words | Highlight Dashboard KPI cards & MCP Badge |
| **3. Scene 1: Clean Recovery (`TXN_LIVE_01`)** | `1:25 - 2:15` | 50s | 65 words | Click `TXN_LIVE_01`, open Audit Drawer |
| **4. Scene 2: Smart Outreach (`TXN_LIVE_02`)** | `2:15 - 3:00` | 45s | 58 words | Click `TXN_LIVE_02`, show `SEND_PAYMENT_METHOD` |
| **5. Scene 3: Promise Engine (`TXN_LIVE_03`)** | `3:00 - 3:45` | 45s | 68 words | Click `TXN_LIVE_03`, open Promise-to-Pay tab |
| **6. Closing Summary** | `3:45 - 4:00` | 15s | 25 words | Full Dashboard view |
| **TOTAL** | **`0:00 - 4:00`** | **240s** | **346 Words** | **Spacious, Crisp & Extremely Professional** |

---

## 📄 Live Demo CSV Dataset (`data/live_demo_test.csv`)

```csv
transaction_id,customer_id,customer_name,customer_email,customer_phone,event_type,amount,currency,failure_reason,payment_method,opt_out,created_at
TXN_LIVE_01,CUST_L101,Aarav Sharma,aarav.sharma@techstar.io,+919876501122,subscription_dunning,4999,INR,bank_decline,credit_card,false,2026-08-24T09:15:00Z
TXN_LIVE_02,CUST_L102,Pooja Hegde,pooja.h@dndsubscriber.com,+919765404455,subscription_dunning,7999,INR,insufficient_funds,upi,true,2026-08-24T10:15:00Z
TXN_LIVE_03,CUST_L103,Vikramaditya Rao,vikram@enterprisesolutions.com,+919556601122,overdue_invoice,85000,INR,invoice_terms_breach,bank_transfer,false,2026-08-24T11:00:00Z
```

---

## 🎙️ Shortened Word-for-Word Voiceover Script

### 🎥 Section 1: Hook & Financial Problem Statement (0:00 – 0:35)
* **Visual:** Camera or crisp title slide.

```text
[0:00 - 0:15] SPEAKER (CAMERA):
"Hello judges! Businesses lose over 15% of ARR to payment failures, bank declines, and overdue invoices."
[PAUSE 1 SECOND]

[0:15 - 0:25] VISUAL CUE: Cut to static problem diagram.
"Traditional recovery relies on dumb timer rules that spam customers and violate DND compliance."
[PAUSE 1 SECOND]

[0:25 - 0:35] VISUAL CUE: Cut to ReviveAI Dashboard.
"Meet ReviveAI — an autonomous revenue recovery platform powered by a 6-agent LangGraph state machine, ChromaDB RAG, and an independent Model Context Protocol Compliance Guard that recovers lost revenue safely and deterministically."
```

---

### 💻 Section 2: Dashboard & Architecture Overview (0:35 – 1:25)
* **Visual:** Live Dashboard (`http://localhost:3000`). Hover on KPI cards and Agent Workflow.

```text
[0:35 - 0:55] VISUAL CUE: Hover on top KPI Summary Cards.
"Here is our live ReviveAI Dashboard displaying real-time metrics: Total Revenue at Risk, Recovered Money, and Recovery Rate."
[PAUSE 2 SECONDS]

[0:55 - 1:15] VISUAL CUE: Point to Agent Pills (Detector -> Diagnosis -> Strategy -> Compliance -> Execution).
"Under the hood, 6 specialized LangGraph agents normalize events, run ChromaDB RAG diagnosis, and calculate optimal recovery strategies."
[PAUSE 2 SECONDS]

[1:15 - 1:25] VISUAL CUE: Highlight green 'MCP Compliance Guard Active' badge.
"Crucially, every single action is verified by our independent Model Context Protocol Compliance Guard before execution."
```

---

### ⚡ Section 3: Demo Scene 1 — Clean Recovery (`TXN_LIVE_01`) (1:25 – 2:15)
* **Visual:** Click `TXN_LIVE_01` (Aarav Sharma, ₹4,999) $\rightarrow$ Open Audit Drawer.

```text
[1:25 - 1:45] ACTION CUE: Click row TXN_LIVE_01.
"In Scene 1, we ingest TXN_LIVE_01, a ₹4,999 failed subscription."
[PAUSE 2 SECONDS - Audit drawer opens]

[1:45 - 2:00] VISUAL CUE: Highlight JSON Audit Drawer steps.
"Opening our live audit drawer, the Detector normalizes the event, ChromaDB diagnoses a temporary bank decline, and Strategy selects RETRY_PAYMENT."
[PAUSE 2 SECONDS]

[2:00 - 2:15] VISUAL CUE: Point to MCP APPROVED -> Status: RECOVERED.
"The MCP Guard verifies attempt 1 of 3, approves execution, the payment succeeds, and ₹4,999 is added to our Recovered Revenue instantly!"
```

---

### 🛡️ Section 4: Demo Scene 2 — Smart Outreach (`TXN_LIVE_02`) (2:15 – 3:00)
* **Visual:** Click `TXN_LIVE_02` (Pooja Hegde, ₹7,999) $\rightarrow$ Audit Drawer showing `SEND_PAYMENT_METHOD`.

```text
[2:15 - 2:35] ACTION CUE: Click row TXN_LIVE_02.
"For TXN_LIVE_02, a ₹7,999 failure due to insufficient funds, direct retries would fail. Strategy selects SEND_PAYMENT_METHOD."
[PAUSE 2 SECONDS]

[2:35 - 3:00] VISUAL CUE: Point to MCP evaluation & SMS link dispatch.
"The MCP Guard checks customer preferences and approves dispatching a secure payment update link via SMS, allowing the user to update details without intrusive retry spam."
```

---

### 🤝 Section 5: Demo Scene 3 — Payment Link & Promise Engine (`TXN_LIVE_03`) (3:00 – 3:45)
* **Visual:** Click `TXN_LIVE_03` (Vikramaditya Rao, ₹85,000) $\rightarrow$ Open Promise-to-Pay tab $\rightarrow$ Click 'Log New Commitment' $\rightarrow$ Click 'Run Deadline Watcher'.

```text
[3:00 - 3:15] ACTION CUE: Click row TXN_LIVE_03. Highlight GENERATE_LINK.
"For B2B invoice TXN_LIVE_03 (₹85,000), ReviveAI generates an instant payment link."
[PAUSE 2 SECONDS]

[3:15 - 3:30] ACTION CUE: Switch to Promise-to-Pay tab, click Log New Commitment (CASE_LIVE_03, ₹85,000).
"When the client commits to pay in 3 days, we log it in our Promise-to-Pay Engine, pausing outreach."
[PAUSE 2 SECONDS]

[3:30 - 3:45] ACTION CUE: Click 'Run Deadline Watcher' scan button. Show status 'broken' and auto-requeue.
"If the deadline passes unpaid, our Deadline Watcher flags it broken and re-queues the case back into the Detector pipeline for urgent resolution!"
```

---

### 🏆 Section 6: Winning Closing (3:45 – 4:00)
* **Visual:** Full Dashboard showing final stats.

```text
[3:45 - 4:00] SPEAKER (CAMERA / DASHBOARD):
"Combining LangGraph multi-agents, ChromaDB RAG, deterministic MCP guardrails, and Promise-to-Pay tracking, ReviveAI turns revenue leakage into automated growth with 100% compliance. Thank you!"
```
