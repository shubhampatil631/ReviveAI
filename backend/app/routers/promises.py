import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from backend.app.db.mongo import get_db
from backend.app.models.schemas import PromiseToPaySchema
from backend.app.graph.workflow import run_recovery_workflow

logger = logging.getLogger("reviveai.routers.promises")
router = APIRouter(prefix="/promises", tags=["Promise-to-Pay Module"])

@router.post("/create")
async def create_promise(payload: Dict[str, Any]):
    """
    4.8.1 Promise State Machine: Logs a written/verbal payment commitment from a customer.
    State transition: case -> promised.
    """
    case_id = str(payload.get("case_id", "")).strip()
    try:
        amount = float(payload.get("promised_amount", 0.0))
    except (ValueError, TypeError):
        amount = 0.0
    try:
        days_due = int(payload.get("days_due", 3))
    except (ValueError, TypeError):
        days_due = 3

    if not case_id:
        raise HTTPException(status_code=400, detail="case_id is required")

    db = get_db()
    cases_col = db.get_collection("recovery_cases")

    # Smart lookup for case_id (handles CASE_LIVE_03, TXN_LIVE_03, LIVE_03)
    case_doc = await cases_col.find_one({"case_id": case_id})
    if not case_doc:
        clean_id = case_id.replace('CASE_', '').replace('TXN_', '')
        case_doc = await cases_col.find_one({"$or": [
            {"case_id": f"CASE_{clean_id}"},
            {"transaction_id": case_id},
            {"transaction_id": f"TXN_{clean_id}"},
            {"case_id": {"$regex": clean_id, "$options": "i"}}
        ]})
        if case_doc:
            case_id = case_doc["case_id"]

    due_date = datetime.utcnow() + timedelta(days=days_due)
    clean_suffix = case_id[-4:] if len(case_id) >= 4 else case_id
    promise_id = f"PROM_{clean_suffix}_{datetime.utcnow().strftime('%M%S')}_{uuid.uuid4().hex[:6]}"

    promise_doc = {
        "promise_id": promise_id,
        "case_id": case_id,
        "promised_amount": amount,
        "due_date": due_date.isoformat(),
        "status": "promised",
        "created_at": datetime.utcnow().isoformat()
    }

    col = db.get_collection("promises")
    await col.insert_one(promise_doc)

    # Update case status to promised_to_pay
    await cases_col.update_one(
        {"case_id": case_id},
        {"$set": {"status": "promised_to_pay", "updated_at": datetime.utcnow().isoformat()}}
    )

    promise_doc.pop("_id", None)
    return {"message": "Promise-to-Pay registered", "promise": promise_doc}

@router.get("")
async def list_promises(status: Optional[str] = None):
    """
    Lists all recorded customer payment promises, optionally filtered by status.
    """
    db = get_db()
    col = db.get_collection("promises")
    query = {}
    if status and status != "all":
        query["status"] = status.lower()

    cursor = col.find(query).sort("due_date", 1)
    promises = await cursor.to_list()
    for p in promises:
        p.pop("_id", None)
    return {"promises": promises, "total": len(promises)}

@router.post("/{promise_id}/mark-paid")
async def mark_promise_paid(promise_id: str):
    """
    4.8.1 Promise State Machine transition: promised -> paid.
    Updates promise status to 'paid' and case status to 'recovered'.
    """
    db = get_db()
    col = db.get_collection("promises")
    promise = await col.find_one({"promise_id": promise_id})

    if not promise:
        raise HTTPException(status_code=404, detail="Promise not found")

    await col.update_one({"promise_id": promise_id}, {"$set": {"status": "paid", "updated_at": datetime.utcnow().isoformat()}})

    # Update case status to recovered
    case_id = promise.get("case_id")
    cases_col = db.get_collection("recovery_cases")
    await cases_col.update_one(
        {"case_id": case_id},
        {"$set": {
            "status": "recovered",
            "recovered_amount": promise.get("promised_amount", 0.0),
            "updated_at": datetime.utcnow().isoformat()
        }}
    )

    return {"message": f"Promise {promise_id} marked as PAID.", "status": "paid"}

@router.post("/{promise_id}/mark-broken")
async def mark_promise_broken(promise_id: str):
    """
    4.8.1 & 4.8.3 Promise State Machine transition: promised -> broken.
    Triggers 4.8.3 Re-Queue Handler into Detector pipeline.
    """
    db = get_db()
    col = db.get_collection("promises")
    cases_col = db.get_collection("recovery_cases")

    promise = await col.find_one({"promise_id": promise_id})
    if not promise:
        raise HTTPException(status_code=404, detail="Promise not found")

    await col.update_one({"promise_id": promise_id}, {"$set": {"status": "broken", "updated_at": datetime.utcnow().isoformat()}})

    case_id = promise.get("case_id")
    case = await cases_col.find_one({"case_id": case_id})

    requeue_res = {}
    if case:
        event_payload = {
            "event_id": f"REQUEUE_BROKEN_{promise_id}",
            "transaction_id": case.get("transaction_id") or f"TXN_{case_id}",
            "customer_id": case.get("customer_id"),
            "event_type": "overdue_invoice",
            "amount": case.get("amount"),
            "failure_reason": "broken_promise_to_pay"
        }
        requeue_res = await run_recovery_workflow(event_payload)

    return {
        "message": f"Promise {promise_id} marked as BROKEN. Case re-queued to Detector agent.",
        "status": "broken",
        "requeue_result": requeue_res
    }

@router.post("/check-deadlines")
async def deadline_watcher():
    """
    4.8.2 & 4.8.3 Deadline Watcher & Re-Queue Handler:
    Scans for overdue promises. Any promise past its due_date without status 'paid' is marked 'broken'
    and automatically re-queued into the LangGraph Detector pipeline as a high-priority event.
    """
    db = get_db()
    col = db.get_collection("promises")
    cases_col = db.get_collection("recovery_cases")

    cursor = col.find({"status": "promised"})
    promises = await cursor.to_list()

    now = datetime.utcnow()
    processed = []

    for p in promises:
        due = p.get("due_date")
        if isinstance(due, str):
            due = datetime.fromisoformat(due.replace("Z", "+00:00"))

        if now > due:
            # Mark promise broken
            await col.update_one({"promise_id": p["promise_id"]}, {"$set": {"status": "broken", "updated_at": datetime.utcnow().isoformat()}})
            
            # Re-queue into detector pipeline as broken promise
            case_id = p["case_id"]
            case = await cases_col.find_one({"case_id": case_id})
            
            if case:
                event_payload = {
                    "event_id": f"REQUEUE_BROKEN_PROMISE_{case_id}",
                    "transaction_id": case.get("transaction_id") or f"TXN_{case_id}",
                    "customer_id": case.get("customer_id"),
                    "event_type": "overdue_invoice",
                    "amount": case.get("amount"),
                    "failure_reason": "broken_promise_to_pay"
                }
                requeue_res = await run_recovery_workflow(event_payload)
                processed.append({
                    "promise_id": p["promise_id"],
                    "case_id": case_id,
                    "status": "broken",
                    "action": "requeued_to_detector",
                    "result_status": requeue_res.get("final_status")
                })

    return {
        "message": f"Deadline Watcher executed. Handled {len(processed)} overdue promises.",
        "processed": processed
    }
