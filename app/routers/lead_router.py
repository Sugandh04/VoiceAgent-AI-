from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_
from typing import List, Optional

from app.database import get_db
from app.models.lead import Lead, LeadStatus
from app.models.booking import DemoBooking
from app.models.call import Call, CallStatus
from app.models.user import User
from app.schemas.lead import LeadCreateSchema, LeadResponseSchema
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/api/contacts", tags=["Contacts / Leads"])

@router.get("", response_model=List[LeadResponseSchema])
async def list_contacts(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return []
    
    stmt = select(Lead).where(Lead.user_id == current_user.id).order_by(Lead.created_at.desc())
    if status and status != "ALL":
        stmt = stmt.where(Lead.status == status)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where((Lead.name.ilike(term)) | (Lead.phone_number.ilike(term)) | (Lead.company.ilike(term)))
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("", response_model=LeadResponseSchema)
async def create_contact(
    payload: LeadCreateSchema,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    clean_phone = payload.phone_number.strip().replace(" ", "").replace("-", "")
    user_id = current_user.id

    # Check existing for this specific user
    stmt = select(Lead).where(Lead.phone_number == clean_phone, Lead.user_id == user_id)
    existing = await db.execute(stmt)
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="A contact with this phone number already exists in your account.")

    lead = Lead(
        user_id=user_id,
        phone_number=clean_phone,
        name=payload.name,
        company=payload.company,
        email=payload.email,
        notes=payload.notes,
        status=LeadStatus.NEW
    )
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    stmt = select(Lead).where(Lead.id == contact_id, Lead.user_id == current_user.id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Contact not found or unauthorized")
    await db.delete(lead)
    await db.commit()
    return {"message": "Contact deleted successfully", "id": contact_id}

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns real-time analytics for Dashboard KPIs strictly scoped to current user."""
    if not current_user:
        return {
            "total_leads": 0,
            "demos_booked": 0,
            "total_calls": 0,
            "calls_connected": 0,
            "calls_not_picked": 0,
            "conversion_rate": 0.0
        }

    user_id = current_user.id

    lead_stmt = select(func.count(Lead.id)).where(Lead.user_id == user_id)
    booking_stmt = select(func.count(DemoBooking.id)).where(DemoBooking.user_id == user_id)
    call_stmt = select(func.count(Call.id)).where(Call.user_id == user_id)
    not_picked_stmt = select(func.count(Call.id)).where(Call.user_id == user_id, Call.status.in_([CallStatus.NO_ANSWER, CallStatus.BUSY, CallStatus.FAILED]))
    connected_stmt = select(func.count(Call.id)).where(Call.user_id == user_id, Call.status == CallStatus.COMPLETED)

    total_leads = (await db.execute(lead_stmt)).scalar() or 0
    demos_booked = (await db.execute(booking_stmt)).scalar() or 0
    total_calls = (await db.execute(call_stmt)).scalar() or 0
    calls_not_picked = (await db.execute(not_picked_stmt)).scalar() or 0
    calls_connected = (await db.execute(connected_stmt)).scalar() or 0

    conversion_rate = round((demos_booked / total_leads * 100), 1) if total_leads > 0 else 0.0

    return {
        "total_leads": total_leads,
        "demos_booked": demos_booked,
        "total_calls": total_calls,
        "calls_connected": calls_connected,
        "calls_not_picked": calls_not_picked,
        "conversion_rate": conversion_rate
    }
