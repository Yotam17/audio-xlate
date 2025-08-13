"""
API utility functions for external service calls.
"""

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

def transcribe(filename: str, model: Optional[str] = None, opening_entries: Optional[List[Dict]] = None) -> Dict:
    """
    Transcribe an audio file using OpenAI's Whisper model.
    
    Args:
        filename: Path to the audio file
        model: Whisper model to use (default: "whisper-1")
        opening_entries: Optional list of opening entries to add to the SRT
    
    Returns:
        Whisper verbose JSON response with segments and words
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Audio file not found: {filename}")
    
    # Use default model if none specified
    if model is None:
        model = "whisper-1"
    
    logger.info(f"Transcribing {filename} with model {model}")
    
    try:
        with open(filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment", "word"]
            )
        
        logger.info(f"Successfully transcribed {filename}")
        
        # Convert the OpenAI object to a dictionary
        if hasattr(transcript, 'model_dump'):
            # For newer Pydantic versions
            return transcript.model_dump()
        elif hasattr(transcript, 'dict'):
            # For older Pydantic versions
            return transcript.dict()
        else:
            # Fallback: convert to dict manually
            return dict(transcript)
        
    except Exception as e:
        logger.error(f"Error transcribing {filename}: {str(e)}")
        raise
