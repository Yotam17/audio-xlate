import os
import tempfile
from typing import List, Dict
from pydub import AudioSegment
from app.utils.r2_utils import download_from_r2
from app.utils.srt_utils import parse_srt_entries
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_narration_sync_logic(
    translated_srt: str,
    optimized_sentences: List[Dict],
    uuid: str
) -> Dict:
    """
    Validate narration synchronization by comparing SRT timing with actual audio duration.
    
    Args:
        translated_srt: The translated SRT content as a string
        optimized_sentences: List of optimized sentence dictionaries
        uuid: The UUID associated with the TTS batch
    
    Returns:
        Dict containing validation entries and average percentage deviation
    """
    logger.info(f"Starting narration sync validation for UUID: {uuid}")
    
    # Parse the translated SRT to get timing information
    srt_entries = parse_srt_entries(translated_srt)
    srt_map = {entry["index"]: entry for entry in srt_entries}
    
    logger.info(f"Parsed {len(srt_entries)} SRT entries")
    logger.info(f"Processing {len(optimized_sentences)} optimized sentences")
    
    validation_entries = []
    total_percentage_deviation = 0.0
    total_real_percentage_deviation = 0.0  # For real (not absolute) values
    valid_entries_count = 0
    
    # Process each optimized entry
    for i, opt in enumerate(optimized_sentences):
        try:
            logger.info(f"Processing optimized entry {i}: {opt.get('text', '')[:50]}...")
            
            if "srt_entries" not in opt or not opt["srt_entries"]:
                logger.warning(f"Optimized entry {i} has no srt_entries, skipping")
                continue
            
            # Get the first and last SRT entry numbers for this optimized entry
            srt_entry_numbers = opt["srt_entries"]
            first_srt_num = srt_entry_numbers[0]
            last_srt_num = srt_entry_numbers[-1]
            
            # Get SRT timing information
            if first_srt_num not in srt_map or last_srt_num not in srt_map:
                logger.warning(f"SRT entries {first_srt_num} or {last_srt_num} not found in srt_map")
                continue
            
            first_srt_entry = srt_map[first_srt_num]
            last_srt_entry = srt_map[last_srt_num]
            
            # Calculate SRT duration (end of last entry - start of first entry)
            srt_start_ms = first_srt_entry["start_ms"]
            srt_end_ms = last_srt_entry["end_ms"]
            srt_duration_ms = srt_end_ms - srt_start_ms
            srt_duration_sec = srt_duration_ms / 1000.0
            
            # Download and measure audio duration
            r2_key = f"tts/{uuid}/{str(i).zfill(3)}.mp3"
            logger.info(f"Downloading audio file: {r2_key}")
            
            temp_audio_path = download_from_r2(r2_key)
            audio_segment = AudioSegment.from_file(temp_audio_path)
            audio_duration_sec = len(audio_segment) / 1000.0
            
            # Clean up temporary file
            os.remove(temp_audio_path)
            
            # Calculate gap and percentage deviation
            gap_sec = srt_duration_sec - audio_duration_sec
            percentage_deviation = (gap_sec / srt_duration_sec) * 100 if srt_duration_sec > 0 else 0
            
            logger.info(f"Entry {i}: SRT={srt_duration_sec:.2f}s, Audio={audio_duration_sec:.2f}s, Gap={gap_sec:.2f}s, Dev={percentage_deviation:.1f}%")
            
            # Create validation entry
            validation_entry = {
                "optimized_entry_index": i,
                "srt_entries": srt_entry_numbers,
                "srt_time": round(srt_duration_sec, 3),
                "audio_time": round(audio_duration_sec, 3),
                "gap": round(gap_sec, 3),
                "percentage_deviation": round(percentage_deviation, 2)
            }
            
            validation_entries.append(validation_entry)
            total_percentage_deviation += abs(percentage_deviation)  # Absolute for average
            total_real_percentage_deviation += percentage_deviation  # Real for average
            valid_entries_count += 1
            
        except Exception as e:
            logger.error(f"Error processing optimized entry {i}: {str(e)}")
            continue
    
    # Calculate average percentage deviations
    average_percentage_deviation = (
        total_percentage_deviation / valid_entries_count 
        if valid_entries_count > 0 else 0.0
    )
    
    average_real_percentage_deviation = (
        total_real_percentage_deviation / valid_entries_count 
        if valid_entries_count > 0 else 0.0
    )
    
    logger.info(f"Validation complete. Processed {valid_entries_count} entries.")
    logger.info(f"Average absolute percentage deviation: {average_percentage_deviation:.2f}%")
    logger.info(f"Average real percentage deviation: {average_real_percentage_deviation:.2f}%")
    
    return {
        "validation_entries": validation_entries,
        "average_percentage_deviation": round(average_percentage_deviation, 2),
        "average_real_percentage_deviation": round(average_real_percentage_deviation, 2)
    } 