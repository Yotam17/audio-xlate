from fastapi import APIRouter, Body
from app.logic.optimize import optimize_sentence_flow

router = APIRouter()

@router.post("/optimize_sentence_flow")
def optimize_flow(srt_text: str = Body(..., embed=True)):
    """
    Returns a list of merged sentence chunks for TTS purposes.
    """
    result = optimize_sentence_flow(srt_text)
    return {"optimized": result}
