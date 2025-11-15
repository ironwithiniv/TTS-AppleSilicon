"""
TTS Engine module for speech synthesis.
Supports Coqui TTS (local) and ElevenLabs (cloud API).
Optimized for Apple Silicon with Metal (MPS) support.
"""

import os
import torch
import numpy as np
import soundfile as sf
from typing import Optional, Dict
from pathlib import Path


class TTSEngine:
    """Text-to-Speech engine with support for multiple backends."""
    
    def __init__(self, config: Dict):
        """
        Initialize TTS engine.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.engine = config.get('tts', {}).get('engine', 'coqui')
        self.device = self._get_device()
        self.model = None
        self.speaker_manager = None
        
        if self.engine == 'coqui':
            self._init_coqui()
        elif self.engine == 'elevenlabs':
            self._init_elevenlabs()
        else:
            raise ValueError(f"Unknown TTS engine: {self.engine}")
    
    def _get_device(self) -> str:
        """
        Determine the best available device (MPS for Apple Silicon, else CPU).
        
        Returns:
            Device string ('mps' or 'cpu')
        """
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        else:
            return "cpu"
    
    def _init_coqui(self):
        """Initialize Coqui TTS engine."""
        try:
            from TTS.api import TTS
            
            coqui_config = self.config.get('tts', {}).get('coqui', {})
            model_name = coqui_config.get('model_name', 'tts_models/en/ljspeech/tacotron2-DDC')
            
            print(f"Initializing Coqui TTS with model: {model_name}")
            print(f"Using device: {self.device}")
            
            # Initialize TTS with device parameter
            # Note: Some TTS models may not support MPS directly, will fallback to CPU
            try:
                self.tts = TTS(model_name=model_name, progress_bar=False, gpu=(self.device != "cpu"))
            except Exception:
                # Fallback: initialize without GPU parameter and manually set device
                print("Warning: Could not set device during initialization, using default")
                self.tts = TTS(model_name=model_name, progress_bar=False)
            
            # Try to move model to device if it's a PyTorch model
            if hasattr(self.tts, 'to'):
                try:
                    self.tts.to(self.device)
                except Exception as e:
                    print(f"Warning: Could not move model to {self.device}: {e}")
                    print("Continuing with default device...")
            
            print("Coqui TTS initialized successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Coqui TTS: {e}")
    
    def _init_elevenlabs(self):
        """Initialize ElevenLabs TTS engine."""
        elevenlabs_config = self.config.get('tts', {}).get('elevenlabs', {})
        api_key = elevenlabs_config.get('api_key', '')
        
        if not api_key:
            raise ValueError("ElevenLabs API key not provided in config.yaml")
        
        self.api_key = api_key
        self.voice_id = elevenlabs_config.get('voice_id', '21m00Tcm4TlvDq8ikWAM')
        self.model_id = elevenlabs_config.get('model_id', 'eleven_monolingual_v1')
        
        print("ElevenLabs TTS initialized (will use API for synthesis)")
    
    def synthesize(self, text: str, output_path: str, speaker: Optional[str] = None) -> float:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            output_path: Path to save the audio file
            speaker: Optional speaker name/ID (for multi-speaker models)
            
        Returns:
            Duration of the generated audio in seconds
        """
        if self.engine == 'coqui':
            return self._synthesize_coqui(text, output_path, speaker)
        elif self.engine == 'elevenlabs':
            return self._synthesize_elevenlabs(text, output_path)
        else:
            raise ValueError(f"Unknown engine: {self.engine}")
    
    def _synthesize_coqui(self, text: str, output_path: str, speaker: Optional[str] = None) -> float:
        """
        Synthesize using Coqui TTS.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio
            speaker: Optional speaker name
            
        Returns:
            Duration in seconds
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get sample rate from config
        sample_rate = self.config.get('tts', {}).get('coqui', {}).get('sample_rate', 22050)
        
        try:
            # Synthesize speech
            # Coqui TTS can return either audio data or save directly to file
            # We'll use the tts method that returns audio data
            if speaker:
                wav = self.tts.tts(text=text, speaker=speaker)
            else:
                wav = self.tts.tts(text=text)
            
            # Convert to numpy array if needed
            if isinstance(wav, torch.Tensor):
                # Move to CPU before converting to numpy (works for both CPU and MPS)
                if wav.device.type == 'mps':
                    wav = wav.cpu()
                wav = wav.numpy()
            
            # Ensure it's 1D array
            if wav.ndim > 1:
                wav = wav.flatten()
            
            # Normalize audio
            if wav.dtype != np.float32:
                wav = wav.astype(np.float32)
            
            max_val = np.abs(wav).max()
            if max_val > 0:
                wav = wav / max_val * 0.95  # Normalize to 95% to avoid clipping
            
            # Save audio file
            sf.write(output_path, wav, sample_rate)
            
            # Calculate duration
            duration = len(wav) / sample_rate
            
            return duration
            
        except Exception as e:
            raise RuntimeError(f"Coqui TTS synthesis failed: {e}")
    
    def _synthesize_elevenlabs(self, text: str, output_path: str) -> float:
        """
        Synthesize using ElevenLabs API.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio
            
        Returns:
            Duration in seconds
        """
        import requests
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Save audio file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # Get duration from audio file
            import soundfile as sf
            data, sample_rate = sf.read(output_path)
            duration = len(data) / sample_rate
            
            return duration
            
        except Exception as e:
            raise RuntimeError(f"ElevenLabs API synthesis failed: {e}")

