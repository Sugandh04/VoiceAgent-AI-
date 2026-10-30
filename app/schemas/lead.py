from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LeadCreateSchema(BaseModel):
    phone_number: str
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None

class LeadResponseSchema(BaseModel):
    id: int
    phone_number: str
    name: Optional[str]
    company: Optional[str]
    email: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class DemoBookingCreateSchema(BaseModel):
    lead_id: Optional[int] = None
    call_sid: Optional[str] = None
    scheduled_time: datetime
    notes: Optional[str] = None

class DemoBookingResponseSchema(BaseModel):
    id: int
    lead_id: Optional[int]
    call_sid: Optional[str]
    scheduled_time: datetime
    status: str
    notes: Optional[str]
    lead: Optional[LeadResponseSchema] = None

    class Config:
        from_attributes = True
