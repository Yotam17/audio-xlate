# 🎬 YT Xlate Agent

AI-powered subtitle translation and voice-over tool using OpenAI, ElevenLabs, and FFmpeg.  
Translates `.srt` files from one language to another while preserving timing, emotional tone, and pacing. Includes Text-to-Speech capabilities for creating dubbed content.

---

## 🚀 Quick Start (Docker)

```bash
git clone https://github.com/Yotam17/yt-xlate-agent.git
cd yt-xlate-agent

# Copy and configure environment variables
cp env.example .env
# Edit .env with your API keys

# Build and run the Docker container
docker build -t yt-xlate-agent .
docker run --env-file .env -p 8080:8080 yt-xlate-agent
```

The API will be available at `http://localhost:8080/docs` for interactive documentation.

---

## ⚙️ Environment Configuration

Create a `.env` file with the following variables:

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here

# ElevenLabs API Configuration  
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here

# Cloudflare R2 Storage Configuration
R2_ACCESS_KEY_ID=your-r2-access-key-id-here
R2_SECRET_ACCESS_KEY=your-r2-secret-access-key-here
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_BUCKET_NAME=yt-xlate
```

You can use `env.example` as a starting point.

---

## 📂 Project Structure

```
app/
├── logic/           # Core business logic
├── routes/          # FastAPI endpoints
├── utils/           # Utility functions
├── tts/             # Text-to-Speech integrations
├── prompts/         # AI prompts
└── main.py          # FastAPI application
```

---

## 🔧 API Endpoints

### Translation
- `POST /api/v1/translate` - Translate SRT subtitles
- `POST /api/v1/translate_voice_over` - Translate and generate TTS audio

### TTS (Text-to-Speech)
- `POST /api/v1/tts` - Generate speech from text
- `POST /api/v1/tts_sentences` - Generate TTS for multiple sentences

### Audio Processing
- `POST /api/v1/combine_audio` - Combine audio segments
- `POST /api/v1/adjust_audio_length` - Adjust audio timing

### Transcription
- `POST /api/v1/transcribe` - Transcribe audio to text
- `POST /api/v1/whisper_to_srt` - Convert Whisper output to SRT

### Optimization
- `POST /api/v1/optimize` - Optimize subtitle flow
- `POST /api/v1/validate_narration_sync` - Validate audio-text synchronization

---

## 📝 Features

- ✅ Multi-language subtitle translation
- ✅ Text-to-Speech integration (ElevenLabs)
- ✅ Audio timing adjustment
- ✅ Whisper transcription
- ✅ Cloud storage integration (Cloudflare R2)
- ✅ Parallel processing for faster results
- ✅ RESTful API with OpenAPI documentation

---

## 🛠️ Development

### Local Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

---

## 🪪 License

This project is licensed under the MIT License.
See the [LICENSE](LICENSE) file for details.

---

## ⚠️ FFmpeg Licensing Notice

This project uses FFmpeg for subtitle and audio processing.
FFmpeg is installed via the Debian/Ubuntu package manager (apt), using the default build (typically LGPL).

No custom codecs or static linking are used.

➡️ If you modify or rebuild FFmpeg (e.g., to enable GPL codecs like libx264), you are responsible for complying with the FFmpeg licensing terms.

---

## 👤 Author

**Yotam Rosenthal**

- [LinkedIn](https://www.linkedin.com/in/yotam-rosenthal-7806b925/)
- [GitHub](https://github.com/Yotam17)
