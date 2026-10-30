import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.config import settings
from app.models.call import Call, CallStatus
from app.models.user import User
from app.schemas.call import OutboundCallRequest, OutboundCallResponse, CallDetailSchema
from app.services.exotel_service import exotel_service
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/api/calls", tags=["Calls"])

@router.post("/outbound", response_model=OutboundCallResponse)
async def initiate_call(
    req: OutboundCallRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Starts a voice call session.
    If target looks like an E.164 phone number and Exotel credentials exist, triggers an outbound PSTN call.
    Otherwise, returns the WebSocket URL for browser mic calling.
    """
    call_sid = f"web_call_{uuid.uuid4().hex[:8]}"
    user_id = current_user.id if current_user else None
    
    ws_base = getattr(settings, "PUBLIC_WS_URL", None) or f"ws://{settings.HOST}:{settings.PORT}/ws/voice-bot"
    ws_url = f"{ws_base}?callSid={call_sid}"

    new_call = Call(
        user_id=user_id,
        call_sid=call_sid,
        from_number=req.to,
        caller_id="VoiceAgent-AI",
        status=CallStatus.QUEUED,
        start_time=datetime.utcnow(),
        custom_field=req.customField
    )
    db.add(new_call)
    await db.commit()
    await db.refresh(new_call)

    # Optional: Trigger Exotel PSTN dial if phone number format
    if req.to and req.to.startswith("+91") and settings.EXOTEL_ACCOUNT_SID:
        await exotel_service.initiate_outbound_call(destination_number=req.to, custom_field=call_sid)

    return OutboundCallResponse(
        callSid=call_sid,
        wsUrl=ws_url,
        status=new_call.status.value
    )

@router.get("", response_model=List[CallDetailSchema])
async def list_calls(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List recent call sessions and their turn-by-turn history for current user."""
    if not current_user:
        return []
    result = await db.execute(
        select(Call)
        .options(selectinload(Call.turns))
        .where(Call.user_id == current_user.id)
        .order_by(Call.start_time.desc())
        .limit(50)
    )
    return result.scalars().all()
