import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure root workspace is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.config import settings
from backend.app.db.mongo import db_manager
from backend.app.rag.embeddings import rag_store
from backend.app.ingestion.queue import event_queue
from backend.app.middleware.auth import APIKeyAuthMiddleware
from backend.app.routers import events, cases, batch, compliance, promises, rag, stream
from scripts.seed_chroma import seed_chroma
from scripts.seed_mongo import seed_mongo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reviveai.main")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ReviveAI system services...")
    await db_manager.connect()
    rag_store.initialize()
    seed_chroma()
    await seed_mongo()
    await event_queue.start_worker()
    logger.info("ReviveAI system ready for traffic.")
    yield
    logger.info("Shutting down ReviveAI system services...")
    await event_queue.stop_worker()
    await db_manager.disconnect()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Revenue Recovery Agent with MCP Compliance Guardrails",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Middleware (4.11.5)
app.add_middleware(APIKeyAuthMiddleware)

# Include Routers with /api prefix for frontend compatibility + root prefix fallback
for r in [events.router, cases.router, batch.router, compliance.router, promises.router, rag.router, stream.router]:
    app.include_router(r, prefix="/api")
    app.include_router(r)

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "connected" if db_manager.is_connected else "mock_in_memory",
        "rag_store": "chroma" if not rag_store.use_fallback else "memory_fallback",
        "event_queue": event_queue.get_status()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
