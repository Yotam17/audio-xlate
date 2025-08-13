import os
from openai import OpenAI
from typing import Dict, Optional, List
import logging
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_to_subtitles(filename: str, model: Optional[str] = None, opening_entries: Optional[List[Dict]] = None) -> Dict:
    """
    Transcribe an audio file and convert to SRT subtitles.
    
    Args:
        filename: Path to the audio file
        model: Whisper model to use (default: "whisper-1")
        opening_entries: Optional list of opening entries to add to the SRT
    
    Returns:
        Dict containing both transcription and subtitle data
    """
    from app.utils.api_utils import transcribe
    from app.logic.subtitle_generation import generate_subtitles_from_whisper
    from app.utils.srt_utils import whisper_to_srt_format, add_opening_entries_to_srt
    
    # First, transcribe the audio
    whisper_response = transcribe(filename, model, opening_entries)
    
    # Generate subtitles
    subtitles = generate_subtitles_from_whisper(whisper_response)
    
    # Convert to SRT format
    srt_text = whisper_to_srt_format(subtitles)
    
    # Add opening entries if provided
    if opening_entries:
        srt_text = add_opening_entries_to_srt(srt_text, opening_entries)
    
    return {
        "whisper_response": whisper_response,
        "subtitles": subtitles,
        "srt_text": srt_text
    }

# Function moved to app.utils.srt_utils
