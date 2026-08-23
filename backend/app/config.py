import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "ReviveAI - Autonomous Revenue Recovery Agent"
    VERSION: str = "1.0.0"
    
    # LLM Keys & Endpoints
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
    
    # Storage
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "reviveai")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Compliance Defaults
    MAX_RETRY_ATTEMPTS: int = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    RETRY_COOLDOWN_MINUTES: int = int(os.getenv("RETRY_COOLDOWN_MINUTES", "30"))
    MESSAGE_COOLDOWN_HOURS: int = int(os.getenv("MESSAGE_COOLDOWN_HOURS", "24"))
    MAX_ESCALATION_TIER: int = int(os.getenv("MAX_ESCALATION_TIER", "3"))
    
    # App
    ENV: str = os.getenv("ENV", "development")
    API_KEY_SECRET: str = os.getenv("API_KEY_SECRET", "demo-secret-key")

settings = Settings()
