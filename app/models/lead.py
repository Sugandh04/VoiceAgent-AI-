from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base

class LeadStatus(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    INTERESTED = "INTERESTED"
    DEMO_SCHEDULED = "DEMO_SCHEDULED"
    CALLBACK_REQUESTED = "CALLBACK_REQUESTED"
    NOT_INTERESTED = "NOT_INTERESTED"
    CONVERTED = "CONVERTED"

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    phone_number = Column(String(50), index=True, nullable=False)
    name = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    whatsapp_number = Column(String(50), nullable=True)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    callbacks = relationship("CallbackRequest", back_populates="lead", cascade="all, delete-orphan")
    bookings = relationship("DemoBooking", back_populates="lead", cascade="all, delete-orphan")

class CallbackRequest(Base):
    __tablename__ = "callback_requests"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    callback_time = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(String(50), default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="callbacks")
