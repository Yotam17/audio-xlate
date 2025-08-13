import os
from uuid import uuid4
from pydub import AudioSegment
from app.utils.r2_utils import upload_file_to_r2, download_from_r2, generate_presigned_url
from app.utils.srt_utils import parse_srt_entries

def combine_audio_segments(
    original_srt_text: str,
    optimized: list[dict],
    #audio_base_url: str,
    uuid: str,
    adjusted_entries: list[int] = None,
) -> str:
    """
    Combines audio segments based on optimized sentence flow and SRT timing,
    then uploads the final result to Cloudflare R2 as uuid-full.mp3.

    Args:
        original_srt_text: The original SRT content
        optimized: List of optimized sentence dictionaries
        uuid: The UUID associated with the TTS batch
        adjusted_entries: List of entry indices that have been adjusted (optional)

    Returns the temporary download URL of the uploaded file (expires in 1 hour).
    """
    print(f"original_srt_text: {original_srt_text}")
    srt_entries = parse_srt_entries(original_srt_text)
    print(f"srt_entries: {srt_entries}")
    print(f"optimized: {optimized}")
    print(f"adjusted_entries: {adjusted_entries}")

    # Create a map from SRT entry number to SRT entry data for quick lookup
    srt_map = {entry["index"]: entry for entry in srt_entries}

    full_audio = AudioSegment.silent(duration=0)
    current_pos = 0

    # Walk through optimized entries (not srt_entries)
    for i, opt in enumerate(optimized):
        if "audio_file" in opt and "srt_entries" in opt and opt["srt_entries"]:
            # Get the first SRT entry number from this optimized entry
            first_srt_entry_num = opt["srt_entries"][0]
            
            # Get the corresponding SRT entry data
            if first_srt_entry_num in srt_map:
                srt_entry = srt_map[first_srt_entry_num]
                start_ms = srt_entry["start_ms"]
                
                # Check if this entry has been adjusted
                if adjusted_entries and i in adjusted_entries:
                    r2_key = f"tts/{uuid}/{str(i).zfill(3)}-adjusted.mp3"
                    print(f"Using adjusted audio for entry {i}")
                else:
                    r2_key = f"tts/{uuid}/{str(i).zfill(3)}.mp3"
                
                print(f"Processing optimized entry {i}: SRT entry {first_srt_entry_num} at {start_ms}ms")
                print(f"R2 key: {r2_key}")

                # Add silence if needed
                if start_ms > current_pos:
                    silence_duration = start_ms - current_pos
                    full_audio += AudioSegment.silent(duration=silence_duration)
                    current_pos = start_ms

                # Download and add the audio segment using R2 key
                temp_audio_path = download_from_r2(r2_key)
                audio_segment = AudioSegment.from_file(temp_audio_path)
                full_audio += audio_segment
                current_pos += len(audio_segment)
                os.remove(temp_audio_path)
            else:
                print(f"Warning: SRT entry {first_srt_entry_num} not found in srt_map")

    local_final_path = f"/tmp/{uuid}-full.mp3"
    full_audio.export(local_final_path, format="mp3")

    # Upload to R2
    r2_key = f"tts/{uuid}/full.mp3"
    upload_file_to_r2(local_final_path, r2_key)
    os.remove(local_final_path)

    # Generate temporary download URL (expires in 1 hour)
    temp_download_url = generate_presigned_url(r2_key, expiration=3600)  # 3600 seconds = 1 hour
    
    print(f"Generated temporary download URL: {temp_download_url}")
    return temp_download_url
