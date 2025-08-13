# app/routes/translate_voice_over.py

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
import tempfile
import os
import uuid

from app.logic.transcription_orchestration import transcribe_to_subtitles
from app.logic.translation_logic import translate_srt_with_gpt
from app.logic.optimize import optimize_sentence_flow
from app.logic.tts_sentences import tts_sentences
from app.logic.combine_segments import combine_audio_segments
from app.logic.adjust_audio_length import adjust_audio_length_logic
from app.tts.eleven_labs import ElevenLabsTts

router = APIRouter()

class OpeningEntry(BaseModel):
    index: int = Field(..., description="The subtitle entry index (e.g., 1, 2, 3)")
    start: str = Field(..., description="Start time in SRT format (e.g., '00:00:01,000')")
    end: str = Field(..., description="End time in SRT format (e.g., '00:00:04,000')")
    text: str = Field(..., description="The subtitle text content to display")

    class Config:
        schema_extra = {
            "example": {
                "index": 1,
                "start": "00:00:00,000",
                "end": "00:00:03,000",
                "text": "Welcome to our presentation"
            }
        }

class TranslateVoiceOverRequest(BaseModel):
    origin_lang: str = Field(..., description="The source language code (e.g. 'en', 'he').")
    target_lang: str = Field(..., description="The target language code (e.g. 'en', 'he').")
    tts_tool: str = Field(..., description="TTS tool to use (currently only 'elevenlabs' supported).")
    voice_id: str = Field(..., description="Voice ID for TTS generation.")
    tts_model: Optional[str] = Field(None, description="Model ID for TTS generation (optional).")
    max_workers: int = Field(5, description="Maximum number of parallel processes for translation and TTS generation (default: 5).")
    translation_notes: Optional[str] = Field(None, description="Optional free text for special translation notes to guide the translation process.")
    whisper_model: Optional[str] = Field(None, description="Whisper model to use for transcription (optional).")

class TranslateVoiceOverResponse(BaseModel):
    origin_srt: str = Field(..., description="The original SRT content generated from the audio")
    translated_srt: str = Field(..., description="The translated SRT content in the target language")
    audio_url: str = Field(..., description="Temporary download URL to the combined final MP3 file (expires in 1 hour)")

    class Config:
        schema_extra = {
            "example": {
                "origin_srt": "1\n00:00:01,000 --> 00:00:04,000\nHello world\n\n2\n00:00:04,000 --> 00:00:07,000\nHow are you?",
                "translated_srt": "1\n00:00:01,000 --> 00:00:04,000\nשלום עולם\n\n2\n00:00:04,000 --> 00:00:07,000\nמה שלומך?",
                "audio_url": "https://example.com/audio/abc123.mp3"
            }
        }

class ErrorDetail(BaseModel):
    error: str = Field(..., description="Error message describing what went wrong")
    error_type: str = Field(..., description="Type of the exception that occurred")
    traceback: str = Field(..., description="Full stack trace for debugging purposes")

    class Config:
        schema_extra = {
            "example": {
                "error": "TTS generation failed: API key is invalid",
                "error_type": "AuthenticationError",
                "traceback": "Traceback (most recent call last):\n  File \"...\"\n    ..."
            }
        }

class ErrorResponse(BaseModel):
    detail: ErrorDetail = Field(..., description="Detailed error information")

    class Config:
        schema_extra = {
            "example": {
                "detail": {
                    "error": "TTS generation failed: API key is invalid",
                    "error_type": "AuthenticationError",
                    "traceback": "Traceback (most recent call last):\n  File \"...\"\n    ..."
                }
            }
        }

@router.post(
    "/translate_voice_over", 
    response_model=TranslateVoiceOverResponse,
    summary="Translate voice over from audio file",
    description="Upload an audio file, transcribe it, translate the content, and generate new audio in the target language",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Invalid input parameters"},
        500: {"model": ErrorResponse, "description": "Internal Server Error - Processing failed"}
    }
)
async def translate_voice_over(
    file: UploadFile = File(..., description="Audio file to transcribe and translate (max 25MB)"),
    origin_lang: str = Form(..., description="The source language code (e.g. 'en', 'he', 'es', 'fr')"),
    target_lang: str = Form(..., description="The target language code (e.g. 'en', 'he', 'es', 'fr')"),
    tts_tool: str = Form(..., description="TTS tool to use (currently only 'elevenlabs' supported)"),
    voice_id: str = Form(..., description="Voice ID for TTS generation (e.g. 'voice123' for ElevenLabs)"),
    tts_model: Optional[str] = Form(None, description="Model ID for TTS generation (e.g. 'eleven_multilingual_v2' for ElevenLabs)"),
    max_workers: int = Form(5, description="Maximum number of parallel processes for translation and TTS generation (default: 5, max: 10)"),
    translation_notes: Optional[str] = Form(None, description="Optional free text for special translation notes to guide the translation process"),
    whisper_model: Optional[str] = Form(None, description="Whisper model to use for transcription (e.g. 'whisper-1', 'whisper-1-large')"),
    opening_entries: Optional[str] = Form(None, description="JSON string of opening entries to add to the beginning of the SRT (optional)")
):
    try:
        print(f"[DEBUG] Starting translate_voice_over with file: {file.filename}, size: {file.size} bytes")
        print(f"[DEBUG] Parameters: origin_lang={origin_lang}, target_lang={target_lang}, tts_tool={tts_tool}")
        print(f"[DEBUG] Additional params: voice_id={voice_id}, max_workers={max_workers}, whisper_model={whisper_model}")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (limit to 25MB for Whisper)
        if file.size and file.size > 25 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 25MB")
        
        # Parse opening entries if provided
        parsed_opening_entries = None
        if opening_entries:
            try:
                import json
                opening_entries_list = json.loads(opening_entries)
                # Validate the structure
                for entry in opening_entries_list:
                    if not all(key in entry for key in ["index", "start", "end", "text"]):
                        raise HTTPException(status_code=400, detail="Invalid opening entry format. Each entry must have index, start, end, and text fields.")
                parsed_opening_entries = opening_entries_list
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format for opening_entries")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            # Write uploaded file to temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Step 1: Transcribe audio to SRT
            print(f"[DEBUG] Starting Step 1: Transcription with whisper_model={whisper_model}")
            try:
                transcription_result = transcribe_to_subtitles(
                    temp_file_path, 
                    whisper_model, 
                    parsed_opening_entries
                )
                origin_srt = transcription_result["srt_text"]
                print(f"[DEBUG] Step 1 completed successfully. SRT length: {len(origin_srt)} characters")
            except Exception as e:
                print(f"[ERROR] Step 1 (Transcription) failed: {str(e)}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                raise Exception(f"Transcription failed: {str(e)}")
            
            # Step 2: Translate SRT
            print(f"[DEBUG] Starting Step 2: Translation from {origin_lang} to {target_lang} with {max_workers} workers")
            try:
                translated_srt, notes = translate_srt_with_gpt(
                    origin_srt,
                    origin_lang,
                    target_lang,
                    max_workers,
                    translation_notes
                )
                print(f"[DEBUG] Step 2 completed successfully. Translated SRT length: {len(translated_srt)} characters")
            except Exception as e:
                print(f"[ERROR] Step 2 (Translation) failed: {str(e)}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                raise Exception(f"Translation failed: {str(e)}")

            # Step 3: Optimize sentences
            print(f"[DEBUG] Starting Step 3: Sentence optimization")
            try:
                optimized = optimize_sentence_flow(translated_srt)
                print(f"[DEBUG] Step 3 completed successfully. Optimized {len(optimized)} sentences")
            except Exception as e:
                print(f"[ERROR] Step 3 (Sentence optimization) failed: {str(e)}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                raise Exception(f"Sentence optimization failed: {str(e)}")

            # Step 4: Generate TTS files
            print(f"[DEBUG] Starting Step 4: TTS generation with {tts_tool}, voice_id={voice_id}, model={tts_model}")
            try:
                if tts_tool == "elevenlabs":
                    api_key = os.getenv("ELEVENLABS_API_KEY")
                    print(f"[DEBUG] Using ElevenLabs API key: {'***' + api_key[-4:] if api_key else 'NOT SET'}")
                    tts_tool_instance = ElevenLabsTts(api_key=api_key)
                else:
                    raise HTTPException(status_code=400, detail=f"TTS tool '{tts_tool}' is not supported yet.")
                
                sentences = [entry["text"] for entry in optimized]
                print(f"[DEBUG] Generating TTS for {len(sentences)} sentences")
                tts_result = tts_sentences(sentences, tts_tool_instance, voice_id, tts_model, max_workers=max_workers)
                print(f"[DEBUG] Step 4 completed successfully. TTS UUID: {tts_result.get('uuid', 'N/A')}")
            except Exception as e:
                print(f"[ERROR] Step 4 (TTS generation) failed: {str(e)}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                raise Exception(f"TTS generation failed: {str(e)}")
            
            # Add audio file URLs to optimized entries
            for i, entry in enumerate(optimized):
                entry["audio_file"] = tts_result["audio_files"][i]

            # Step 5: Adjust audio length for better synchronization
            print(f"[DEBUG] Starting Step 5: Audio length adjustment")
            try:
                adjustment_result = adjust_audio_length_logic(
                    translated_srt=translated_srt,
                    optimized_sentences=optimized,
                    uuid=tts_result["uuid"]
                )
                adjusted_entries = adjustment_result["adjusted"]
                print(f"[DEBUG] Step 5 completed successfully. Adjusted {len(adjusted_entries)} entries")
            except Exception as e:
                print(f"[ERROR] Step 5 (Audio length adjustment) failed: {str(e)}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                raise Exception(f"Audio length adjustment failed: {str(e)}")

            # Step 6: Combine audio (using adjusted files when available)
            print(f"[DEBUG] Starting Step 6: Audio combination")
            try:
                audio_url = combine_audio_segments(
                    original_srt_text=translated_srt,
                    optimized=optimized,
                    uuid=tts_result["uuid"],
                    adjusted_entries=adjusted_entries
                )
                print(f"[DEBUG] Step 6 completed successfully. Audio URL: {audio_url}")
            except Exception as e:
                print(f"[ERROR] Step 6 (Audio combination) failed: {str(e)}")
                print(f"[ERROR] Exception type: {type(e).__name__}")
                import traceback
                print(f"[ERROR] Traceback: {traceback.format_exc()}")
                raise Exception(f"Audio combination failed: {str(e)}")

            print(f"[DEBUG] All steps completed successfully!")
            print(f"[DEBUG] Final audio_url: {audio_url}")
            print(f"[DEBUG] Final adjusted_entries count: {len(adjusted_entries) if adjusted_entries else 0}")
            return TranslateVoiceOverResponse(
                origin_srt=origin_srt,
                translated_srt=translated_srt,
                audio_url=audio_url
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except FileNotFoundError as e:
        print(f"[ERROR] FileNotFoundError: {str(e)}")
        raise HTTPException(status_code=400, detail=f"File not found: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Unexpected error in translate_voice_over: {str(e)}")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        import traceback
        full_traceback = traceback.format_exc()
        print(f"[ERROR] Full traceback:\n{full_traceback}")
        error_detail = {
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": full_traceback
        }
        raise HTTPException(status_code=500, detail=error_detail)
