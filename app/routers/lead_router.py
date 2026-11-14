import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, or_
from typing import List, Optional

from app.database import get_db
from app.models.lead import Lead, LeadStatus
from app.models.booking import DemoBooking
from app.models.call import Call, CallStatus
from app.models.user import User
from app.schemas.lead import LeadCreateSchema, LeadResponseSchema
from app.routers.auth_router import require_user
from app.cache import cache
from app.routers.ws_router import broadcast_event
from app.services.dashboard_service import compute_dashboard_stats

router = APIRouter(prefix="/api/contacts", tags=["Contacts / Leads"])

@router.get("", response_model=List[LeadResponseSchema])
async def list_contacts(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Lead)
        .where(Lead.user_id == current_user.id)
        .order_by(Lead.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
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
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
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

    # Invalidate dashboard cache
    await cache.delete(f"dashboard:stats:{user_id}")
    await broadcast_event("LEAD_ADDED", {"id": lead.id, "name": lead.name, "phone": clean_phone}, user_id=user_id)

    return lead

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: int,
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Lead).where(Lead.id == contact_id, Lead.user_id == current_user.id)
    res = await db.execute(stmt)
    lead = res.scalars().first()
    if not lead:
        raise HTTPException(status_code=404, detail="Contact not found or unauthorized")
    await db.delete(lead)
    await db.commit()

    # Invalidate dashboard cache
    await cache.delete(f"dashboard:stats:{current_user.id}")
    await broadcast_event("LEAD_DELETED", {"id": contact_id}, user_id=current_user.id)

    return {"message": "Contact deleted successfully", "id": contact_id}

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns real-time analytics for Dashboard KPIs, customer sentiment distribution,
    and call connection/drop-off behavior strictly scoped to current user.
    Uses Redis cache with a 30s TTL to prevent hitting the database on every request.
    """
    return await compute_dashboard_stats(current_user.id, db)
