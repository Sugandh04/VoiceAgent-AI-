import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class ElevenLabsTtsService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.voice_id = settings.ELEVENLABS_VOICE_ID
        self.model_id = settings.ELEVENLABS_MODEL_ID

    async def synthesize_pcm(self, text: str, sample_rate: int = 16000) -> bytes:
        """
        Synthesizes spoken text into raw Linear PCM bytes via ElevenLabs Turbo v2.5.
        Formats: pcm_16000 for web calls, pcm_8000 for telephony.
        """
        if not text or not text.strip():
            return b""

        output_format = "pcm_16000" if sample_rate >= 16000 else "pcm_8000"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}?output_format={output_format}"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "use_speaker_boost": True
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    pcm_bytes = response.content
                    logger.info(f"ElevenLabs synthesized {len(pcm_bytes)} PCM bytes ({output_format}) for: '{text[:30]}...'")
                    return pcm_bytes
                else:
                    logger.error(f"ElevenLabs TTS error ({response.status_code}): {response.text}")
                    return b""
            except Exception as e:
                logger.error(f"Failed calling ElevenLabs TTS: {e}")
                return b""

elevenlabs_tts_service = ElevenLabsTtsService()
