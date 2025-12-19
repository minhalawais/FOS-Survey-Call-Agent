"""
FOS Survey Agent - Indic Parler-TTS
Text-to-Speech for Urdu using Indic Parler-TTS model.

Features:
- Native Urdu support (21 Indic languages)
- 69 unique voice options
- Controllable prosody via prompts
- CPU and GPU inference
"""

import os
import io
import asyncio
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import torch
import soundfile as sf
from loguru import logger

# Thread pool for CPU inference
_executor = ThreadPoolExecutor(max_workers=1)

# Global model instances (lazy loaded)
_model = None
_tokenizer = None
_description_tokenizer = None


def get_model():
    """Load Indic Parler-TTS model."""
    global _model, _tokenizer, _description_tokenizer
    
    if _model is None:
        from parler_tts import ParlerTTSForConditionalGeneration
        from transformers import AutoTokenizer
        
        model_name = os.getenv("TTS_MODEL", "ai4bharat/indic-parler-tts")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading Indic Parler-TTS: {model_name} on {device}")
        
        _model = ParlerTTSForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float32 if device == "cpu" else torch.float16
        ).to(device)
        
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _description_tokenizer = AutoTokenizer.from_pretrained(
            model_name, 
            padding_side="left"
        )
        
        logger.info("Indic Parler-TTS loaded successfully")
    
    return _model, _tokenizer, _description_tokenizer


class IndicTTS:
    """
    Indic Parler-TTS wrapper for LiveKit integration.
    
    Generates natural Urdu speech from text.
    """
    
    def __init__(self):
        self.language = os.getenv("TTS_LANGUAGE", "urd")
        self.speaker = os.getenv("TTS_SPEAKER", "Anu")
        self.sample_rate = 22050
        
        # Voice description template
        self.description_template = (
            "{speaker} speaks clearly in Urdu with a natural tone. "
            "The speech is at a moderate pace with professional delivery."
        )
    
    async def synthesize(self, text: str) -> Optional[bytes]:
        """
        Synthesize Urdu speech from text.
        
        Args:
            text: Urdu text to speak
            
        Returns:
            WAV audio bytes
        """
        try:
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(
                _executor,
                self._synthesize_sync,
                text
            )
            return audio_bytes
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous synthesis."""
        model, tokenizer, desc_tokenizer = get_model()
        device = next(model.parameters()).device
        
        # Create description
        description = self.description_template.format(speaker=self.speaker)
        
        # Tokenize
        input_ids = desc_tokenizer(
            description,
            return_tensors="pt"
        ).input_ids.to(device)
        
        prompt_input_ids = tokenizer(
            text,
            return_tensors="pt"
        ).input_ids.to(device)
        
        # Generate
        with torch.no_grad():
            generation = model.generate(
                input_ids=input_ids,
                prompt_input_ids=prompt_input_ids,
                do_sample=True,
                temperature=1.0
            )
        
        # Convert to audio
        audio_arr = generation.cpu().numpy().squeeze()
        
        # Write to WAV
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_arr, self.sample_rate, format='WAV')
        audio_buffer.seek(0)
        
        audio_bytes = audio_buffer.read()
        logger.debug(f"Generated {len(audio_bytes)} bytes of audio")
        
        return audio_bytes
    
    async def synthesize_stream(self, text: str):
        """
        Stream audio chunks for real-time playback.
        
        For LiveKit integration with low latency.
        """
        # For now, generate full audio and yield in chunks
        audio_bytes = await self.synthesize(text)
        
        if audio_bytes:
            chunk_size = 4096
            for i in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[i:i + chunk_size]
    
    def set_speaker(self, speaker: str):
        """Set the voice speaker."""
        self.speaker = speaker
        logger.info(f"TTS speaker set to: {speaker}")
    
    def set_language(self, language: str):
        """Set the language code."""
        self.language = language
        logger.info(f"TTS language set to: {language}")
