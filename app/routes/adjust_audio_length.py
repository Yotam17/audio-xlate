from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
from app.logic.adjust_audio_length import adjust_audio_length_logic

router = APIRouter()

class OptimizedSentence(BaseModel):
    text: str = Field(..., description="The merged sentence text.")
    srt_entries: List[int] = Field(..., description="The SRT line numbers included in this sentence.")

class AdjustAudioLengthRequest(BaseModel):
    translated_srt: str = Field(..., description="The translated SRT content as a string.")
    optimized_sentences: List[OptimizedSentence] = Field(..., description="List of optimized sentences.")
    uuid: str = Field(..., description="The UUID associated with the TTS batch.")

class AdjustAudioLengthResponse(BaseModel):
    adjusted: List[int] = Field(..., description="List of entry indices that were adjusted.")

@router.post(
    "/adjust_audio_length",
    response_model=AdjustAudioLengthResponse,
    summary="Adjust audio length for better synchronization",
    description="Analyzes audio synchronization gaps and adjusts audio speed to better match SRT timing. Only adjusts entries with gaps > 1 second and percentage deviation > 4%. Maximum adjustment is ±15%."
)
def adjust_audio_length_endpoint(req: AdjustAudioLengthRequest):
    try:
        result = adjust_audio_length_logic(
            translated_srt=req.translated_srt,
            optimized_sentences=[entry.dict() for entry in req.optimized_sentences],
            uuid=req.uuid
        )
        return AdjustAudioLengthResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 