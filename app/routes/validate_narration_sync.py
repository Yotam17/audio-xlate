from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from app.logic.validate_narration_sync import validate_narration_sync_logic

router = APIRouter()

class OptimizedSentence(BaseModel):
    text: str = Field(..., description="The merged sentence text.")
    srt_entries: List[int] = Field(..., description="The SRT line numbers included in this sentence.")

class ValidateNarrationSyncRequest(BaseModel):
    translated_srt: str = Field(..., description="The translated SRT content as a string.")
    optimized_sentences: List[OptimizedSentence] = Field(..., description="List of optimized sentences.")
    uuid: str = Field(..., description="The UUID associated with the TTS batch.")

class SyncValidationEntry(BaseModel):
    optimized_entry_index: int = Field(..., description="Index of the optimized entry.")
    srt_entries: List[int] = Field(..., description="SRT entry numbers in this optimized entry.")
    srt_time: float = Field(..., description="SRT duration in seconds (end - start).")
    audio_time: float = Field(..., description="Actual audio duration in seconds.")
    gap: float = Field(..., description="Difference between SRT and audio time (srt_time - audio_time).")
    percentage_deviation: float = Field(..., description="Percentage deviation from SRT time.")

class ValidateNarrationSyncResponse(BaseModel):
    validation_entries: List[SyncValidationEntry] = Field(..., description="List of validation results for each optimized entry.")
    average_percentage_deviation: float = Field(..., description="Average absolute percentage deviation across all entries.")
    average_real_percentage_deviation: float = Field(..., description="Average real percentage deviation across all entries (can be negative).")

@router.post(
    "/validate_narration_sync",
    response_model=ValidateNarrationSyncResponse,
    summary="Validate narration synchronization",
    description="Compares SRT timing with actual audio duration to measure synchronization accuracy."
)
def validate_narration_sync_endpoint(req: ValidateNarrationSyncRequest):
    try:
        result = validate_narration_sync_logic(
            translated_srt=req.translated_srt,
            optimized_sentences=[entry.dict() for entry in req.optimized_sentences],
            uuid=req.uuid
        )
        return ValidateNarrationSyncResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 