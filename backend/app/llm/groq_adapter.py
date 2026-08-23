import httpx
import logging
from backend.app.config import settings

logger = logging.getLogger("reviveai.llm.groq")

class GroqAdapter:
    """
    4.12.2 Groq Adapter:
    Low-latency model adapter for fast classification tasks.
    Supports candidate model failover across Groq model tiers.
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.candidate_models = [
            "groq/compound",
            "groq/compound-mini",
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b"
        ]

    async def classify(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            return ""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for model in self.candidate_models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(self.endpoint, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "")
                    else:
                        logger.warning(f"Groq model {model} status {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                logger.warning(f"Groq model {model} exception: {e}")

        return ""

groq_adapter = GroqAdapter()
