from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid

class Lead(BaseModel):
    lead_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    platform: Literal["Reddit", "X", "LinkedIn"]
    author_handle: str
    author_profile_url: Optional[str] = None
    post_url: str
    post_excerpt: str
    
    # AI Analysis Results
    has_pain: bool = False
    pain_category: Optional[str] = None
    pain_summary: Optional[str] = None
    urgency_score: int = 0
    suggested_outreach_message: Optional[str] = None
    
    lead_status: str = "New"
    notes: Optional[str] = ""
    last_updated_utc: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
