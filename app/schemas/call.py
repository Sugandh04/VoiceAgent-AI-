from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class OutboundCallRequest(BaseModel):
    to: Optional[str] = Field(default="Browser User", description="Phone number or Browser user")
    customField: Optional[str] = Field(default="web-voice-agent", description="Metadata tag")

class OutboundCallResponse(BaseModel):
    callSid: str
    wsUrl: str
    status: str

class TurnSchema(BaseModel):
    speaker: str
    text: str
    timestamp: datetime

    class Config:
        from_attributes = True

class CallDetailSchema(BaseModel):
    call_sid: str
    from_number: Optional[str]
    to_number: Optional[str]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: int
    turns: List[TurnSchema] = []

    class Config:
        from_attributes = True
