from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base

class CallStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RINGING = "RINGING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NO_ANSWER = "NO_ANSWER"
    BUSY = "BUSY"

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    call_sid = Column(String(100), unique=True, index=True, nullable=False)
    from_number = Column(String(50), nullable=True)
    to_number = Column(String(50), nullable=True)
    caller_id = Column(String(50), nullable=True)
    status = Column(SQLEnum(CallStatus), default=CallStatus.QUEUED, nullable=False)
    direction = Column(String(20), default="OUTBOUND")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    recording_url = Column(String(500), nullable=True)
    custom_field = Column(String(255), nullable=True)
    
    turns = relationship("ConversationTurn", back_populates="call", cascade="all, delete-orphan")

class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id = Column(Integer, primary_key=True, index=True)
    call_sid = Column(String(100), ForeignKey("calls.call_sid"), nullable=False, index=True)
    speaker = Column(String(20), nullable=False) # "USER" or "BOT"
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    call = relationship("Call", back_populates="turns")
