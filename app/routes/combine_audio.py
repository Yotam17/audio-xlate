from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List
from app.logic.combine_segments import combine_audio_segments

router = APIRouter()

class OptimizedEntry(BaseModel):
    text: str
    srt_entries: List[int]
    audio_file: str

class CombineRequest(BaseModel):
    uuid: str = Field(..., description="The unique identifier for the audio session.")
    original_srt: str = Field(..., description="The original SRT content as a string.")
    #audio_base_url: str = Field(..., description="The base URL where individual audio files are stored.")
    optimized: List[OptimizedEntry]
    adjusted_entries: List[int] = Field(default=[], description="List of entry indices that have been adjusted for better synchronization.")

class CombineResponse(BaseModel):
    audio_url: str = Field(..., description="Temporary download URL to the combined final MP3 file (expires in 1 hour).")

@router.post("/combine_audio", response_model=CombineResponse, summary="Combine audio segments", description="Combines generated audio segments into one track based on sentence flow and returns temporary download URL (expires in 1 hour). Uses adjusted audio files when available.")
def combine_audio_endpoint(req: CombineRequest):
    print(f"req: {req}")
    url = combine_audio_segments(
        original_srt_text=req.original_srt,
        optimized=[entry.dict() for entry in req.optimized],
        #audio_base_url=req.audio_base_url,
        uuid=req.uuid,
        adjusted_entries=req.adjusted_entries,
    )
    return CombineResponse(audio_url=url)
