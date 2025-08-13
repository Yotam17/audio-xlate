from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
import os

from app.tts.eleven_labs import ElevenLabsTts
from app.logic.tts_sentences import tts_sentences

router = APIRouter()

class SentenceEntry(BaseModel):
    text: str = Field(..., description="The merged sentence text.")
    srt_entries: List[int] = Field(..., description="The SRT line numbers included in this sentence.")

class TtsAudioRequest(BaseModel):
    optimized: List[SentenceEntry] = Field(..., description="Optimized sentences ready for tts processing.")
    tts_tool: Literal["elevenlabs"] = Field(..., description="Currently only 'elevenlabs' is supported.")
    voice_id: str = Field(..., description="Voice ID used for tts generation (e.g. from ElevenLabs).")
    model: str = Field(None, description="Model ID for tts generation (e.g. 'eleven_multilingual_v2'). If not provided, will use default.")
    max_workers: int = Field(5, description="Maximum number of parallel processes for TTS generation (default: 5).")

class TtsAudioResponse(BaseModel):
    uuid: str = Field(..., description="The UUID associated with this tts batch.")
    audio_files: List[str] = Field(..., description="List of accessible URLs for the generated audio files.")

def get_tts_tool(tool_name: str):
    if tool_name == "elevenlabs":
        return ElevenLabsTts(api_key=os.getenv("ELEVENLABS_API_KEY"))
    raise ValueError(f"tts tool '{tool_name}' is not supported yet.")

@router.post(
    "/tts_optimized_sentences",
    response_model=TtsAudioResponse,
    summary="Generate tts audio from optimized sentence flow",
    description="Uses the specified tts tool (currently only ElevenLabs) to generate audio from optimized SRT sentences and uploads to R2."
)
def tts_optimized_sentences(req: TtsAudioRequest):
    try:
        tts = get_tts_tool(req.tts_tool)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    sentences = [entry.text for entry in req.optimized]
    result = tts_sentences(sentences, tts, req.voice_id, req.model, max_workers=req.max_workers)
    return TtsAudioResponse(**result)
