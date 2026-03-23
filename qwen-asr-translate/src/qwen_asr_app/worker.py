"""
ASR Worker API - HTTP interface for ASR inference
Runs in CPU or GPU worker containers
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ASR Worker", version="1.0.0")

# Worker state
worker_device = os.getenv("WORKER_DEVICE", "cpu")
model_loaded = False
asr_engine = None


class HealthResponse(BaseModel):
    status: str
    device: str
    model_loaded: bool
    gpu_available: bool
    gpu_vram_gb: Optional[float] = None


class TranscribeRequest(BaseModel):
    audio_data: str  # base64 encoded audio
    sample_rate: int = 16000
    language: str = "auto"


class TranscribeResponse(BaseModel):
    text: str
    language: str
    duration: float
    device_used: str


class DeviceSwitchRequest(BaseModel):
    device: str  # "cpu" or "cuda"
    model_name: Optional[str] = None


@app.get("/health")
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    gpu_available = torch.cuda.is_available()
    gpu_vram = None
    
    if gpu_available:
        try:
            gpu_vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except Exception:
            pass
    
    return HealthResponse(
        status="healthy",
        device=worker_device,
        model_loaded=model_loaded,
        gpu_available=gpu_available,
        gpu_vram_gb=gpu_vram
    )


@app.get("/status")
async def get_status():
    """Get detailed worker status"""
    return {
        "device": worker_device,
        "model_loaded": model_loaded,
        "gpu_available": torch.cuda.is_available(),
        "torch_version": torch.__version__,
    }


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    """Transcribe audio data"""
    global model_loaded, asr_engine
    
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # TODO: Implement actual transcription logic
        # This is a placeholder - will be replaced with real ASR engine
        result = {
            "text": "[Transcription placeholder]",
            "language": request.language,
            "duration": 0.0,
            "device_used": worker_device
        }
        
        logger.info(f"Transcription completed on {worker_device}")
        return TranscribeResponse(**result)
    
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load-model")
async def load_model(device: Optional[str] = None, model_name: Optional[str] = None):
    """Load or reload ASR model"""
    global model_loaded, asr_engine, worker_device
    
    if device:
        worker_device = device
    
    try:
        # TODO: Implement actual model loading
        # This is a placeholder - will be replaced with real ASR engine
        model_loaded = True
        
        logger.info(f"Model loaded on {worker_device}")
        return {"status": "success", "device": worker_device}
    
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/unload-model")
async def unload_model():
    """Unload ASR model to free memory"""
    global model_loaded, asr_engine
    
    try:
        # TODO: Implement actual model unloading
        model_loaded = False
        
        if worker_device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Model unloaded")
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Model unloading failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize worker on startup"""
    logger.info(f"Starting ASR Worker on {worker_device}")
    logger.info(f"Torch version: {torch.__version__}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    # Auto-load model on startup
    try:
        await load_model()
    except Exception as e:
        logger.warning(f"Failed to auto-load model: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down ASR Worker")
    if worker_device == "cuda" and torch.cuda.is_available():
        torch.cuda.empty_cache()
