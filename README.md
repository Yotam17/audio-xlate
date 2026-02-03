# Audio Xlate - AI-Powered Audio Translation & TTS Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Evaluation-red.svg)](EVALUATION-LICENSE.md)

A comprehensive AI-powered platform for audio transcription, translation, and text-to-speech synthesis. Built with FastAPI, OpenAI Whisper, and multiple TTS providers.

## 🌐 Live Demo

**Try it out live:** [Audio Translate Pro Demo](https://app--audio-translate-pro-ad27c76c.base44.app/Home)

## 🚀 Features

- **Audio Transcription**: Convert audio to text using OpenAI Whisper
- **Multi-language Translation**: AI-powered text translation
- **Text-to-Speech**: Multiple TTS providers (OpenAI, Google, ElevenLabs)
- **Audio Processing**: FFmpeg-based audio manipulation and optimization
- **Subtitle Generation**: Create SRT files from audio
- **Voice-over Translation**: Complete audio translation pipeline
- **Health Monitoring**: Comprehensive health check endpoints
- **Docker Support**: Containerized deployment

## 🏗️ Architecture

```
audio-xlate/
├── app/
│   ├── logic/           # Core business logic
│   ├── routes/          # API endpoints
│   ├── tts/            # Text-to-Speech providers
│   ├── utils/          # Utility functions
│   └── main.py         # FastAPI application
├── Dockerfile           # Container configuration
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 📋 Prerequisites

- Python 3.10+
- FFmpeg
- Docker (optional)
- API keys for:
  - OpenAI
  - ElevenLabs (optional)
  - Google Cloud (optional)

## 🛠️ Installation

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd audio-xlate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Environment Setup**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your actual API keys and configuration
   nano .env  # or use your preferred editor
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 2: Docker Deployment

1. **Build the image**
   ```bash
   docker build -t audio-xlate .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env audio-xlate
   ```

## ⚙️ Environment Configuration

### Creating .env from env.example

The project includes an `env.example` file that you must copy and configure:

```bash
# Copy the example file
cp env.example .env

# Edit the .env file with your actual values
nano .env
```

### Required Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs (Optional)
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Google Cloud (Optional)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# R2 Storage (Optional)
R2_ACCOUNT_ID=your_r2_account_id
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=your_bucket_name

# Server Configuration
PORT=8000
HOST=0.0.0.0
```

## 🚀 Quick Start

1. **Start the service**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Root Endpoint: http://localhost:8000/

3. **Test transcription**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/transcribe" \
        -H "Content-Type: multipart/form-data" \
        -F "audio_file=@your_audio.mp3"
   ```

## 📚 API Endpoints

### Core Services

- **`/api/v1/transcribe`** - Audio transcription
- **`/api/v1/translate`** - Text translation
- **`/api/v1/tts`** - Text-to-speech synthesis
- **`/api/v1/translate-voice-over`** - Complete audio translation pipeline

### Audio Processing

- **`/api/v1/combine-audio`** - Merge audio segments
- **`/api/v1/optimize`** - Audio optimization
- **`/api/v1/adjust-audio-length`** - Audio length adjustment

### Utilities

- **`/api/v1/whisper-to-srt`** - Generate SRT subtitles
- **`/api/v1/validate-narration-sync`** - Validate audio-text synchronization

### Health Monitoring

- **`/health`** - Comprehensive health check
- **`/health/simple`** - Basic health status
- **`/ready`** - Readiness probe

## 🔧 Development

### Code Structure

- **`app/logic/`** - Business logic and orchestration
- **`app/routes/`** - API route handlers
- **`app/tts/`** - TTS provider implementations
- **`app/utils/`** - Utility functions and helpers

### Adding New TTS Providers

1. Create a new class in `app/tts/`
2. Implement the `TTSInterface` methods
3. Add configuration to environment variables
4. Update the TTS factory in `app/tts/__init__.py`

### Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

## 🐳 Docker

### Build Options

```bash
# Development build
docker build -t audio-xlate:dev .

# Production build
docker build --target production -t audio-xlate:prod .
```

### Docker Compose (Optional)

Create a `docker-compose.yml` file for easier development:

```yaml
version: '3.8'
services:
  audio-xlate:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./app:/app/app
    environment:
      - PYTHONPATH=/app
```

## 📊 Monitoring & Health Checks

The application provides comprehensive health monitoring:

- **System Metrics**: CPU, memory, disk usage
- **Service Status**: API availability, TTS providers
- **Environment Checks**: API key validation
- **Readiness Probes**: Kubernetes compatibility

## 🔒 Security

- API key validation
- Input sanitization
- File upload restrictions
- Environment variable protection

## 📝 License

This project is licensed under the Evaluation License. See [EVALUATION-LICENSE.md](EVALUATION-LICENSE.md) for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   ```bash
   # Install FFmpeg
   sudo apt-get install ffmpeg  # Ubuntu/Debian
   brew install ffmpeg          # macOS
   ```

2. **API key errors**
   - Verify `.env` file exists and contains valid keys
   - Check API key permissions and quotas

3. **Audio processing failures**
   - Ensure audio file format is supported
   - Check file size limits
   - Verify FFmpeg installation

### Logs

```bash
# View application logs
docker logs <container-id>

# Local development logs
uvicorn app.main:app --log-level debug
```

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the [health endpoints documentation](HEALTH_ENDPOINTS.md)
- Review the API documentation at `/docs`

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Core transcription and translation features
- Multiple TTS provider support
- Docker containerization
- Health monitoring endpoints

---

**Made with ❤️ using FastAPI, OpenAI, and modern AI technologies**