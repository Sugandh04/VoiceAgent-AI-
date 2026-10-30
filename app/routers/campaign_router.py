import csv
import io
import asyncio
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel

from app.database import get_db, AsyncSessionLocal
from app.models.campaign import Campaign, CampaignLead, CampaignStatus, CampaignLeadStatus
from app.models.user import User
from app.services.exotel_service import exotel_service
from app.routers.auth_router import get_current_user

logger = logging.getLogger("campaign-router")
router = APIRouter(prefix="/api/campaigns", tags=["Outbound Campaigns"])

class CampaignSchema(BaseModel):
    id: int
    name: str
    status: str
    total_leads: int
    called_leads: int
    booked_demos: int
    concurrency: int

    class Config:
        from_attributes = True

async def run_campaign_dialer(campaign_id: int):
    """Background queue worker that dials pending campaign leads."""
    logger.info(f"🚀 Starting background dialer for Campaign #{campaign_id}...")
    while True:
        async with AsyncSessionLocal() as db:
            # Check campaign status
            res = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
            campaign = res.scalars().first()
            if not campaign or campaign.status != CampaignStatus.RUNNING:
                logger.info(f"Campaign #{campaign_id} is no longer running (status: {getattr(campaign, 'status', 'DELETED')}). Stopping dialer.")
                break

            # Fetch pending leads up to concurrency limit
            stmt = select(CampaignLead).where(
                CampaignLead.campaign_id == campaign_id,
                CampaignLead.status == CampaignLeadStatus.PENDING
            ).limit(campaign.concurrency)
            leads_res = await db.execute(stmt)
            pending_leads = leads_res.scalars().all()

            if not pending_leads:
                campaign.status = CampaignStatus.COMPLETED
                await db.commit()
                logger.info(f"🎉 Campaign #{campaign_id} completed all leads!")
                break

            for lead in pending_leads:
                lead.status = CampaignLeadStatus.DIALING
                lead.attempts += 1
                lead.last_called_at = datetime.utcnow()
                campaign.called_leads += 1
            await db.commit()

            # Trigger Exotel dials concurrently
            for lead in pending_leads:
                logger.info(f"📞 Dialing campaign lead: {lead.name} ({lead.phone_number})")
                try:
                    result = await exotel_service.initiate_outbound_call(
                        destination_number=lead.phone_number,
                        custom_field=f"campaign_{campaign_id}_lead_{lead.id}"
                    )
                    lead.call_sid = result.get("call_sid") if result.get("success") else None
                except Exception as e:
                    logger.error(f"Error dialing {lead.phone_number}: {e}")

            await asyncio.sleep(10)  # Wait interval between batches

@router.post("/upload", response_model=CampaignSchema)
async def upload_campaign_csv(
    name: str = Form(...),
    concurrency: int = Form(5),
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a CSV file of leads (Columns: name, phone, company, city).
    Creates a new Outbound Campaign ready for automatic dialing.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    contents = await file.read()
    text = contents.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    user_id = current_user.id
    campaign = Campaign(
        user_id=user_id,
        name=name,
        status=CampaignStatus.DRAFT,
        concurrency=concurrency,
        total_leads=0,
        called_leads=0,
        booked_demos=0
    )
    db.add(campaign)
    await db.flush()

    leads_count = 0
    for row in reader:
        phone = row.get("phone") or row.get("phone_number") or row.get("mobile") or row.get("Phone")
        if not phone:
            continue
        clean_phone = phone.strip()
        lead_name = row.get("name") or row.get("Name") or "Business Lead"
        company = row.get("company") or row.get("Company") or ""
        city = row.get("city") or row.get("City") or ""

        lead_obj = CampaignLead(
            campaign_id=campaign.id,
            name=lead_name.strip(),
            phone_number=clean_phone,
            company=company.strip(),
            city=city.strip(),
            status=CampaignLeadStatus.PENDING
        )
        db.add(lead_obj)
        leads_count += 1

    campaign.total_leads = leads_count
    await db.commit()
    await db.refresh(campaign)

    logger.info(f"📁 Created Campaign '{name}' (ID: {campaign.id}) with {leads_count} leads for user {user_id} from CSV.")
    return campaign

@router.get("", response_model=List[CampaignSchema])
async def list_campaigns(
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all outbound calling campaigns for the authenticated user."""
    if not current_user:
        return []
    res = await db.execute(
        select(Campaign)
        .where(Campaign.user_id == current_user.id)
        .order_by(Campaign.created_at.desc())
    )
    return res.scalars().all()

@router.post("/{campaign_id}/start")
async def start_campaign(
    campaign_id: int, 
    background_tasks: BackgroundTasks, 
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start automated outbound dialing for a campaign."""
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    if current_user:
        stmt = stmt.where(Campaign.user_id == current_user.id)
    res = await db.execute(stmt)
    campaign = res.scalars().first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.RUNNING
    await db.commit()

    background_tasks.add_task(run_campaign_dialer, campaign_id)
    return {"message": f"Campaign #{campaign_id} started successfully", "status": "RUNNING"}

@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: int, 
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pause an active outbound calling campaign."""
    stmt = select(Campaign).where(Campaign.id == campaign_id)
    if current_user:
        stmt = stmt.where(Campaign.user_id == current_user.id)
    res = await db.execute(stmt)
    campaign = res.scalars().first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    return {"message": f"Campaign #{campaign_id} paused", "status": "PAUSED"}
