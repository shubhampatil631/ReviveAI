import csv
import io
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.app.db.mongo import get_db

logger = logging.getLogger("reviveai.routers.batch")
router = APIRouter(prefix="/batch", tags=["Batch & Reporting"])

@router.get("/report")
async def get_summary_report():
    """
    Returns aggregate executive dashboard metrics: ₹ at risk, ₹ recovered, recovery rate %, status breakdown.
    """
    db = get_db()
    col = db.get_collection("recovery_cases")
    cursor = col.find({})
    cases = await cursor.to_list()

    total_cases = len(cases)
    total_at_risk = sum(c.get("amount", 0.0) for c in cases)
    total_recovered = sum(c.get("recovered_amount", 0.0) for c in cases if c.get("status") == "recovered")
    recovery_rate = round((total_recovered / total_at_risk * 100), 1) if total_at_risk > 0 else 0.0

    status_counts = {}
    action_counts = {}
    for c in cases:
        st = c.get("status", "unknown")
        act = c.get("selected_action", "none")
        status_counts[st] = status_counts.get(st, 0) + 1
        action_counts[act] = action_counts.get(act, 0) + 1

    return {
        "metrics": {
            "total_cases": total_cases,
            "total_at_risk_inr": total_at_risk,
            "total_recovered_inr": total_recovered,
            "recovery_rate_pct": recovery_rate,
            "blocked_by_compliance": status_counts.get("blocked", 0),
            "escalated_count": status_counts.get("escalated", 0)
        },
        "status_breakdown": status_counts,
        "action_breakdown": action_counts
    }

@router.get("/report/export")
async def export_audit_csv():
    """
    Streams a full CSV audit export of all cases and compliance records.
    """
    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    cursor = cases_col.find({}).sort("created_at", -1)
    cases = await cursor.to_list()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Case ID", "Transaction ID", "Customer ID", "Customer Name", 
        "Event Type", "Amount (INR)", "Risk Score", "Root Cause", 
        "Selected Action", "Attempts", "Status", "Recovered Amount (INR)"
    ])

    for c in cases:
        writer.writerow([
            c.get("case_id", ""),
            c.get("transaction_id", ""),
            c.get("customer_id", ""),
            c.get("customer_name", ""),
            c.get("event_type", ""),
            c.get("amount", 0.0),
            c.get("risk_score", 0.0),
            c.get("root_cause", ""),
            c.get("selected_action", ""),
            c.get("attempts", 0),
            c.get("status", ""),
            c.get("recovered_amount", 0.0)
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reviveai_audit_export.csv"}
    )
