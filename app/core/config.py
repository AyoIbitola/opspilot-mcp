from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError

class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str

    # Reddit (Read-only mode - no credentials needed)
    REDDIT_CLIENT_ID: Optional[str] = None  # Not needed for read-only access
    REDDIT_CLIENT_SECRET: Optional[str] = None  # Not needed for read-only access
    REDDIT_USER_AGENT: str = "OpsPilotLeadMCP/1.0 (Read-only)"

    # LinkedIn (Optional)
    LINKEDIN_USERNAME: Optional[str] = None
    LINKEDIN_PASSWORD: Optional[str] = None
    
    # X (Twitter) - Optional for Scraper
    TWITTER_USERNAME: Optional[str] = None
    TWITTER_EMAIL: Optional[str] = None
    TWITTER_PASSWORD: Optional[str] = None
    
    # Google Sheets
    GOOGLE_SERVICE_ACCOUNT_JSON: str
    SPREADSHEET_NAME: str = "OpsPilot Leads"

    # Target Configuration
    SUBREDDITS: List[str] = [
        "askmanagers",
        "projectmanagement",
        "startups",
        "Entrepreneur"
    ]
    
    KEYWORDS: List[str] = [
        "reporting", "visibility", "manage", "team", "growth",
        "excel", "sheet", "manual", "chasing", "automation",
        "ops", "operations", "dashboard"
    ]

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

try:
    settings = Settings()
except ValidationError as e:
    # We might want to handle this more gracefully or just fail startup
    print(f"Configuration Error: {e}")
    # For now, let it crash if critical env vars are missing, except optional ones
    raise
