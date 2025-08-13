import os
import requests
from app.tts.interface import TTSInterface

class ElevenLabsTts(TTSInterface):
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_tts(self, text: str, voice_id: str, model: str = None) -> bytes:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Use default model if none provided
        model_id = model if model is not None else "eleven_multilingual_v2"
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.content  # MP3 binary
