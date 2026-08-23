import os
import json
import asyncio
import logging
from dotenv import load_dotenv

load_dotenv()

from backend.app.db.mongo import db_manager, get_db
from backend.app.rag.embeddings import rag_store
from scripts.seed_chroma import seed_chroma

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rebuild_embeddings")

async def rebuild_embeddings():
    logger.info("Wiping and rebuilding RAG vector store embeddings...")
    rag_store.initialize()
    if rag_store.chroma_client and not rag_store.use_fallback:
        try:
            rag_store.chroma_client.delete_collection("resolved_cases")
            rag_store.chroma_client.delete_collection("policy_kb")
            logger.info("ChromaDB collections reset.")
        except Exception as e:
            logger.warning(f"Collection reset note: {e}")
            
    # Seed base policies and seed cases
    seed_chroma()

    # Sync from MongoDB recovery_cases collection
    await db_manager.connect()
    db = get_db()
    cases_col = db.get_collection("recovery_cases")
    cases = await cases_col.find({"status": {"$in": ["recovered", "closed", "escalated"]}}).to_list()

    logger.info(f"Re-indexing {len(cases)} resolved/escalated cases from MongoDB into ChromaDB...")
    for case in cases:
        summary_text = (
            f"{case.get('event_type')} caused by {case.get('root_cause', 'unknown')}, "
            f"amount {case.get('amount')}, action taken {case.get('action_taken', 'RETRY_PAYMENT')}, "
            f"outcome {case.get('status')}"
        )
        rag_store.add_resolved_case({
            "case_id": case.get("case_id"),
            "event_type": case.get("event_type"),
            "root_cause": case.get("root_cause", "unknown"),
            "amount": case.get("amount"),
            "action": case.get("action_taken", "RETRY_PAYMENT"),
            "outcome": case.get("status"),
            "summary": summary_text
        })

    logger.info("RAG embeddings rebuild complete.")

if __name__ == "__main__":
    asyncio.run(rebuild_embeddings())
