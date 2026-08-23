import csv
import io
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Header, Query
from backend.app.ingestion.normalizer import EventNormalizer
from backend.app.ingestion.webhook_receiver import WebhookReceiver
from backend.app.ingestion.queue import event_queue
from backend.app.graph.workflow import run_recovery_workflow

logger = logging.getLogger("reviveai.routers.events")
router = APIRouter(prefix="/events", tags=["Events & Ingestion"])

@router.post("/ingest")
async def ingest_event(payload: Dict[str, Any], async_mode: bool = Query(False)):
    """
    4.1.1 & 4.1.3 Ingestion Endpoint:
    Normalizes incoming raw event from any source into canonical Event schema.
    If async_mode=true, enqueues into 4.1.4 Event Queue.
    Otherwise, processes synchronously through the ReviveAI workflow.
    """
    normalized_event = EventNormalizer.normalize(payload)
    logger.info(f"[Events API] Ingested event {normalized_event['event_id']} (async={async_mode})")

    if async_mode:
        enqueued = await event_queue.enqueue(normalized_event)
        if not enqueued:
            raise HTTPException(status_code=503, detail="Event Queue is full. Please try again later.")
        return {
            "status": "queued",
            "event_id": normalized_event["event_id"],
            "source": normalized_event["source"],
            "message": "Event queued for background processing."
        }

    result = await run_recovery_workflow(normalized_event)
    return {
        "status": "processed",
        "case_id": result.get("case_id"),
        "event_id": normalized_event["event_id"],
        "event_type": result.get("event_type"),
        "final_status": result.get("final_status"),
        "recovered_amount": result.get("recovered_amount"),
        "attempts": result.get("attempts")
    }

@router.post("/webhook/razorpay")
async def razorpay_webhook(
    payload: Dict[str, Any], 
    x_razorpay_signature: Optional[str] = Header(None)
):
    """
    4.1.1 Webhook Receiver for Razorpay payloads.
    """
    normalized = WebhookReceiver.process_webhook(payload, provider="razorpay")
    result = await run_recovery_workflow(normalized)
    return {
        "status": "processed",
        "provider": "razorpay",
        "case_id": result.get("case_id"),
        "final_status": result.get("final_status"),
        "recovered_amount": result.get("recovered_amount")
    }

@router.post("/webhook/stripe")
async def stripe_webhook(
    payload: Dict[str, Any], 
    stripe_signature: Optional[str] = Header(None)
):
    """
    4.1.1 Webhook Receiver for Stripe payloads.
    """
    normalized = WebhookReceiver.process_webhook(payload, provider="stripe")
    result = await run_recovery_workflow(normalized)
    return {
        "status": "processed",
        "provider": "stripe",
        "case_id": result.get("case_id"),
        "final_status": result.get("final_status"),
        "recovered_amount": result.get("recovered_amount")
    }

@router.post("/batch-upload")
async def batch_upload(file: UploadFile = File(...), async_mode: bool = Query(False)):
    """
    4.1.2 Batch CSV Loader:
    Accepts CSV of synthetic transactions, normalizes each row, and processes batch events.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")
        
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    
    processed_cases = []
    for row in reader:
        normalized = EventNormalizer.normalize(row, source="batch_csv")
        
        if async_mode:
            await event_queue.enqueue(normalized)
            processed_cases.append({
                "event_id": normalized.get("event_id"),
                "status": "queued"
            })
        else:
            res = await run_recovery_workflow(normalized)
            processed_cases.append({
                "case_id": res.get("case_id"),
                "event_type": res.get("event_type"),
                "status": res.get("final_status"),
                "recovered_amount": res.get("recovered_amount")
            })

    return {
        "message": f"Successfully ingested {len(processed_cases)} events from CSV batch.",
        "async_mode": async_mode,
        "cases": processed_cases
    }

@router.get("/queue/status")
async def queue_status():
    """
    4.1.4 Event Queue Metrics & Health Check.
    """
    return event_queue.get_status()
