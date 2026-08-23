import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.app.db.mongo import get_db

logger = logging.getLogger("reviveai.routers.stream")
router = APIRouter(prefix="/events", tags=["Streaming Live Event Channel"])

@router.get("/stream")
async def stream_live_case_updates() -> StreamingResponse:
    """
    4.11.6 Native FastAPI Server-Sent Events (SSE) Live-Stream Channel:
    Streams live case state updates and multi-agent workflow events to the dashboard.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        db = get_db()
        cases_col = db.get_collection("recovery_cases")
        last_count = 0
        
        while True:
            try:
                cursor = cases_col.find({})
                cases = await cursor.to_list()
                current_count = len(cases)
                
                # Fetch recent cases
                recent_cases = cases[-5:] if cases else []
                data_payload = {
                    "event_type": "dashboard_sync",
                    "total_cases": current_count,
                    "new_cases_count": max(0, current_count - last_count),
                    "latest_cases": recent_cases
                }
                last_count = current_count

                # SSE Event Format
                yield f"event: update\ndata: {json.dumps(data_payload, default=str)}\n\n"
            except Exception as e:
                logger.error(f"Error in SSE event stream generator: {e}")
            
            await asyncio.sleep(3.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
