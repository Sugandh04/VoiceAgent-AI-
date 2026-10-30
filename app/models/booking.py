from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class DemoBooking(Base):
    __tablename__ = "demo_bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    call_sid = Column(String(100), nullable=True)
    scheduled_time = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    meeting_link = Column(String(255), nullable=True)
    status = Column(String(50), default="CONFIRMED")
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="bookings")
