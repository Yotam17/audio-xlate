import re
from datetime import timedelta
from typing import List, Dict

def parse_time(srt_time: str):
    """Parse SRT time format (HH:MM:SS,mmm) to milliseconds"""
    h, m, s = srt_time.split(":")
    s, ms = s.split(",")
    total_ms = int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms)
    return total_ms

def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to SRT timestamp format (HH:MM:SS,mmm).
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def parse_srt_entries(srt_text: str):
    """Parse SRT text and return list of entries with index and start_ms"""
    entries = []
    blocks = re.split(r'\n{2,}', srt_text.strip())

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            number = int(lines[0])
            start, end = lines[1].split(" --> ")
            text = " ".join(lines[2:]).strip()
            entries.append({
                "index": number,
                "start_ms": parse_time(start.strip()),
                "end_ms": parse_time(end.strip()),
                "text": text
            })

    return entries

def whisper_to_srt_format(subtitles: List[Dict]) -> str:
    """
    Convert a list of subtitle dictionaries to SRT format.
    
    Args:
        subtitles: List of dicts with 'start', 'end', 'text' keys
                  start and end should be in seconds
    
    Returns:
        SRT formatted string
    """
    srt_lines = []
    
    for i, subtitle in enumerate(subtitles, 1):
        # Format timestamps
        start_time = format_timestamp(subtitle['start'])
        end_time = format_timestamp(subtitle['end'])
        
        # Add SRT entry
        srt_lines.append(str(i))  # Index
        srt_lines.append(f"{start_time} --> {end_time}")  # Timestamps
        srt_lines.append(subtitle['text'])  # Text
        srt_lines.append("")  # Empty line between entries
    
    return "\n".join(srt_lines)

def add_opening_entries_to_srt(srt_text: str, opening_entries: List[Dict]) -> str:
    """
    Add opening entries to the beginning of SRT text and renumber existing entries.
    
    Args:
        srt_text: Original SRT text
        opening_entries: List of opening entry dictionaries with index, start, end, text
    
    Returns:
        Modified SRT text with opening entries added
    """
    if not opening_entries:
        return srt_text
    
    # Parse existing SRT entries
    existing_entries = parse_srt_entries(srt_text)
    
    # Create new SRT with opening entries + existing entries (renumbered)
    new_entries = []
    
    # Add opening entries first
    for entry in opening_entries:
        new_entries.append({
            "index": entry["index"],
            "start_ms": parse_time(entry["start"]),
            "end_ms": parse_time(entry["end"]),
            "text": entry["text"]
        })
    
    # Add existing entries with renumbered indices
    for entry in existing_entries:
        new_entries.append({
            "index": entry["index"] + len(opening_entries),
            "start_ms": entry["start_ms"],
            "end_ms": entry["end_ms"],
            "text": entry["text"]
        })
    
    # Convert back to SRT format
    srt_lines = []
    for entry in new_entries:
        start_time = format_timestamp(entry["start_ms"] / 1000.0)
        end_time = format_timestamp(entry["end_ms"] / 1000.0)
        srt_lines.append(str(entry["index"]))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(entry["text"])
        srt_lines.append("")
    
    return "\n".join(srt_lines) 