import os
import logging
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.config import settings

logger = logging.getLogger("reviveai.middleware.auth")

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    4.11.5 Auth Middleware:
    Simple API Key authentication for API protection during demo/production deployment.
    Bypasses authentication for health checks, webhooks, and docs.
    """
    def __init__(self, app, api_key: str = "reviveai_demo_secret_key_2026"):
        super().__init__(app)
        self.api_key = os.getenv("REVIVEAI_API_KEY", api_key)
        self.unprotected_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/events/webhook",
            "/events/stream"
        ]

    async def dispatch(self, request: Request, call_next):
        # Allow OPTIONS request for CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow unprotected endpoints
        path = request.url.path
        if any(path.startswith(p) for p in self.unprotected_paths):
            return await call_next(request)

        # Check API key header if provided
        provided_key = request.headers.get("X-API-Key")
        if provided_key and provided_key != self.api_key:
            logger.warning(f"Unauthorized access attempt to {path}")
            raise HTTPException(status_code=401, detail="Invalid API Key credentials")

        return await call_next(request)
