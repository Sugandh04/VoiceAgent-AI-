import asyncio
import logging
import os
import sys
import re
import pathlib
from typing import Annotated, Optional
from dotenv import load_dotenv

# Ensure project root is in sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
    Agent,
    AgentSession,
    function_tool,
)
from livekit.plugins import openai, silero, deepgram
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.models.lead import Lead, LeadStatus, CallbackRequest
from app.models.booking import DemoBooking
from app.models.call import Call, CallStatus, ConversationTurn
from app.models.campaign import CampaignLead, CampaignLeadStatus
from app.services.whatsapp_service import whatsapp_service
from datetime import datetime

load_dotenv()
logger = logging.getLogger("livekit-voice-agent")

def normalize_phone_number(text: str) -> Optional[str]:
    """Extracts a valid 10-digit Indian phone/WhatsApp number from text or spoken digit words."""
    if not text:
        return None
    word_map = {
        'zero': '0', 'oh': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9'
    }
    clean = text.lower()
    for w, d in word_map.items():
        clean = re.sub(r'\b' + w + r'\b', d, clean)
    digits = re.sub(r'\D', '', clean)
    if digits.startswith('91') and len(digits) == 12:
        digits = digits[2:]
    elif digits.startswith('0') and len(digits) == 11:
        digits = digits[1:]
    match = re.search(r'[6-9]\d{9}', digits)
    return match.group(0) if match else (digits if len(digits) == 10 else None)

def is_telecom_announcement(text: str) -> bool:
    """Detects Indian telecom IVR/voicemail/switched-off automated announcements (AMD)."""
    if not text:
        return False
    lower = text.lower()
    ivr_phrases = [
        "subscriber is busy",
        "switched off",
        "not reachable",
        "cannot take your call",
        "leave a message",
        "please dial again",
        "vyast hai",
        "kripya kuch samay baad",
        "switch off",
        "kripya pratiksha karein",
        "number does not exist"
    ]
    return any(p in lower for p in ivr_phrases)

async def record_booking_in_db(
    phone_or_whatsapp: str,
    name: str = "Lead",
    day_and_time: str = "Upcoming Slot",
    notes: str = "",
    call_sid: Optional[str] = None
):
    """Direct database helper to save lead, demo booking, and trigger WhatsApp confirmation."""
    try:
        await init_db()
        phone = normalize_phone_number(phone_or_whatsapp) or phone_or_whatsapp or "Anonymous"
        async with AsyncSessionLocal() as db:
            user_id = None
            if call_sid:
                c_res = await db.execute(select(Call).where(Call.call_sid == call_sid))
                c_obj = c_res.scalars().first()
                if c_obj and c_obj.user_id:
                    user_id = c_obj.user_id

            stmt = select(Lead).where(Lead.phone_number == phone)
            if user_id:
                stmt = stmt.where(Lead.user_id == user_id)
            res = await db.execute(stmt)
            lead = res.scalars().first()
            if not lead:
                lead = Lead(
                    user_id=user_id,
                    phone_number=phone,
                    name=name if name != "Lead" else None,
                    whatsapp_number=phone,
                    status=LeadStatus.DEMO_SCHEDULED,
                    notes=f"Auto-captured from call. {notes}"
                )
                db.add(lead)
                await db.flush()
            else:
                lead.status = LeadStatus.DEMO_SCHEDULED
                if name and name != "Lead":
                    lead.name = name
                lead.whatsapp_number = phone
                if not user_id and lead.user_id:
                    user_id = lead.user_id

            booking = DemoBooking(
                user_id=user_id,
                lead_id=lead.id,
                call_sid=call_sid,
                scheduled_time=datetime.utcnow(),
                notes=f"5-Minute Phone Demo time requested: {day_and_time}. Notes: {notes}",
                status="CONFIRMED"
            )
            db.add(booking)
            await db.commit()
            logger.info(f"💾 [DATABASE] Saved 5-Min Phone Demo Booking for '{name}' | Phone: '{phone}' | Slot: '{day_and_time}' (user_id={user_id})")

            # Trigger automated WhatsApp confirmation
            asyncio.create_task(
                whatsapp_service.send_demo_confirmation(
                    to_phone=phone,
                    name=name if name != "Lead" else "Sir/Ma'am",
                    demo_time=day_and_time,
                    notes=notes
                )
            )
            return True
    except Exception as e:
        logger.error(f"❌ Database error in record_booking_in_db: {e}", exc_info=True)
        return False

@function_tool
async def book_demo(
    phone_or_whatsapp: Annotated[str, "Phone or WhatsApp number given by caller for the 5-minute phone demo call"],
    name: Annotated[str, "Name of caller if known, otherwise 'Caller'"] = "Caller",
    preferred_day_and_time: Annotated[str, "Agreed day and time for 5-minute phone demo (e.g. Tomorrow 3 PM)"] = "Tomorrow",
    notes: Annotated[str, "Any brief notes or customer requests"] = "",
) -> str:
    """Tool to immediately book and confirm a 5-minute phone call demo appointment."""
    logger.info(f"⚡ [TOOL CALL] book_demo invoked for phone demo: name={name}, phone={phone_or_whatsapp}, time={preferred_day_and_time}")
    success = await record_booking_in_db(
        phone_or_whatsapp=phone_or_whatsapp,
        name=name,
        day_and_time=preferred_day_and_time,
        notes=notes
    )
    if success:
        return f"Phone demo confirmed for {name} on {preferred_day_and_time}. Our specialist will call on {phone_or_whatsapp}. Confirmation sent to WhatsApp."
    return f"Phone demo confirmed for {name} on {preferred_day_and_time}."

async def entrypoint(ctx: JobContext):
    await init_db()
    room_name = ctx.room.name
    logger.info(f"🎙️ LiveKit WebRTC Voice Worker joined room: {room_name}")

    # 1. Connect to room audio tracks via WebRTC (UDP / Opus)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # 2. Record Call in DB
    try:
        async with AsyncSessionLocal() as db:
            call_rec = Call(
                call_sid=room_name,
                status=CallStatus.IN_PROGRESS,
                direction="INBOUND" if "console" in room_name else "OUTBOUND",
                start_time=datetime.utcnow()
            )
            db.add(call_rec)
            await db.commit()
    except Exception as e:
        logger.warning(f"Could not initialize call record in DB: {e}")

    # 3. Configure Ultra-fast LLM
    llm_instance = openai.LLM(model="gpt-4o-mini") if settings.OPENAI_API_KEY else openai.LLM(
        base_url=settings.SARVAM_LLM_URL.replace("/v1/chat/completions", "/v1"),
        api_key=settings.SARVAM_API_KEY,
        model=settings.SARVAM_LLM_MODEL
    )

    # 4. Configure Ultra-low latency TTS (Deepgram Aura sub-120ms)
    tts_instance = deepgram.TTS(
        api_key=settings.DEEPGRAM_API_KEY,
        model="aura-asteria-en"
    )

    # 5. Create Agent with VAD + STT + Tools + Speed Tuning
    agent = Agent(
        instructions=settings.SYSTEM_PROMPT,
        vad=silero.VAD.load(
            min_speech_duration=0.15,
            min_silence_duration=0.35
        ),
        stt=deepgram.STT(api_key=settings.DEEPGRAM_API_KEY),
        llm=llm_instance,
        tts=tts_instance,
        tools=[book_demo],
        allow_interruptions=True,
        min_endpointing_delay=0.25,
        max_endpointing_delay=0.55
    )

    # 6. Session with Preemptive Generation & Turn Speed Optimization
    session = AgentSession(
        allow_interruptions=True,
        min_interruption_duration=0.6,
        min_interruption_words=2,
        resume_false_interruption=True,
        preemptive_generation=True,
        min_endpointing_delay=0.25,
        max_endpointing_delay=0.55
    )

    # 7. Auto-persist all conversation turns and auto-capture phone numbers on disconnect
    async def persist_session_data():
        logger.info(f"💾 Persisting complete conversation for room {room_name}...")
        try:
            messages = list(agent.chat_ctx.messages()) if hasattr(agent.chat_ctx, 'messages') else []
            extracted_phone = None
            conversation_text = []

            async with AsyncSessionLocal() as db:
                for msg in messages:
                    role_str = str(msg.role).upper()
                    speaker = "USER" if "USER" in role_str else "BOT"
                    text = msg.content if isinstance(msg.content, str) else " ".join([str(c) for c in msg.content if c])
                    if not text:
                        continue
                    conversation_text.append(f"{speaker}: {text}")

                    # Save conversation turn
                    turn = ConversationTurn(
                        call_sid=room_name,
                        speaker=speaker,
                        text=text,
                        timestamp=datetime.utcnow()
                    )
                    db.add(turn)

                    # Look for phone/WhatsApp number in user messages
                    if speaker == "USER" and not extracted_phone:
                        candidate = normalize_phone_number(text)
                        if candidate:
                            extracted_phone = candidate
                            logger.info(f"📱 Auto-detected phone number from conversation: {extracted_phone}")

                # Update call record & check AMD / IVR announcement
                stmt = select(Call).where(Call.call_sid == room_name)
                res = await db.execute(stmt)
                call_obj = res.scalars().first()
                if call_obj:
                    # Check if speech was an automated IVR / switched-off announcement
                    is_ivr = any(is_telecom_announcement(t) for t in conversation_text if "USER:" in t)
                    if is_ivr:
                        call_obj.status = CallStatus.NO_ANSWER
                        logger.info(f"🚫 Telecom announcement / IVR detected for call {room_name}. Marked status as NO_ANSWER.")
                    else:
                        call_obj.status = CallStatus.COMPLETED

                    call_obj.end_time = datetime.utcnow()
                    if call_obj.start_time:
                        call_obj.duration_seconds = int((call_obj.end_time - call_obj.start_time).total_seconds())

                await db.commit()

            # If user provided a phone number or demo info (and was a real human), ensure it is recorded as a Lead & Booking
            if extracted_phone and not any(is_telecom_announcement(t) for t in conversation_text):
                full_conv_notes = "\n".join(conversation_text[-4:])  # recent context
                await record_booking_in_db(
                    phone_or_whatsapp=extracted_phone,
                    name="Caller",
                    day_and_time="As discussed in call",
                    notes=f"Auto-captured from transcript. Context: {full_conv_notes}",
                    call_sid=room_name
                )
        except Exception as e:
            logger.error(f"Error persisting session data: {e}", exc_info=True)

    ctx.add_shutdown_callback(persist_session_data)

    await session.start(agent=agent, room=ctx.room)
    logger.info("✅ Agent session active. Ready to book demos and save to SQLite.")

    # Greet caller
    if settings.ENABLE_GREETING:
        logger.info(f"🗣️ Sending greeting: {settings.GREETING_MESSAGE}")
        await session.say(settings.GREETING_MESSAGE, allow_interruptions=True)

def run_agent():
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    run_agent()
