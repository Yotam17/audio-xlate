import os
from openai import OpenAI
from app.tts.interface import TTSInterface

class OpenAITts(TTSInterface):
    def __init__(self, api_key: str = None):
        """
        Initialize OpenAI TTS client.
        
        Args:
            api_key: OpenAI API key (optional, will use OPENAI_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Available voices for OpenAI TTS
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        # Available models for OpenAI TTS
        self.available_models = ["tts-1", "tts-1-hd"]

    def get_tts(self, text: str, voice_id: str, model: str = None) -> bytes:
        """
        Generate TTS audio from text using OpenAI TTS.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice identifier (one of: "alloy", "echo", "fable", "onyx", "nova", "shimmer")
            model: Model to use (optional, defaults to "tts-1")
        
        Returns:
            Audio data as bytes (MP3 format)
        """
        try:
            # Validate voice_id
            if voice_id not in self.available_voices:
                raise ValueError(f"Invalid voice_id '{voice_id}'. Available voices: {', '.join(self.available_voices)}")
            
            # Use default model if none provided
            model_id = model if model in self.available_models else "tts-1"
            
            # Generate speech
            response = self.client.audio.speech.create(
                model=model_id,
                voice=voice_id,
                input=text
            )
            
            # Return audio content as bytes
            return response.content
            
        except Exception as e:
            raise Exception(f"OpenAI TTS failed: {str(e)}")

    def list_available_voices(self, language_code: str = None) -> list:
        """
        List available voices for OpenAI TTS.
        
        Args:
            language_code: Language code (not used for OpenAI TTS, kept for interface compatibility)
        
        Returns:
            List of available voice names
        """
        return [
            {
                "name": voice,
                "description": self._get_voice_description(voice),
                "provider": "openai"
            }
            for voice in self.available_voices
        ]

    def get_voice_info(self, voice_id: str) -> dict:
        """
        Get detailed information about a specific voice.
        
        Args:
            voice_id: Voice identifier
        
        Returns:
            Dictionary with voice information
        """
        if voice_id not in self.available_voices:
            raise ValueError(f"Voice {voice_id} not found. Available voices: {', '.join(self.available_voices)}")
        
        return {
            "name": voice_id,
            "description": self._get_voice_description(voice_id),
            "provider": "openai",
            "supported_models": self.available_models
        }

    def _get_voice_description(self, voice: str) -> str:
        """
        Get human-readable description of a voice.
        
        Args:
            voice: Voice identifier
        
        Returns:
            Voice description
        """
        descriptions = {
            "alloy": "A balanced, neutral voice with a warm tone",
            "echo": "A clear, articulate voice with good pronunciation",
            "fable": "A storytelling voice with expressive qualities",
            "onyx": "A deep, authoritative voice with gravitas",
            "nova": "A bright, energetic voice with enthusiasm",
            "shimmer": "A smooth, melodic voice with a pleasant tone"
        }
        return descriptions.get(voice, "OpenAI TTS voice")

    def validate_text_length(self, text: str) -> bool:
        """
        Validate that text is within OpenAI TTS limits.
        
        Args:
            text: Text to validate
        
        Returns:
            True if text is valid, False otherwise
        """
        # OpenAI TTS has a limit of 4096 characters
        return len(text) <= 4096

    def get_text_length_info(self, text: str) -> dict:
        """
        Get information about text length and TTS limits.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with length information
        """
        current_length = len(text)
        max_length = 4096
        
        return {
            "current_length": current_length,
            "max_length": max_length,
            "is_valid": current_length <= max_length,
            "remaining_chars": max_length - current_length if current_length <= max_length else 0
        }
