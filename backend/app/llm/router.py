import logging
from typing import Optional
from backend.app.llm.groq_adapter import groq_adapter
from backend.app.llm.gemini_adapter import gemini_adapter
from backend.app.llm.ollama_adapter import ollama_adapter

logger = logging.getLogger("reviveai.llm.router")

class LLMRouter:
    async def route_call(self, task_type: str, prompt: str, system_prompt: str = "") -> Optional[str]:
        """
        Routes call based on task shape with 3-tier hybrid failover chain:
        - classification: Groq (Llama-70b) -> Gemini Pro -> Ollama (Small model)
        - reasoning / generation: Gemini Pro -> Groq -> Ollama (Small model)
        """
        response = ""
        if task_type == "classification":
            logger.info("[LLM Router] Attempting classification with Groq...")
            response = await groq_adapter.classify(prompt, system_prompt)
            
            if not response:
                logger.info("[LLM Router] Groq unavailable. Failing over to Gemini Pro...")
                response = await gemini_adapter.generate(prompt, system_prompt)
                
            if not response:
                logger.info("[LLM Router] Gemini unavailable. Failing over to Ollama small model...")
                response = await ollama_adapter.generate(prompt, system_prompt)
        else:
            logger.info("[LLM Router] Attempting reasoning/generation with Gemini Pro...")
            response = await gemini_adapter.generate(prompt, system_prompt)
            
            if not response:
                logger.info("[LLM Router] Gemini unavailable. Failing over to Groq...")
                response = await groq_adapter.classify(prompt, system_prompt)
                
            if not response:
                logger.info("[LLM Router] Groq unavailable. Failing over to Ollama small model...")
                response = await ollama_adapter.generate(prompt, system_prompt)

        return response if response else None

llm_router = LLMRouter()
