from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.database import get_db
from app.models.booking import DemoBooking
from app.models.user import User
from app.schemas.lead import DemoBookingResponseSchema
from app.routers.auth_router import require_user

router = APIRouter(prefix="/api/demo-bookings", tags=["Demo Bookings"])

@router.get("", response_model=List[DemoBookingResponseSchema])
async def list_demo_bookings(
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    current_user: User = Depends(require_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(DemoBooking)
        .options(selectinload(DemoBooking.lead))
        .where(DemoBooking.user_id == current_user.id)
        .order_by(DemoBooking.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return result.scalars().all()
