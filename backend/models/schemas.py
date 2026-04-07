from pydantic import BaseModel, Field
from typing import List, Optional, Any
import json

# 1. Used for Gemini to understand how to parse user intent
class IntentSchema(BaseModel):
    intent: str = Field(
        ..., 
        description="Must be exactly one of: schedule, reschedule, transcribe, summarise, cancel, query"
    )
    attendees: List[str] = Field(default_factory=list, description="List of attendee email addresses")
    duration_minutes: int = Field(default=60, description="Duration of the meeting in minutes")
    preferred_time: str = Field(default="next available", description="Preferred time in natural language")
    meeting_title: Optional[str] = Field(default=None, description="Title of the meeting if available")
    notes: Optional[str] = Field(default="", description="Any extra context or notes for the meeting")

# 2. Used for API responses (The 'Summaries' and 'Calendar' tabs)
class MeetingResponse(BaseModel):
    id: int
    title: str
    status: str
    start_time: Optional[Any] = None
    
    class Config:
        from_attributes = True