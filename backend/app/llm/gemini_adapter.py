import httpx
import logging
from backend.app.config import settings

logger = logging.getLogger("reviveai.llm.gemini")

class GeminiAdapter:
    """
    4.12.3 Gemini Adapter:
    Nuanced reasoning adapter for ambiguous cases & personalized message copy generation (incl. Hinglish variant).
    Supports candidate model failover across Gemini model tiers.
    """
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.candidate_models = [
            "gemini-3.5-flash",
            "gemini-flash-latest",
            "gemini-pro-latest",
            "gemini-3.6-flash"
        ]

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key:
            return ""
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}"}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {"contents": contents}

        for model in self.candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    else:
                        logger.warning(f"Gemini model {model} status {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                logger.warning(f"Gemini model {model} exception: {e}")

        return ""

gemini_adapter = GeminiAdapter()
