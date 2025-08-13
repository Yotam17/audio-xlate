from typing import List, Dict
from app.logic.subtitle_generation import generate_subtitles_from_whisper
from app.utils.srt_utils import format_timestamp

def whisper_to_srt_format(subtitles: List[Dict]) -> str:
    """
    Convert subtitle list to SRT format string.
    
    Args:
        subtitles: List of subtitle dictionaries
    
    Returns:
        SRT formatted string
    """
    srt_lines = []
    
    for i, subtitle in enumerate(subtitles, 1):
        # Format timestamps
        start_time = format_timestamp(subtitle['start'])
        end_time = format_timestamp(subtitle['end'])
        
        srt_lines.append(str(i))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(subtitle['text'])
        srt_lines.append("")
    
    return "\n".join(srt_lines) 