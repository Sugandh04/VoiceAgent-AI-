import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class OutboundCallRequest(BaseModel):
    to: Optional[str] = Field(default="Browser User", description="Phone number or Browser user")
    customField: Optional[str] = Field(default="web-voice-agent", description="Metadata tag")

    @field_validator("to")
    @classmethod
    def validate_destination(cls, v: Optional[str]) -> Optional[str]:
        if not v or v.strip().lower() in ("browser user", "web", "browser"):
            return "Browser User"
        clean = re.sub(r"[\s\-()]", "", v.strip())
        # Check if caller passed an Indian mobile number
        if clean.startswith("+91") and re.match(r"^\+91[6-9]\d{9}$", clean):
            return clean
        if clean.startswith("0") and len(clean) == 11 and re.match(r"^0[6-9]\d{9}$", clean):
            return f"+91{clean[1:]}"
        if len(clean) == 10 and re.match(r"^[6-9]\d{9}$", clean):
            return f"+91{clean}"
        # If it starts with '+' but is not a valid Indian number, check international E.164
        if clean.startswith("+"):
            if not re.match(r"^\+[1-9]\d{6,14}$", clean):
                raise ValueError("Invalid international phone number format (must be E.164)")
            return clean
        # If alphanumeric identifier (e.g. user handle / browser room), allow if safe
        if re.match(r"^[A-Za-z0-9_\-\. ]{2,50}$", v):
            return v.strip()
        raise ValueError("Destination must be a valid 10-digit mobile number (+91XXXXXXXXXX) or browser client identifier")

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
    summary: Optional[str] = None
    turns: List[TurnSchema] = []

    class Config:
        from_attributes = True
