from pydub import AudioSegment
from pathlib import Path

def generate_merged_audio(segments, output_path):
    """
    segments: List of dicts with:
        - start (float, sec)
        - end (float, sec)
        - audio_path (str)
    output_path: where to save the merged mp3

    Returns: output_path
    """
    merged = AudioSegment.silent(duration=0)

    current_time = 0.0
    for seg in segments:
        start = seg["start"]
        audio = AudioSegment.from_file(seg["audio_path"])

        # Add silence before this segment if needed
        if start > current_time:
            silence = AudioSegment.silent(duration=(start - current_time) * 1000)
            merged += silence
            current_time = start

        merged += audio
        current_time += len(audio) / 1000

    merged.export(output_path, format="mp3")
    return str(Path(output_path).resolve())