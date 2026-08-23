import os
import json
import logging
from typing import List, Dict, Any
from backend.app.config import settings

logger = logging.getLogger("reviveai.rag")

class RAGVectorStore:
    def __init__(self):
        self.use_fallback = False
        self.chroma_client = None
        self.resolved_collection = None
        self.policy_collection = None
        self._fallback_resolved: List[Dict[str, Any]] = []
        self._fallback_policy: List[Dict[str, Any]] = []

    def initialize(self):
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            
            embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=settings.EMBEDDING_MODEL
            )
            
            self.resolved_collection = self.chroma_client.get_or_create_collection(
                name="resolved_cases",
                embedding_function=embed_fn
            )
            self.policy_collection = self.chroma_client.get_or_create_collection(
                name="policy_kb",
                embedding_function=embed_fn
            )
            logger.info("ChromaDB initialized successfully.")
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed ({e}). Falling back to memory RAG store.")
            self.use_fallback = True

    def add_resolved_case(self, case_summary: Dict[str, Any]):
        summary_text = case_summary.get("summary") or f"{case_summary.get('event_type')} caused by {case_summary.get('root_cause')}, amount {case_summary.get('amount')}, action taken {case_summary.get('action')}, outcome {case_summary.get('outcome')}"
        case_id = case_summary.get("case_id", f"CASE_{len(self._fallback_resolved)+1}")
        
        if self.use_fallback or not self.resolved_collection:
            self._fallback_resolved.append({
                "id": case_id,
                "text": summary_text,
                "metadata": case_summary
            })
        else:
            try:
                self.resolved_collection.upsert(
                    ids=[case_id],
                    documents=[summary_text],
                    metadatas=[{
                        "event_type": str(case_summary.get("event_type", "")),
                        "root_cause": str(case_summary.get("root_cause", "")),
                        "action": str(case_summary.get("action", "")),
                        "outcome": str(case_summary.get("outcome", ""))
                    }]
                )
            except Exception as e:
                logger.error(f"Error upserting into ChromaDB resolved_cases: {e}")

    def add_policy_chunk(self, policy_data: Dict[str, Any]):
        policy_id = policy_data.get("id", f"POL_{len(self._fallback_policy)+1}")
        text = policy_data.get("text", "")
        
        if self.use_fallback or not self.policy_collection:
            self._fallback_policy.append({
                "id": policy_id,
                "text": text,
                "metadata": policy_data
            })
        else:
            try:
                self.policy_collection.upsert(
                    ids=[policy_id],
                    documents=[text],
                    metadatas=[{
                        "policy_type": str(policy_data.get("policy_type", "")),
                        "section": str(policy_data.get("section", ""))
                    }]
                )
            except Exception as e:
                logger.error(f"Error upserting into ChromaDB policy_kb: {e}")

    def query_similar_cases(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if self.use_fallback or not self.resolved_collection:
            # Word match similarity fallback
            query_words = set(query_text.lower().split())
            scored = []
            for item in self._fallback_resolved:
                text_words = set(item["text"].lower().split())
                score = len(query_words.intersection(text_words))
                scored.append((score, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [item for _, item in scored[:top_k]]
        else:
            try:
                results = self.resolved_collection.query(
                    query_texts=[query_text],
                    n_results=top_k
                )
                output = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else [{}]*len(docs)
                    for doc, meta in zip(docs, metas):
                        output.append({"text": doc, "metadata": meta})
                return output
            except Exception as e:
                logger.error(f"ChromaDB query error: {e}")
                return []

    def query_policy(self, query_text: str, top_k: int = 2) -> List[Dict[str, Any]]:
        if self.use_fallback or not self.policy_collection:
            query_words = set(query_text.lower().split())
            scored = []
            for item in self._fallback_policy:
                text_words = set(item["text"].lower().split())
                score = len(query_words.intersection(text_words))
                scored.append((score, item))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [item for _, item in scored[:top_k]]
        else:
            try:
                results = self.policy_collection.query(
                    query_texts=[query_text],
                    n_results=top_k
                )
                output = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else [{}]*len(docs)
                    for doc, meta in zip(docs, metas):
                        output.append({"text": doc, "metadata": meta})
                return output
            except Exception as e:
                logger.error(f"ChromaDB policy query error: {e}")
                return []

rag_store = RAGVectorStore()
