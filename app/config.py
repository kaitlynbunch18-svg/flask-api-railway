import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
    DATABASE_URL = os.getenv("DATABASE_URL")  # eg: postgres://...
    IDP_TABLE_TTL = int(os.getenv("IDP_TABLE_TTL_SEC", 60 * 60 * 24 * 7))  # 7 days
    MAX_PAYLOAD_BYTES = int(os.getenv("MAX_PAYLOAD_BYTES", 1024*1024*2))
    WORKFLOW_AUTH_TOKEN = os.getenv("WORKFLOW_AUTH_TOKEN", "workflow-secret")
    # API keys for downstream calls (optional)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
