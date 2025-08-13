from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import tempfile
import os
import json
from app.utils.api_utils import transcribe
from app.logic.transcription_orchestration import transcribe_to_subtitles

router = APIRouter()

class OpeningEntry(BaseModel):
    index: int = Field(..., description="The subtitle entry index (e.g., 1, 2, 3).")
    start: str = Field(..., description="Start time in SRT format (e.g., '00:00:01,000').")
    end: str = Field(..., description="End time in SRT format (e.g., '00:00:04,000').")
    text: str = Field(..., description="The subtitle text content.")

class TranscribeResponse(BaseModel):
    whisper_response: Dict = Field(..., description="Complete Whisper verbose JSON response.")
    model_used: str = Field(..., description="Whisper model used for transcription.")

class TranscribeToSubtitlesResponse(BaseModel):
    whisper_response: Dict = Field(..., description="Complete Whisper verbose JSON response.")
    subtitles: List[Dict] = Field(..., description="List of structured subtitle entries.")
    srt_text: str = Field(..., description="The complete SRT formatted text.")
    model_used: str = Field(..., description="Whisper model used for transcription.")

@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Transcribe audio file using Whisper",
    description="Upload an audio file and get the complete Whisper verbose JSON response with segments and word-level timestamps. Optionally add opening entries for silent subtitles or on-screen text."
)
async def transcribe_endpoint(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    model: Optional[str] = Form(None, description="Whisper model to use (optional)"),
    opening_entries: Optional[str] = Form(None, description="JSON string of opening entries to add to the beginning of the SRT (optional)")
):
    try:
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
            # Transcribe the file
            whisper_response = transcribe(temp_file_path, model, parsed_opening_entries)
            
            # Use the model that was actually used
            model_used = model if model else "whisper-1"
            
            return TranscribeResponse(
                whisper_response=whisper_response,
                model_used=model_used
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.post(
    "/transcribe_to_subtitles",
    response_model=TranscribeToSubtitlesResponse,
    summary="Transcribe audio file and convert to SRT subtitles",
    description="Upload an audio file, transcribe it with Whisper, and convert the result to SRT subtitles with intelligent sentence splitting. Optionally add opening entries for silent subtitles or on-screen text."
)
async def transcribe_to_subtitles_endpoint(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    model: Optional[str] = Form(None, description="Whisper model to use (optional)"),
    opening_entries: Optional[str] = Form(None, description="JSON string of opening entries to add to the beginning of the SRT (optional)")
):
    try:
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
            # Transcribe and convert to subtitles
            result = transcribe_to_subtitles(temp_file_path, model, parsed_opening_entries)
            
            # Use the model that was actually used
            model_used = model if model else "whisper-1"
            
            return TranscribeToSubtitlesResponse(
                whisper_response=result["whisper_response"],
                subtitles=result["subtitles"],
                srt_text=result["srt_text"],
                model_used=model_used
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription and subtitle generation failed: {str(e)}") 