"""
FOS Survey Agent - Whisper STT
Faster-Whisper integration for Urdu speech-to-text.

Optimized for:
- Low latency transcription
- Urdu language accuracy
- CPU inference (no GPU required)
"""

import os
import io
import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import soundfile as sf
from loguru import logger

# Thread pool for CPU inference
_executor = ThreadPoolExecutor(max_workers=2)

# Global model instance (lazy loaded)
_model = None


def get_model():
    """Get or load the Whisper model."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        
        model_name = os.getenv("WHISPER_MODEL", "base")
        device = os.getenv("WHISPER_DEVICE", "cpu")
        compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        
        logger.info(f"Loading Whisper model: {model_name} on {device}")
        
        _model = WhisperModel(
            model_name,
            device=device,
            compute_type=compute_type
        )
        
        logger.info("Whisper model loaded successfully")
    
    return _model


class WhisperSTT:
    """
    Faster-Whisper STT for LiveKit integration.
    
    Provides async transcription of Urdu speech.
    """
    
    def __init__(self):
        self.language = "ur"  # Urdu
        self.beam_size = 5
        self.vad_filter = True
        
    async def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio to Urdu text.
        
        Args:
            audio_data: Raw audio bytes (WAV format)
            
        Returns:
            Transcribed Urdu text
        """
        try:
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                _executor,
                self._transcribe_sync,
                audio_data
            )
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def _transcribe_sync(self, audio_data: bytes) -> str:
        """Synchronous transcription."""
        model = get_model()
        
        # Load audio
        try:
            audio, sample_rate = sf.read(io.BytesIO(audio_data))
        except Exception:
            # Try as raw float32
            audio = np.frombuffer(audio_data, dtype=np.float32)
            sample_rate = 16000
        
        # Ensure mono
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)
        
        # Ensure float32
        audio = audio.astype(np.float32)
        
        # Transcribe
        segments, info = model.transcribe(
            audio,
            language=self.language,
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
            vad_parameters={
                "min_silence_duration_ms": 500,
                "speech_pad_ms": 200
            }
        )
        
        # Combine segments
        text = " ".join([seg.text for seg in segments]).strip()
        
        logger.debug(f"Transcribed ({info.language}): {text[:50]}...")
        
        return text
    
    async def transcribe_stream(self, audio_stream):
        """
        Transcribe streaming audio.
        
        For LiveKit integration.
        """
        # Collect audio chunks
        chunks = []
        async for chunk in audio_stream:
            chunks.append(chunk)
        
        # Combine and transcribe
        audio_data = b"".join(chunks)
        return await self.transcribe(audio_data)
