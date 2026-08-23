from typing import Dict, Any, List
from backend.app.rag.embeddings import rag_store

async def retrieve_similar_cases(event_type: str, root_cause: str, amount: float) -> List[Dict[str, Any]]:
    query_text = f"{event_type} caused by {root_cause}, amount ~{amount}"
    return rag_store.query_similar_cases(query_text=query_text, top_k=3)

async def retrieve_relevant_policies(topic: str) -> List[Dict[str, Any]]:
    return rag_store.query_policy(query_text=topic, top_k=2)
