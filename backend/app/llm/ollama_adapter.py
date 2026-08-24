import httpx
import logging
from backend.app.config import settings

logger = logging.getLogger("reviveai.llm.ollama")

class OllamaAdapter:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.candidate_models = [
            settings.OLLAMA_MODEL,
            "qwen2.5:1.5b",
            "llama3.2:1b",
            "phi3:mini"
        ]
        self.endpoint = f"{self.host.rstrip('/')}/api/chat"

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Deduplicate models preserving order
        unique_models = []
        for m in self.candidate_models:
            if m and m not in unique_models:
                unique_models.append(m)

        for model in unique_models:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(self.endpoint, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        msg = data.get("message", {})
                        content = msg.get("content", "")
                        if content:
                            return content
                    else:
                        logger.warning(f"Ollama model {model} API status: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Ollama model {model} exception: {e}")
        return ""

ollama_adapter = OllamaAdapter()
