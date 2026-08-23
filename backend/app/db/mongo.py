import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.app.config import settings

logger = logging.getLogger("reviveai.db")

class InMemoryCollection:
    PRIMARY_KEYS = {
        "promises": "promise_id",
        "audit_logs": "log_id",
        "compliance_decisions": "decision_id",
        "recovery_cases": "case_id",
        "transactions": "transaction_id",
        "customers": "customer_id",
        "events": "event_id"
    }

    def __init__(self, name: str):
        self.name = name
        self.documents: Dict[str, Dict[str, Any]] = {}
        
    def _get_key(self, doc: Dict[str, Any]) -> str:
        pk = self.PRIMARY_KEYS.get(self.name)
        if pk and pk in doc:
            return str(doc[pk])
        if "_id" in doc:
            return str(doc["_id"])
        for k in ["promise_id", "log_id", "decision_id", "case_id", "transaction_id", "customer_id", "event_id"]:
            if k in doc:
                return str(doc[k])
        return str(len(self.documents) + 1)

    async def create_index(self, keys, **kwargs):
        """Mock create_index stub for in-memory collections."""
        return str(keys)

    async def insert_one(self, doc: Dict[str, Any]):
        key = self._get_key(doc)
        doc["_id"] = key
        self.documents[key] = doc
        return type('InsertResult', (), {'inserted_id': key})()

    async def update_one(self, filter_query: Dict[str, Any], update_query: Dict[str, Any]):
        doc = await self.find_one(filter_query)
        if not doc:
            return type('UpdateResult', (), {'modified_count': 0})()
        
        if "$set" in update_query:
            for k, v in update_query["$set"].items():
                doc[k] = v
        if "$inc" in update_query:
            for k, v in update_query["$inc"].items():
                doc[k] = doc.get(k, 0) + v
        return type('UpdateResult', (), {'modified_count': 1})()

    def _get_nested_val(self, doc: Dict[str, Any], key: str) -> Any:
        if key in doc:
            return doc[key]
        if "." in key:
            parts = key.split(".")
            curr = doc
            for p in parts:
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    return None
            return curr
        return doc.get(key)

    def _match_doc(self, doc: Dict[str, Any], filter_query: Dict[str, Any]) -> bool:
        for k, v in filter_query.items():
            doc_val = self._get_nested_val(doc, k)
            if isinstance(v, dict):
                if "$in" in v and doc_val not in v["$in"]:
                    return False
                if "$nin" in v and doc_val in v["$nin"]:
                    return False
                if "$ne" in v and doc_val == v["$ne"]:
                    return False
            elif doc_val != v:
                return False
        return True

    async def find_one(self, filter_query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for doc in self.documents.values():
            if self._match_doc(doc, filter_query):
                return doc
        return None

    def find(self, filter_query: Dict[str, Any] = None):
        filter_query = filter_query or {}
        matched = []
        for doc in self.documents.values():
            if self._match_doc(doc, filter_query):
                matched.append(doc)
        
        class Cursor:
            def __init__(self, items):
                self.items = items
            def sort(self, key, direction=-1):
                reverse = (direction == -1)
                self.items.sort(key=lambda x: str(x.get(key, "")), reverse=reverse)
                return self
            def limit(self, n):
                self.items = self.items[:n]
                return self
            async def to_list(self, length=None):
                return self.items[:length] if length else self.items
            def __aiter__(self):
                self._iter = iter(self.items)
                return self
            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration
                    
        return Cursor(matched)

    async def count_documents(self, filter_query: Dict[str, Any] = None) -> int:
        filter_query = filter_query or {}
        cursor = self.find(filter_query)
        res = await cursor.to_list()
        return len(res)


class Database:
    def __init__(self):
        self.is_connected = False
        self.client = None
        self.db = None
        self.use_mock = False
        self._mock_cols: Dict[str, InMemoryCollection] = {}

    def get_collection(self, name: str):
        if self.use_mock or not self.is_connected:
            if name not in self._mock_cols:
                self._mock_cols[name] = InMemoryCollection(name)
            return self._mock_cols[name]
        return self.db[name]

    async def setup_indexes(self):
        """Setup 5A.2 MongoDB Collection Indexes."""
        if not self.is_connected or self.db is None:
            return
        try:
            await self.db["customers"].create_index("customer_id", unique=True)
            await self.db["customers"].create_index("opt_out")
            await self.db["transactions"].create_index("transaction_id", unique=True)
            await self.db["transactions"].create_index("customer_id")
            await self.db["transactions"].create_index("status")
            await self.db["recovery_cases"].create_index("case_id", unique=True)
            await self.db["recovery_cases"].create_index("status")
            await self.db["recovery_cases"].create_index("event_type")
            await self.db["recovery_cases"].create_index([("created_at", -1)])
            await self.db["promises"].create_index("case_id")
            await self.db["promises"].create_index([("due_date", 1), ("status", 1)])
            await self.db["audit_logs"].create_index([("case_id", 1), ("timestamp", 1)])
            await self.db["compliance_decisions"].create_index("case_id")
            logger.info("MongoDB collection indexes initialized successfully.")
        except Exception as idx_err:
            logger.warning(f"Collection index initialization warning: {idx_err}")

    async def connect(self):
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=15000,
                retryWrites=True
            )
            await self.client[settings.DB_NAME].command('ping')
            self.db = self.client[settings.DB_NAME]
            self.is_connected = True
            self.use_mock = False
            logger.info("Successfully connected to MongoDB Atlas.")
            await self.setup_indexes()
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}. Falling back to in-memory database mock.")
            self.use_mock = True

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB connection closed.")

db_manager = Database()

def get_db():
    return db_manager
