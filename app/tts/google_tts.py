import os
from google.cloud import texttospeech
from app.tts.interface import TTSInterface

class GoogleTts(TTSInterface):
    def __init__(self, credentials_path: str = None):
        """
        Initialize Google TTS client.
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file (optional)
                            If not provided, will use GOOGLE_APPLICATION_CREDENTIALS env var
        """
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        self.client = texttospeech.TextToSpeechClient()
        
        # Default voice settings
        self.default_voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Standard-A"
        )
        
        self.default_audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0,
            volume_gain_db=0.0
        )

    def get_tts(self, text: str, voice_id: str, model: str = None) -> bytes:
        """
        Generate TTS audio from text.
        
        Args:
            text: Text to convert to speech
            voice_id: Voice identifier (format: "language_code-voice_name" e.g., "en-US-Standard-A")
            model: Model to use (optional, will use default if not specified)
        
        Returns:
            Audio data as bytes (MP3 format)
        """
        try:
            # Parse voice_id to extract language and voice name
            if "-" in voice_id:
                parts = voice_id.split("-", 1)
                language_code = parts[0]
                voice_name = voice_id
            else:
                # Default to English if no language specified
                language_code = "en-US"
                voice_name = voice_id
            
            # Create voice selection params
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            
            # Create synthesis input
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # Perform text-to-speech request
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=self.default_audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            raise Exception(f"Google TTS failed: {str(e)}")

    def list_available_voices(self, language_code: str = None) -> list:
        """
        List available voices for a specific language.
        
        Args:
            language_code: Language code to filter voices (e.g., "en-US", "he-IL")
        
        Returns:
            List of available voice names
        """
        try:
            if language_code:
                voices = self.client.list_voices(language_code=language_code)
            else:
                voices = self.client.list_voices()
            
            voice_list = []
            for voice in voices.voices:
                voice_info = {
                    "name": voice.name,
                    "language_code": voice.language_codes[0] if voice.language_codes else None,
                    "ssml_gender": voice.ssml_gender.name if voice.ssml_gender else None
                }
                voice_list.append(voice_info)
            
            return voice_list
            
        except Exception as e:
            raise Exception(f"Failed to list voices: {str(e)}")

    def get_voice_info(self, voice_id: str) -> dict:
        """
        Get detailed information about a specific voice.
        
        Args:
            voice_id: Voice identifier
        
        Returns:
            Dictionary with voice information
        """
        try:
            voices = self.client.list_voices()
            
            for voice in voices.voices:
                if voice.name == voice_id:
                    return {
                        "name": voice.name,
                        "language_codes": voice.language_codes,
                        "ssml_gender": voice.ssml_gender.name if voice.ssml_gender else None,
                        "natural_sample_rate_hertz": voice.natural_sample_rate_hertz
                    }
            
            raise Exception(f"Voice {voice_id} not found")
            
        except Exception as e:
            raise Exception(f"Failed to get voice info: {str(e)}")
