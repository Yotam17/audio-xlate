# app/routes/translate.py
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict

from app.logic.translation_logic import translate_srt_with_gpt

router = APIRouter()

class TranslateRequest(BaseModel):
    source_srt: str = Field(..., description="The content of the original SRT file as a string.")
    source_language: str = Field(..., description="The language code of the original subtitles (e.g. 'en', 'he').")
    target_language: str = Field(..., description="The language code to translate the subtitles into.")
    max_workers: int = Field(5, description="Maximum number of parallel processes for translation (default: 5).")
    translation_notes: str | None = Field(None, description="Optional free text for special translation notes to guide the translation process.")

class TranslateResponse(BaseModel):
    translated_srt: str = Field(..., description="The translated SRT content as a string.")
    notes: str | None = Field(None, description="Optional notes or metadata about the translation process.")

@router.post("/translate_srt", response_model=TranslateResponse, summary="Translate subtitles using GPT", description="Translates an SRT string from a source language to a target language using GPT.")
def translate_srt_endpoint(req: TranslateRequest):
    translated, notes = translate_srt_with_gpt(
        req.source_srt,
        req.source_language,
        req.target_language,
        req.max_workers,
        req.translation_notes
    )
    print("translated", translated)
    return TranslateResponse(translated_srt=translated, notes=notes)
