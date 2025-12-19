"""
FOS Survey Agent - STT Service Client
Client for Whisper STT service with audio format conversion
"""

import io
import httpx
from typing import Optional
from loguru import logger

from app.config import settings


class STTService:
    """Client for Speech-to-Text service"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.whisper_url
        self.timeout = 60.0  # Longer timeout for CPU transcription
    
    async def transcribe(self, audio_bytes: bytes) -> Optional[str]:
        """
        Transcribe audio to text.
        Handles various audio formats (webm, wav, etc.)
        
        Args:
            audio_bytes: Audio file content (any format)
            
        Returns:
            Transcribed text or None on error
        """
        try:
            # Try to convert to WAV if needed
            wav_bytes = self._convert_to_wav(audio_bytes)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/transcribe",
                    files={"audio": ("audio.wav", wav_bytes, "audio/wav")}
                )
                response.raise_for_status()
                result = response.json()
                text = result.get("text", "").strip()
                logger.info(f"Transcribed: {text[:50]}..." if len(text) > 50 else f"Transcribed: {text}")
                return text
                
        except httpx.TimeoutException:
            logger.error("STT service timeout - CPU transcription may take longer")
            return None
        except Exception as e:
            logger.error(f"STT service error: {e}")
            return None
    
    def _convert_to_wav(self, audio_bytes: bytes) -> bytes:
        """
        Convert audio to WAV format using pydub or soundfile.
        Falls back to raw bytes if conversion fails.
        """
        # Check if already WAV (starts with RIFF header)
        if audio_bytes[:4] == b'RIFF':
            return audio_bytes
        
        try:
            # Try using soundfile for conversion
            import soundfile as sf
            import numpy as np
            
            # Read from any format
            audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Write as WAV
            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, audio_data, sample_rate, format='WAV')
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            logger.warning(f"Audio conversion failed ({e}), trying raw bytes")
            
            # Try pydub as fallback
            try:
                from pydub import AudioSegment
                
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
                wav_buffer = io.BytesIO()
                audio.export(wav_buffer, format='wav')
                wav_buffer.seek(0)
                return wav_buffer.read()
                
            except Exception as e2:
                logger.warning(f"Pydub conversion also failed ({e2}), using raw bytes")
                return audio_bytes
    
    async def health_check(self) -> bool:
        """Check if STT service is available"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Global instance
stt_service = STTService()


async def transcribe(audio_bytes: bytes) -> Optional[str]:
    """Convenience function to transcribe audio"""
    return await stt_service.transcribe(audio_bytes)
