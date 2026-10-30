from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.models.booking import DemoBooking
from app.models.user import User
from app.schemas.lead import DemoBookingResponseSchema
from app.routers.auth_router import get_current_user

router = APIRouter(prefix="/api/demo-bookings", tags=["Demo Bookings"])

@router.get("", response_model=List[DemoBookingResponseSchema])
async def list_demo_bookings(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user:
        return []
    result = await db.execute(
        select(DemoBooking)
        .options(selectinload(DemoBooking.lead))
        .where(DemoBooking.user_id == current_user.id)
        .order_by(DemoBooking.created_at.desc())
    )
    return result.scalars().all()
