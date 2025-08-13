import os
import tempfile
import ffmpeg
from typing import List, Dict
from app.utils.r2_utils import download_from_r2, upload_file_to_r2
from app.logic.validate_narration_sync import validate_narration_sync_logic
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for adjustment thresholds
MIN_ADJUSTMENT_SECOND = 1.0  # Only adjust if gap is > 1 second
MIN_ADJUSTMENT_PERCENTAGE = 4.0  # Only adjust if percentage deviation is > 4%
MAX_SYNC_ADJUSTMENT = 0.15  # Maximum adjustment factor (0.85 to 1.15)

def adjust_audio_length_logic(
    translated_srt: str,
    optimized_sentences: List[Dict],
    uuid: str
) -> Dict:
    """
    Adjust audio length based on validation results to improve synchronization.
    
    Args:
        translated_srt: The translated SRT content as a string
        optimized_sentences: List of optimized sentence dictionaries
        uuid: The UUID associated with the TTS batch
    
    Returns:
        Dict containing list of adjusted entry indices
    """
    logger.info(f"Starting audio length adjustment for UUID: {uuid}")
    
    # Step 1: Get validation results
    validation_result = validate_narration_sync_logic(
        translated_srt=translated_srt,
        optimized_sentences=optimized_sentences,
        uuid=uuid
    )
    
    validation_entries = validation_result["validation_entries"]
    logger.info(f"Got validation results for {len(validation_entries)} entries")
    
    adjusted_entries = []
    
    # Step 2: Process each validation entry
    for entry in validation_entries:
        entry_index = entry["optimized_entry_index"]
        gap_seconds = abs(entry["gap"])
        percentage_deviation = entry["percentage_deviation"]
        
        logger.info(f"Processing entry {entry_index}: gap={gap_seconds:.2f}s, deviation={percentage_deviation:.1f}%")
        
        # Check if adjustment is needed
        if gap_seconds > MIN_ADJUSTMENT_SECOND and abs(percentage_deviation) > MIN_ADJUSTMENT_PERCENTAGE:
            logger.info(f"Entry {entry_index} requires adjustment")
            
            try:
                # Calculate adjustment factor
                # Positive percentage means audio is longer than SRT (need to speed up)
                # Negative percentage means audio is shorter than SRT (need to slow down)
                adjustment_required = 1.0 - (percentage_deviation / 100.0)
                
                # Clamp adjustment to valid range
                min_adjustment = 1.0 - MAX_SYNC_ADJUSTMENT  # 0.85
                max_adjustment = 1.0 + MAX_SYNC_ADJUSTMENT  # 1.15
                
                if adjustment_required < min_adjustment:
                    adjustment_required = min_adjustment
                    logger.info(f"Clamped adjustment to minimum: {adjustment_required}")
                elif adjustment_required > max_adjustment:
                    adjustment_required = max_adjustment
                    logger.info(f"Clamped adjustment to maximum: {adjustment_required}")
                
                logger.info(f"Final adjustment factor: {adjustment_required:.3f}")
                
                # Step 3: Download original audio
                original_r2_key = f"tts/{uuid}/{str(entry_index).zfill(3)}.mp3"
                adjusted_r2_key = f"tts/{uuid}/{str(entry_index).zfill(3)}-adjusted.mp3"
                
                logger.info(f"Downloading original audio: {original_r2_key}")
                temp_audio_path = download_from_r2(original_r2_key)
                
                # Step 4: Apply FFmpeg adjustment
                temp_adjusted_path = temp_audio_path.replace(".mp3", "-adjusted.mp3")
                
                logger.info(f"Applying FFmpeg adjustment with factor {adjustment_required}")
                
                # Use FFmpeg to adjust speed without changing pitch
                stream = ffmpeg.input(temp_audio_path)
                stream = ffmpeg.filter(stream, 'atempo', adjustment_required)
                stream = ffmpeg.output(stream, temp_adjusted_path, acodec='mp3')
                
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                
                # Step 5: Upload adjusted audio to R2
                logger.info(f"Uploading adjusted audio: {adjusted_r2_key}")
                upload_file_to_r2(temp_adjusted_path, adjusted_r2_key)
                
                # Clean up temporary files
                os.remove(temp_audio_path)
                os.remove(temp_adjusted_path)
                
                adjusted_entries.append(entry_index)
                logger.info(f"Successfully adjusted entry {entry_index}")
                
            except Exception as e:
                logger.error(f"Error adjusting entry {entry_index}: {str(e)}")
                # Clean up temp file if it exists
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                continue
        else:
            logger.info(f"Entry {entry_index} does not require adjustment (gap={gap_seconds:.2f}s, deviation={percentage_deviation:.1f}%)")
    
    logger.info(f"Audio adjustment complete. Adjusted {len(adjusted_entries)} entries: {adjusted_entries}")
    
    return {
        "adjusted": adjusted_entries
    } 