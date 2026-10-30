import numpy as np
import io
import wave
from typing import List

def pcm_to_wav(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2) -> bytes:
    """Wraps raw linear PCM bytes in a valid RIFF WAV header."""
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return wav_io.getvalue()

def downsample_16k_to_8k(pcm_16k: bytes) -> bytes:
    """Downsamples 16-bit Mono Linear PCM from 16kHz to 8kHz by skipping alternate samples."""
    audio_data = np.frombuffer(pcm_16k, dtype=np.int16)
    downsampled = audio_data[::2]
    return downsampled.tobytes()

def upsample_8k_to_16k(pcm_8k: bytes) -> bytes:
    """Upsamples 16-bit Mono Linear PCM from 8kHz to 16kHz using linear interpolation."""
    audio_data = np.frombuffer(pcm_8k, dtype=np.int16)
    upsampled = np.repeat(audio_data, 2)
    return upsampled.tobytes()

def chunk_telephony_audio(pcm_8k: bytes, chunk_ms: int = 40) -> List[bytes]:
    """
    Chunks 8kHz 16-bit Mono PCM into standard telephony frames.
    8000 samples/sec * 2 bytes = 16000 bytes/sec = 16 bytes/ms.
    40ms frame = 40 * 16 = 640 bytes.
    """
    chunk_size = chunk_ms * 16
    return [pcm_8k[i:i + chunk_size] for i in range(0, len(pcm_8k), chunk_size)]
