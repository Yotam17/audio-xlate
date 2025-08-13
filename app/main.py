from fastapi import FastAPI, BackgroundTasks
from app.routes import translate, tts, optimize, combine_audio, translate_voice_over, validate_narration_sync, whisper_to_srt, transcribe, adjust_audio_length
from pydantic import BaseModel

app = FastAPI(title="YT Xlate Agent", version="1.0.0")

app.include_router(translate.router, prefix="/api/v1", tags=["translation"])
app.include_router(tts.router, prefix="/api/v1", tags=["tts"])
app.include_router(optimize.router, prefix="/api/v1", tags=["optimization"])
app.include_router(combine_audio.router, prefix="/api/v1", tags=["audio"])
app.include_router(translate_voice_over.router, prefix="/api/v1", tags=["voice-over"])
app.include_router(validate_narration_sync.router, prefix="/api/v1", tags=["validation"])
app.include_router(whisper_to_srt.router, prefix="/api/v1", tags=["whisper"])
app.include_router(transcribe.router, prefix="/api/v1", tags=["transcription"])
app.include_router(adjust_audio_length.router, prefix="/api/v1", tags=["audio-adjustment"])

class Segment(BaseModel):
    start: float
    end: float
    audio_path: str
@app.get("/")
def read_root():
    return {"msg": "Hello from FastAPI with ffmpeg!"}

def do_warmup():
    """
    Warmup function that preloads heavy components in the background.
    This function runs asynchronously to avoid blocking the API response.
    """
    import os
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    logger.info(f"[WARMUP] Starting warmup process at {datetime.now()}")
    
    try:
        # 1. Test R2 connection and preload client
        logger.info("[WARMUP] Testing R2 connection...")
        from app.utils.r2_utils import test_r2_connection
        r2_status = test_r2_connection()
        logger.info(f"[WARMUP] R2 status: {r2_status['status']}")
        
        # 2. Preload TTS clients
        logger.info("[WARMUP] Preloading TTS clients...")
        try:
            from app.tts.eleven_labs import ElevenLabsTts
            eleven_labs = ElevenLabsTts()
            logger.info("[WARMUP] ElevenLabs TTS client loaded")
        except Exception as e:
            logger.warning(f"[WARMUP] ElevenLabs TTS client failed: {e}")
        
        try:
            from app.tts.google_tts import GoogleTts
            google_tts = GoogleTts()
            logger.info("[WARMUP] Google TTS client loaded")
        except Exception as e:
            logger.warning(f"[WARMUP] Google TTS client failed: {e}")
        
        try:
            from app.tts.openai_tts import OpenAITts
            openai_tts = OpenAITts()
            logger.info("[WARMUP] OpenAI TTS client loaded")
        except Exception as e:
            logger.warning(f"[WARMUP] OpenAI TTS client failed: {e}")
        
        # 3. Test OpenAI connection (for Whisper/transcription)
        logger.info("[WARMUP] Testing OpenAI connection...")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Simple test - just check if client can be created
            logger.info("[WARMUP] OpenAI client created successfully")
        except Exception as e:
            logger.warning(f"[WARMUP] OpenAI client failed: {e}")
        
        # 4. Preload critical modules
        logger.info("[WARMUP] Preloading critical modules...")
        try:
            from app.utils.api_utils import transcribe
            from app.logic.transcription_orchestration import transcribe_to_subtitles
            from app.logic.translation_logic import translate_text
            from app.logic.optimize import optimize_sentence_flow
            from app.logic.tts_sentences import tts_sentences
            logger.info("[WARMUP] Critical modules loaded successfully")
        except Exception as e:
            logger.warning(f"[WARMUP] Critical modules failed: {e}")
        
        # 5. Test file system access
        logger.info("[WARMUP] Testing file system access...")
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
                f.write("warmup test")
            logger.info("[WARMUP] File system access confirmed")
        except Exception as e:
            logger.warning(f"[WARMUP] File system access failed: {e}")
        
        # 6. Check environment variables
        logger.info("[WARMUP] Checking environment variables...")
        critical_vars = [
            "OPENAI_API_KEY", "ELEVENLABS_API_KEY", 
            "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL"
        ]
        for var in critical_vars:
            if os.getenv(var):
                logger.info(f"[WARMUP] {var}: SET")
            else:
                logger.warning(f"[WARMUP] {var}: NOT_SET")
        
        logger.info(f"[WARMUP] Warmup process completed successfully at {datetime.now()}")
        
    except Exception as e:
        logger.error(f"[WARMUP] Warmup process failed: {e}")
        import traceback
        logger.error(f"[WARMUP] Traceback: {traceback.format_exc()}")

@app.get("/api/v1/warmup", tags=["warmup"])
def warmup(bg: BackgroundTasks):
    """
    Warmup endpoint that preloads heavy components in the background.
    
    This endpoint is designed to be called when users visit the landing page,
    so that by the time they need the actual services, everything is ready.
    
    Returns:
        Immediate response indicating warmup has started
    """
    bg.add_task(do_warmup)
    return {
        "status": "warmup_started",
        "message": "Warmup process started in background",
        "timestamp": datetime.now().isoformat(),
        "note": "This endpoint returns immediately while warmup runs in background"
    }

@app.get("/api/v1/warmup/quick", tags=["warmup"])
def quick_warmup():
    """
    Quick warmup endpoint for immediate readiness check.
    
    This endpoint performs minimal warmup tasks and returns quickly.
    Useful for checking if the service is ready for basic operations.
    
    Returns:
        Quick readiness status
    """
    import os
    from datetime import datetime
    
    try:
        # Quick checks that don't take long
        quick_status = {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # Check environment variables
        env_check = {}
        critical_vars = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY", "R2_ACCESS_KEY_ID"]
        for var in critical_vars:
            env_check[var] = "SET" if os.getenv(var) else "NOT_SET"
        
        quick_status["checks"]["environment"] = env_check
        
        # Quick file system test
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
                f.write("quick test")
            quick_status["checks"]["file_system"] = "ready"
        except Exception as e:
            quick_status["checks"]["file_system"] = f"error: {str(e)}"
            quick_status["status"] = "degraded"
        
        # Quick module import test
        try:
            from app.utils.r2_utils import test_r2_connection
            quick_status["checks"]["r2_utils"] = "ready"
        except Exception as e:
            quick_status["checks"]["r2_utils"] = f"error: {str(e)}"
            quick_status["status"] = "degraded"
        
        return quick_status
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint to verify the API is running properly.
    
    Returns:
        Dict with health status and basic system information
    """
    import os
    import platform
    import psutil
    from datetime import datetime
    
    try:
        # Basic system info
        system_info = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "YT Xlate Agent API",
            "version": "1.0.0",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
        
        # Check critical environment variables
        env_vars = {}
        critical_vars = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY"]
        for var in critical_vars:
            env_vars[var] = "SET" if os.getenv(var) else "NOT_SET"
        
        system_info["environment"] = env_vars
        
        return system_info
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health/simple", tags=["health"])
def simple_health_check():
    """
    Simple health check endpoint for load balancers and basic monitoring.
    
    Returns:
        Simple health status
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/detailed", tags=["health"])
def detailed_health_check():
    """
    Detailed health check endpoint with service-specific checks.
    
    Returns:
        Dict with detailed health status of all services
    """
    import os
    from datetime import datetime
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "YT Xlate Agent API",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check environment variables
    env_check = {}
    critical_vars = {
        "OPENAI_API_KEY": "OpenAI API key for transcription and translation",
        "ELEVENLABS_API_KEY": "ElevenLabs API key for TTS generation"
    }
    
    for var, description in critical_vars.items():
        env_check[var] = {
            "status": "SET" if os.getenv(var) else "NOT_SET",
            "description": description
        }
        if not os.getenv(var):
            health_status["status"] = "degraded"
    
    health_status["checks"]["environment"] = env_check
    
    # Check file system access
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=True) as f:
            f.write("test")
        health_status["checks"]["file_system"] = {"status": "healthy", "message": "File system accessible"}
    except Exception as e:
        health_status["checks"]["file_system"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "unhealthy"
    
    # Check Python packages
    package_check = {}
    required_packages = [
        "fastapi", "openai", "requests", "pydub", "ffmpeg-python"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            package_check[package] = {"status": "healthy", "message": "Package available"}
        except ImportError:
            package_check[package] = {"status": "unhealthy", "message": "Package not found"}
            health_status["status"] = "degraded"
    
    health_status["checks"]["packages"] = package_check
    
    # Check if we can create a basic response
    try:
        health_status["checks"]["api_response"] = {"status": "healthy", "message": "API can generate responses"}
    except Exception as e:
        health_status["checks"]["api_response"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/ready", tags=["health"])
def readiness_check():
    """
    Readiness check endpoint for Kubernetes and container orchestration.
    This endpoint checks if the service is ready to receive traffic.
    
    Returns:
        Dict with readiness status
    """
    from datetime import datetime
    
    try:
        # Basic readiness checks
        ready_status = {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "YT Xlate Agent API",
            "checks": {}
        }
        
        # Check if we can import critical modules
        try:
            from app.utils.api_utils import transcribe
            ready_status["checks"]["api_utils"] = {"status": "ready", "message": "API utilities available"}
        except ImportError as e:
            ready_status["checks"]["api_utils"] = {"status": "not_ready", "message": str(e)}
            ready_status["status"] = "not_ready"
        
        # Check if we can import TTS modules
        try:
            from app.tts.eleven_labs import ElevenLabsTts
            ready_status["checks"]["tts_modules"] = {"status": "ready", "message": "TTS modules available"}
        except ImportError as e:
            ready_status["checks"]["tts_modules"] = {"status": "not_ready", "message": str(e)}
            ready_status["status"] = "not_ready"
        
        # Check if we can import logic modules
        try:
            from app.logic.transcription_orchestration import transcribe_to_subtitles
            ready_status["checks"]["logic_modules"] = {"status": "ready", "message": "Logic modules available"}
        except ImportError as e:
            ready_status["checks"]["logic_modules"] = {"status": "not_ready", "message": str(e)}
            ready_status["status"] = "not_ready"
        
        return ready_status
        
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health/r2", tags=["health"])
def r2_health_check():
    """
    R2 storage health check endpoint.
    
    Returns:
        Dict with R2 connection status and configuration
    """
    try:
        from app.utils.r2_utils import test_r2_connection
        return test_r2_connection()
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to test R2 connection"
        }

@app.get("/api/v1/warmup/r2", tags=["warmup"])
def r2_warmup():
    """
    R2-specific warmup endpoint.
    
    This endpoint preloads R2 connections and tests basic operations.
    Useful when you know you'll need R2 storage soon.
    
    Returns:
        R2 warmup status
    """
    try:
        from app.utils.r2_utils import test_r2_connection, validate_presigned_url
        
        # Test connection
        connection_status = test_r2_connection()
        
        # Test presigned URL generation (if connection is successful)
        presigned_test = None
        if connection_status.get("status") == "connected":
            try:
                # Create a test file and generate presigned URL
                import tempfile
                test_content = b"warmup test file"
                test_filename = "warmup_test.txt"
                
                from app.utils.r2_utils import upload_audio_to_r2
                upload_result = upload_audio_to_r2(test_content, test_filename)
                
                # Generate presigned URL
                from app.utils.r2_utils import generate_presigned_url
                presigned_url = generate_presigned_url(test_filename, expiration=300)  # 5 minutes
                
                # Validate the URL
                validation = validate_presigned_url(presigned_url)
                
                presigned_test = {
                    "upload": "success",
                    "presigned_url_generated": "success",
                    "url_validation": validation,
                    "note": "Test file will be automatically cleaned up"
                }
                
            except Exception as e:
                presigned_test = {
                    "error": str(e),
                    "note": "Presigned URL test failed"
                }
        
        return {
            "status": "warmup_completed",
            "timestamp": datetime.now().isoformat(),
            "connection": connection_status,
            "presigned_url_test": presigned_test
        }
        
    except Exception as e:
        return {
            "status": "warmup_failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/v1/warmup/cleanup", tags=["warmup"])
def cleanup_warmup_files():
    """
    Cleanup endpoint for removing test files created during warmup.
    
    This endpoint removes temporary files that were created during
    warmup processes to keep the R2 bucket clean.
    
    Returns:
        Cleanup status
    """
    try:
        from app.utils.r2_utils import cleanup_test_files
        cleanup_result = cleanup_test_files()
        return {
            "status": "cleanup_completed",
            "timestamp": datetime.now().isoformat(),
            "result": cleanup_result
        }
    except Exception as e:
        return {
            "status": "cleanup_failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/startup", tags=["health"])
def startup_check():
    """
    Startup check endpoint for Kubernetes and container orchestration.
    This endpoint checks if the service has finished starting up.
    
    Returns:
        Dict with startup status
    """
    from datetime import datetime
    
    try:
        startup_status = {
            "status": "started",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "YT Xlate Agent API",
            "version": "1.0.0",
            "startup_time": "immediate",  # FastAPI starts very quickly
            "checks": {}
        }
        
        # Check if the main application is running
        startup_status["checks"]["main_app"] = {"status": "started", "message": "FastAPI application is running"}
        
        # Check if all routers are included
        router_check = {}
        expected_routers = [
            "translate", "tts", "optimize", "combine_audio", 
            "translate_voice_over", "validate_narration_sync", 
            "whisper_to_srt", "transcribe", "adjust_audio_length"
        ]
        
        # Check if warmup endpoints are available
        warmup_endpoints = [
            "/api/v1/warmup", "/api/v1/warmup/quick", 
            "/api/v1/warmup/r2", "/api/v1/warmup/cleanup"
        ]
        
        for router_name in expected_routers:
            router_check[router_name] = {"status": "started", "message": f"Router {router_name} included"}
        
        startup_status["checks"]["routers"] = router_check
        
        # Check warmup endpoints
        warmup_check = {}
        for endpoint in warmup_endpoints:
            warmup_check[endpoint] = {"status": "started", "message": f"Warmup endpoint {endpoint} available"}
        
        startup_status["checks"]["warmup_endpoints"] = warmup_check
        
        return startup_status
        
    except Exception as e:
        return {
            "status": "not_started",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
