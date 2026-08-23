import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query
from backend.app.rag.embeddings import rag_store

logger = logging.getLogger("reviveai.routers.rag")
router = APIRouter(prefix="/rag", tags=["RAG Knowledge Module"])

@router.get("/query")
async def query_rag_knowledge(
    text: str = Query(..., description="Query text to search vector store"),
    collection: str = Query("cases", description="Collection type: 'cases' or 'policy'"),
    top_k: int = Query(3, description="Number of top matches to return")
):
    """
    4.9.4 Retriever Interface REST API:
    Queries ChromaDB vector stores (resolved_cases or policy_kb) for contextual grounding.
    """
    if collection.lower() == "policy":
        results = rag_store.query_policy(query_text=text, top_k=top_k)
    else:
        results = rag_store.query_similar_cases(query_text=text, top_k=top_k)

    return {
        "query": text,
        "collection": collection,
        "results": results,
        "count": len(results),
        "store_type": "memory_fallback" if rag_store.use_fallback else "chromadb"
    }
