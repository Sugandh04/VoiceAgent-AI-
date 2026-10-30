from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base

class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

class CampaignLeadStatus(str, enum.Enum):
    PENDING = "PENDING"
    DIALING = "DIALING"
    ANSWERED = "ANSWERED"
    BUSY = "BUSY"
    NO_ANSWER = "NO_ANSWER"
    FAILED = "FAILED"
    DEMO_BOOKED = "DEMO_BOOKED"

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    status = Column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    concurrency = Column(Integer, default=5)
    max_retries = Column(Integer, default=3)
    total_leads = Column(Integer, default=0)
    called_leads = Column(Integer, default=0)
    booked_demos = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    leads = relationship("CampaignLead", back_populates="campaign", cascade="all, delete-orphan")

class CampaignLead(Base):
    __tablename__ = "campaign_leads"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    phone_number = Column(String(50), nullable=False, index=True)
    company = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    status = Column(SQLEnum(CampaignLeadStatus), default=CampaignLeadStatus.PENDING, nullable=False)
    attempts = Column(Integer, default=0)
    last_called_at = Column(DateTime, nullable=True)
    call_sid = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaign = relationship("Campaign", back_populates="leads")
