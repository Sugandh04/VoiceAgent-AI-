import json
import base64
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.audio.audio_buffer import AudioBuffer
from app.audio.resampler import downsample_16k_to_8k, chunk_telephony_audio
from app.services.sarvam_stt import sarvam_stt_service
from app.services.sarvam_llm import sarvam_chat_service
from app.services.elevenlabs_tts import elevenlabs_tts_service
from app.services.intent_detector import intent_detector
from app.models.call import Call, CallStatus, ConversationTurn
from app.models.lead import Lead, LeadStatus
from app.models.booking import DemoBooking

logger = logging.getLogger(__name__)

router = APIRouter()

class CallSession:
    def __init__(self, call_sid: str, system_prompt: str, is_telephony: bool = False):
        self.call_sid = call_sid
        self.stream_sid = None
        self.is_telephony = is_telephony
        self.sample_rate = 8000 if is_telephony else 16000
        self.active = True
        self.call_started = False
        self.greeting_played = False
        self.bot_speaking = False
        self.history = [{"role": "system", "content": system_prompt}]
        self.lead_id = None

    def add_user(self, text: str):
        self.history.append({"role": "user", "content": text})

    def add_assistant(self, text: str):
        self.history.append({"role": "assistant", "content": text})

@router.websocket("/ws/voice-bot")
async def voice_bot_websocket(websocket: WebSocket, callSid: str = None):
    await websocket.accept()
    
    session_id = f"sess_{id(websocket)}"
    initial_call_sid = callSid or f"call_{session_id}"
    
    logger.info(f"WebSocket connected: sessionId={session_id}, callSid={initial_call_sid}")
    
    call_session = CallSession(initial_call_sid, settings.SYSTEM_PROMPT)
    audio_buffer = AudioBuffer(sample_rate=call_session.sample_rate)

    # 1. Start background loops
    async def process_audio_loop():
        """Listens for user speech completion in audio buffer and executes AI turn."""
        while call_session.active:
            await asyncio.sleep(0.15)
            
            if not call_session.greeting_played or call_session.bot_speaking or not call_session.active:
                continue

            if not audio_buffer.is_ready():
                continue

            pcm_data = audio_buffer.drain()
            if not pcm_data:
                continue

            logger.info(f"[{call_session.call_sid}] Transcribing {len(pcm_data)} bytes of user audio...")
            
            user_text = await sarvam_stt_service.transcribe(pcm_data, sample_rate=call_session.sample_rate)
            if not user_text or not user_text.strip():
                continue

            # Prevent echo
            if is_self_echo(user_text, call_session):
                continue

            logger.info(f"[{call_session.call_sid}] USER: {user_text}")
            call_session.add_user(user_text)
            
            # Send user transcript event to UI
            await send_user_transcript(websocket, user_text)
            await save_turn_to_db(call_session.call_sid, "USER", user_text)

            # Intent Check (Booking, Callback, or Disconnect)
            intent_reply, scheduled_time, intent_type = intent_detector.detect_intent(user_text)
            
            if intent_reply:
                if intent_reply == intent_detector.END_CALL:
                    await end_call_with_farewell(websocket, call_session, "No problem at all! Have a great day. Goodbye!")
                    break
                
                # Persist demo booking if scheduled
                if intent_type == "BOOKING" and scheduled_time:
                    await record_booking_to_db(call_session.call_sid, scheduled_time, f"Voice call intent: {user_text}")
                
                await end_call_with_farewell(websocket, call_session, intent_reply)
                break

            # LLM Chat completion
            bot_text = await sarvam_chat_service.chat(call_session.history)
            logger.info(f"[{call_session.call_sid}] BOT: {bot_text}")
            call_session.add_assistant(bot_text)
            
            await save_turn_to_db(call_session.call_sid, "BOT", bot_text)
            await speak(websocket, call_session, bot_text)

    async def greeting_task():
        """Plays greeting once start event is received."""
        while call_session.active and not call_session.call_started:
            await asyncio.sleep(0.1)

        if not call_session.active:
            return

        await asyncio.sleep(max(settings.GREETING_DELAY_MS, 200) / 1000.0)
        
        if settings.ENABLE_GREETING and not call_session.greeting_played and call_session.active:
            call_session.greeting_played = True
            greeting = settings.GREETING_MESSAGE
            logger.info(f"[{call_session.call_sid}] BOT (greeting): {greeting}")
            
            call_session.add_assistant(greeting)
            await save_turn_to_db(call_session.call_sid, "BOT", greeting)
            await speak(websocket, call_session, greeting)
        else:
            call_session.greeting_played = True

    audio_task = asyncio.create_task(process_audio_loop())
    greet_task = asyncio.create_task(greeting_task())

    try:
        while True:
            msg_text = await websocket.receive_text()
            data = json.loads(msg_text)
            event = data.get("event", "").lower()

            if event == "connected":
                logger.info(f"[{call_session.call_sid}] Client connected event received")

            elif event == "start":
                stream_sid = (
                    data.get("stream_sid") or 
                    data.get("streamSid") or 
                    data.get("start", {}).get("stream_sid") or 
                    data.get("start", {}).get("streamSid") or 
                    f"stream_{session_id}"
                )
                call_session.stream_sid = stream_sid
                
                extracted_call_sid = (
                    data.get("start", {}).get("call_sid") or 
                    data.get("start", {}).get("callSid") or 
                    data.get("call_sid") or 
                    data.get("callSid")
                )
                if extracted_call_sid:
                    call_session.call_sid = extracted_call_sid

                # Detect if this is an Exotel telephony stream
                if "exotel" in msg_text.lower() or "stream_sid" in data:
                    call_session.is_telephony = True
                    call_session.sample_rate = 8000

                logger.info(f"[{call_session.call_sid}] Call started. streamSid={stream_sid}, telephony={call_session.is_telephony}")
                call_session.call_started = True

            elif event == "media":
                if call_session.greeting_played:
                    payload_b64 = data.get("media", {}).get("payload", "")
                    if payload_b64:
                        chunk = base64.b64decode(payload_b64)
                        audio_buffer.append(chunk)

                        # Instant Barge-In Interruption Check
                        if call_session.bot_speaking and audio_buffer.consumes_barge_in():
                            logger.info(f"[{call_session.call_sid}] BARGE-IN DETECTED: Halting bot playback immediately.")
                            call_session.bot_speaking = False
                            audio_buffer.reset()
                            await send_clear_event(websocket, call_session.stream_sid)

            elif event == "bot_speech_done":
                logger.info(f"[{call_session.call_sid}] Bot finished speaking on client.")
                call_session.bot_speaking = False
                audio_buffer.reset()

            elif event == "stop":
                logger.info(f"[{call_session.call_sid}] Stop event received from client.")
                break

    except WebSocketDisconnect:
        logger.info(f"[{call_session.call_sid}] WebSocket disconnected.")
    except Exception as e:
        logger.error(f"[{call_session.call_sid}] WebSocket handler error: {e}")
    finally:
        call_session.active = False
        audio_task.cancel()
        greet_task.cancel()
        await update_call_status(call_session.call_sid, CallStatus.COMPLETED)

async def speak(websocket: WebSocket, call_session: CallSession, text: str):
    """Synthesizes TTS audio and streams it to the client/telephony stream."""
    if not call_session.active:
        return

    call_session.bot_speaking = True
    pcm_audio = await elevenlabs_tts_service.synthesize_pcm(text, sample_rate=call_session.sample_rate)
    
    if not call_session.active or not call_session.bot_speaking:
        return

    try:
        # If telephony (8kHz Exotel), send in paced 40ms packets or direct media payload
        if call_session.is_telephony:
            chunks = chunk_telephony_audio(pcm_audio, chunk_ms=40)
            for chunk in chunks:
                if not call_session.active or not call_session.bot_speaking:
                    break
                await websocket.send_json({
                    "event": "media",
                    "stream_sid": call_session.stream_sid,
                    "media": {
                        "payload": base64.b64encode(chunk).decode("utf-8")
                    }
                })
                await asyncio.sleep(0.038) # Pacing for jitter buffers
        else:
            # Web client receives single full audio payload with transcript
            await websocket.send_json({
                "event": "speak",
                "text": text,
                "stream_sid": call_session.stream_sid or "web_stream",
                "media": {
                    "payload": base64.b64encode(pcm_audio).decode("utf-8")
                }
            })
    except Exception as e:
        logger.error(f"[{call_session.call_sid}] Error sending speak event: {e}")

async def end_call_with_farewell(websocket: WebSocket, call_session: CallSession, farewell_text: str):
    logger.info(f"[{call_session.call_sid}] Ending call with farewell: '{farewell_text}'")
    call_session.add_assistant(farewell_text)
    await save_turn_to_db(call_session.call_sid, "BOT", farewell_text)
    await speak(websocket, call_session, farewell_text)
    await asyncio.sleep(1.0)
    
    call_session.active = False
    try:
        await websocket.send_json({
            "event": "stop",
            "stream_sid": call_session.stream_sid
        })
    except Exception:
        pass

async def send_clear_event(websocket: WebSocket, stream_sid: str):
    try:
        await websocket.send_json({
            "event": "clear",
            "stream_sid": stream_sid
        })
    except Exception as e:
        logger.error(f"Failed sending clear event: {e}")

async def send_user_transcript(websocket: WebSocket, text: str):
    try:
        await websocket.send_json({
            "event": "user_transcript",
            "text": text
        })
    except Exception as e:
        logger.error(f"Failed sending user transcript: {e}")

def is_self_echo(user_text: str, call_session: CallSession) -> bool:
    if not user_text or not user_text.strip():
        return True
    clean_user = user_text.strip().lower()
    for msg in reversed(call_session.history):
        if msg.get("role") == "assistant":
            bot_text = msg.get("content", "").lower()
            if clean_user in bot_text or bot_text in clean_user:
                logger.warning(f"[{call_session.call_sid}] DROPPED SPEAKER ECHO: '{user_text}'")
                return True
            break
    return False

# Database helper functions
async def save_turn_to_db(call_sid: str, speaker: str, text: str):
    async with AsyncSessionLocal() as session:
        try:
            turn = ConversationTurn(call_sid=call_sid, speaker=speaker, text=text)
            session.add(turn)
            await session.commit()
        except Exception as e:
            logger.error(f"Failed saving turn to DB: {e}")

async def record_booking_to_db(call_sid: str, scheduled_time, notes: str):
    async with AsyncSessionLocal() as session:
        try:
            call_res = await session.execute(select(Call).where(Call.call_sid == call_sid))
            call_obj = call_res.scalars().first()
            user_id = call_obj.user_id if call_obj else None
            lead_id = None
            if call_obj and call_obj.from_number:
                lead_stmt = select(Lead).where(Lead.phone_number == call_obj.from_number)
                if user_id:
                    lead_stmt = lead_stmt.where(Lead.user_id == user_id)
                lead_res = await session.execute(lead_stmt)
                lead_obj = lead_res.scalars().first()
                if lead_obj:
                    lead_id = lead_obj.id
                    lead_obj.status = LeadStatus.DEMO_SCHEDULED
                    if not user_id and lead_obj.user_id:
                        user_id = lead_obj.user_id

            booking = DemoBooking(
                user_id=user_id,
                lead_id=lead_id,
                call_sid=call_sid,
                scheduled_time=scheduled_time,
                notes=notes,
                status="CONFIRMED"
            )
            session.add(booking)
            await session.commit()
            logger.info(f"[{call_sid}] Persisted DemoBooking to database for {scheduled_time} (user_id={user_id})")
        except Exception as e:
            logger.error(f"Failed saving booking to DB: {e}")

async def update_call_status(call_sid: str, status: CallStatus):
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(select(Call).where(Call.call_sid == call_sid))
            call_obj = result.scalars().first()
            if call_obj:
                call_obj.status = status
                await session.commit()
        except Exception as e:
            logger.error(f"Failed updating call status: {e}")
