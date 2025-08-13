# TTS (Text-to-Speech) Implementations

This directory contains different TTS service implementations that conform to the `TTSInterface` abstract base class.

## Available Implementations

### 1. ElevenLabs TTS (`eleven_labs.py`)
- **Provider**: ElevenLabs
- **Features**: High-quality multilingual voices, voice cloning
- **API Key**: Required - set `ELEVENLABS_API_KEY` environment variable
- **Voice Format**: Custom voice IDs from ElevenLabs dashboard
- **Models**: `eleven_multilingual_v2` (default), custom models

### 2. Google TTS (`google_tts.py`)
- **Provider**: Google Cloud Text-to-Speech
- **Features**: Wide language support, neural voices, SSML support
- **Credentials**: Required - set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- **Voice Format**: `language_code-voice_name` (e.g., `en-US-Standard-A`, `he-IL-Standard-A`)
- **Models**: Uses Google's default neural models

### 3. OpenAI TTS (`openai_tts.py`)
- **Provider**: OpenAI
- **Features**: High-quality voices, fast generation
- **API Key**: Required - set `OPENAI_API_KEY` environment variable
- **Voice Format**: Predefined voices: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`
- **Models**: `tts-1` (default), `tts-1-hd` (higher quality)

## Usage Examples

### Basic Usage

```python
from app.tts.eleven_labs import ElevenLabsTts
from app.tts.google_tts import GoogleTts
from app.tts.openai_tts import OpenAITts

# ElevenLabs
tts = ElevenLabsTts(api_key="your_key")
audio = tts.get_tts("Hello world", "voice_id", "model_name")

# Google TTS
tts = GoogleTts()  # Uses GOOGLE_APPLICATION_CREDENTIALS env var
audio = tts.get_tts("Hello world", "en-US-Standard-A")

# OpenAI TTS
tts = OpenAITts()  # Uses OPENAI_API_KEY env var
audio = tts.get_tts("Hello world", "alloy", "tts-1")
```

### Voice Management

```python
# List available voices
voices = tts.list_available_voices()

# Get voice information
voice_info = tts.get_voice_info("voice_id")

# Google TTS - filter by language
hebrew_voices = tts.list_available_voices("he-IL")
```

### Error Handling

```python
try:
    audio = tts.get_tts(text, voice_id, model)
except Exception as e:
    print(f"TTS failed: {e}")
```

## Environment Variables

Make sure to set the following environment variables:

```bash
# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
GOOGLE_CLOUD_PROJECT=your_project_id

# OpenAI
OPENAI_API_KEY=your_openai_api_key
```

## Voice Selection Guide

### ElevenLabs
- Visit [ElevenLabs Dashboard](https://elevenlabs.io/) to create custom voices
- Use voice IDs from your dashboard
- Supports voice cloning and customization

### Google TTS
- **Standard Voices**: `en-US-Standard-A`, `en-US-Standard-B`, etc.
- **Neural Voices**: `en-US-Neural2-A`, `en-US-Neural2-B`, etc.
- **Wavenet Voices**: `en-US-Wavenet-A`, `en-US-Wavenet-B`, etc.
- **Hebrew Support**: `he-IL-Standard-A`, `he-IL-Wavenet-A`

### OpenAI TTS
- **alloy**: Balanced, neutral voice with warm tone
- **echo**: Clear, articulate voice with good pronunciation
- **fable**: Storytelling voice with expressive qualities
- **onyx**: Deep, authoritative voice with gravitas
- **nova**: Bright, energetic voice with enthusiasm
- **shimmer**: Smooth, melodic voice with pleasant tone

## Performance Considerations

- **ElevenLabs**: Best for multilingual content, voice cloning
- **Google TTS**: Best for language coverage, SSML support
- **OpenAI TTS**: Best for speed, consistent quality

## Text Length Limits

- **ElevenLabs**: No strict limit (recommended: < 5000 characters)
- **Google TTS**: No strict limit (recommended: < 5000 characters)
- **OpenAI TTS**: 4096 characters maximum
