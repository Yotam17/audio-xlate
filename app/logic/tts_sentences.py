import uuid
import multiprocessing as mp
from functools import partial
import logging
from app.utils.r2_utils import upload_audio_to_r2
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _process_single_tts(args):
    """Helper function to process a single TTS request"""
    try:
        text, tts_tool, voice_id, model, filename = args
        logger.info(f"Processing TTS for text: {text[:50]}...")
        audio = tts_tool.get_tts(text, voice_id, model)
        url = upload_audio_to_r2(audio, filename)
        logger.info(f"Successfully processed TTS for: {filename}")
        return url
    except Exception as e:
        logger.error(f"Error processing TTS for text '{text[:50]}...': {str(e)}")
        raise

def tts_sentences(
    sentences: List[str],
    tts_tool,
    voice_id: str,
    model: str = None,
    bucket_prefix: str = "tts",
    max_workers: int = 5
) -> Dict:
    """
    Generate TTS audio for multiple sentences using multiprocessing.
    
    Args:
        sentences: List of text sentences to convert to speech
        tts_tool: TTS tool instance
        voice_id: Voice ID for TTS generation
        model: Model ID for TTS generation (optional)
        bucket_prefix: Prefix for R2 bucket storage
        max_workers: Maximum number of parallel processes (default: 5)
    
    Returns:
        Dict with uuid and list of audio file URLs
    """
    unique_id = str(uuid.uuid4())
    logger.info(f"Starting TTS generation for {len(sentences)} sentences with {max_workers} workers")
    
    # Prepare arguments for multiprocessing
    args_list = []
    for idx, text in enumerate(sentences):
        filename = f"{bucket_prefix}/{unique_id}/{idx:03}.mp3"
        args_list.append((text, tts_tool, voice_id, model, filename))
    
    # Use multiprocessing to generate TTS files in parallel
    actual_workers = min(max_workers, len(sentences))
    logger.info(f"Using {actual_workers} parallel processes")
    
    try:
        with mp.Pool(processes=actual_workers) as pool:
            audio_files = pool.map(_process_single_tts, args_list)
        
        logger.info(f"Successfully generated {len(audio_files)} audio files")
        return {
            "uuid": unique_id,
            "audio_files": audio_files
        }
    except Exception as e:
        logger.error(f"Error in multiprocessing TTS generation: {str(e)}")
        raise
