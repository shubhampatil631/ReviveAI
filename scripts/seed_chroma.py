import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

from backend.app.rag.embeddings import rag_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_chroma")

def seed_chroma():
    """
    5A.8 Cold-Start Seeding Strategy:
    Idempotent loader checking each collection count before inserting, skipping if already seeded.
    """
    rag_store.initialize()
    
    base_dir = os.path.dirname(__file__)
    cases_json_path = os.path.join(base_dir, "..", "data", "seed_resolved_cases.json")
    policy_json_path = os.path.join(base_dir, "..", "data", "policy_kb.json")
    
    # Check if resolved_cases already populated
    cases_count = 0
    if rag_store.use_fallback or not rag_store.resolved_collection:
        cases_count = len(rag_store._fallback_resolved)
    else:
        try:
            cases_count = rag_store.resolved_collection.count()
        except Exception:
            cases_count = 0

    if cases_count == 0 and os.path.exists(cases_json_path):
        logger.info(f"Loading seed resolved cases from {cases_json_path}...")
        with open(cases_json_path, mode="r", encoding="utf-8") as f:
            cases_data = json.load(f)
            for item in cases_data:
                rag_store.add_resolved_case(item)
        logger.info("Successfully seeded resolved cases RAG store.")
    else:
        logger.info(f"RAG resolved_cases already has {cases_count} items. Skipping seed.")

    # Check if policy_kb already populated
    policy_count = 0
    if rag_store.use_fallback or not rag_store.policy_collection:
        policy_count = len(rag_store._fallback_policy)
    else:
        try:
            policy_count = rag_store.policy_collection.count()
        except Exception:
            policy_count = 0

    if policy_count == 0 and os.path.exists(policy_json_path):
        logger.info(f"Loading policy KB from {policy_json_path}...")
        with open(policy_json_path, mode="r", encoding="utf-8") as f:
            policy_data = json.load(f)
            for item in policy_data:
                rag_store.add_policy_chunk(item)
        logger.info("Successfully seeded policy KB RAG store.")
    else:
        logger.info(f"RAG policy_kb already has {policy_count} items. Skipping seed.")

if __name__ == "__main__":
    seed_chroma()
