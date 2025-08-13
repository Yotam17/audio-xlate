from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from app.utils.whisper_to_srt import generate_subtitles_from_whisper, whisper_to_srt_format

router = APIRouter()

class WhisperWord(BaseModel):
    word: str = Field(..., description="The transcribed word.")
    start: float = Field(..., description="Start time of the word in seconds.")
    end: float = Field(..., description="End time of the word in seconds.")

class WhisperSegment(BaseModel):
    text: str = Field(..., description="The transcribed text for this segment.")
    start: float = Field(..., description="Start time of the segment in seconds.")
    end: float = Field(..., description="End time of the segment in seconds.")
    words: List[WhisperWord] = Field(..., description="List of words with timing information.")

class WhisperVerboseRequest(BaseModel):
    segments: List[WhisperSegment] = Field(..., description="List of Whisper segments with timing information.")

class SubtitleEntry(BaseModel):
    start: float = Field(..., description="Start time of the subtitle in seconds.")
    end: float = Field(..., description="End time of the subtitle in seconds.")
    text: str = Field(..., description="The subtitle text.")

class WhisperToSrtResponse(BaseModel):
    subtitles: List[SubtitleEntry] = Field(..., description="List of structured subtitle entries.")
    srt_text: str = Field(..., description="The complete SRT formatted text.")
    
def validate_whisper_response(segments: List[WhisperSegment]) -> None:
    """
    Validate that the Whisper response contains the required data for subtitle generation.
    
    Args:
        segments: List of Whisper segments
    
    Raises:
        HTTPException: If validation fails
    """
    if not segments:
        raise HTTPException(status_code=400, detail="No segments found in Whisper response")
    
    for i, segment in enumerate(segments):
        # Check if segment has required fields
        if not segment.text:
            raise HTTPException(status_code=400, detail=f"Segment {i} has no text")
        
        if segment.start is None or segment.end is None:
            raise HTTPException(status_code=400, detail=f"Segment {i} missing start or end time")
        
        if segment.start >= segment.end:
            raise HTTPException(status_code=400, detail=f"Segment {i} has invalid timing: start ({segment.start}) >= end ({segment.end})")
        
        # Check if segment has words with timing
        if not segment.words:
            raise HTTPException(status_code=400, detail=f"Segment {i} has no words data - word-level timing is required for subtitle generation")
        
        # Validate each word in the segment
        for j, word in enumerate(segment.words):
            if not word.word:
                raise HTTPException(status_code=400, detail=f"Segment {i}, word {j} has no text")
            
            if word.start is None or word.end is None:
                raise HTTPException(status_code=400, detail=f"Segment {i}, word {j} missing start or end time")
            
            if word.start >= word.end:
                raise HTTPException(status_code=400, detail=f"Segment {i}, word {j} has invalid timing: start ({word.start}) >= end ({word.end})")
            
            # Check if word timing is within segment timing
            if word.start < segment.start or word.end > segment.end:
                raise HTTPException(status_code=400, detail=f"Segment {i}, word {j} timing ({word.start}-{word.end}) outside segment timing ({segment.start}-{segment.end})")

@router.post(
    "/whisper_to_srt",
    response_model=WhisperToSrtResponse,
    summary="Convert Whisper verbose JSON to SRT subtitles",
    description="Converts a Whisper verbose JSON response into structured SRT-style subtitles with intelligent sentence splitting and timing optimization. Requires both segments and word-level timing data."
)
def whisper_to_srt_endpoint(req: WhisperVerboseRequest):
    try:
        # Validate the Whisper response
        validate_whisper_response(req.segments)
        
        # Convert request to the format expected by the utility
        verbose_response = {
            "segments": [segment.dict() for segment in req.segments]
        }
        
        # Generate subtitles
        subtitles = generate_subtitles_from_whisper(verbose_response)
        
        if not subtitles:
            raise HTTPException(status_code=400, detail="No subtitles could be generated from the Whisper response")
        
        # Convert to SRT format
        srt_text = whisper_to_srt_format(subtitles)
        
        # Convert to response format
        subtitle_entries = [
            SubtitleEntry(
                start=subtitle["start"],
                end=subtitle["end"],
                text=subtitle["text"]
            )
            for subtitle in subtitles
        ]
        
        return WhisperToSrtResponse(
            subtitles=subtitle_entries,
            srt_text=srt_text
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing Whisper response: {str(e)}") 