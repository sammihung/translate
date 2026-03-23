"""
API Gateway Server - HTTP API for Qwen ASR
Provides REST API for device switching and transcription
"""

import os
import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix UTF-8 encoding for logging on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Simple logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("qwen_asr_api")

# Create FastAPI app
app = FastAPI(
    title="Qwen ASR API",
    description="REST API for Qwen ASR Translate - Device switching and transcription",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
current_device = "cpu"
gpu_available = True
gpu_vram_gb = 8.0


# Request/Response Models

class DeviceSwitchRequest(BaseModel):
    device: str  # "cpu" or "cuda"


class DeviceStatus(BaseModel):
    status: str
    current_device: str
    cpu_available: bool
    gpu_available: bool
    gpu_vram_gb: Optional[float] = None


class HealthStatus(BaseModel):
    app: str
    workers: Dict[str, Any]


# API Endpoints

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check for all services"""
    return HealthStatus(
        app="healthy",
        workers={
            "cpu": {"status": "available", "url": os.getenv("CPU_WORKER_URL", "http://localhost:8001")},
            "gpu": {"status": "available" if gpu_available else "unavailable", "url": os.getenv("GPU_WORKER_URL", "http://localhost:8002")}
        }
    )


@app.get("/status", response_model=DeviceStatus)
async def get_status():
    """Get current device status"""
    return DeviceStatus(
        status="ok",
        current_device=current_device,
        cpu_available=True,
        gpu_available=gpu_available,
        gpu_vram_gb=gpu_vram_gb
    )


@app.post("/api/device")
async def switch_device(request: DeviceSwitchRequest):
    """Switch between CPU and GPU workers"""
    global current_device
    
    if request.device not in ["cpu", "cuda"]:
        raise HTTPException(status_code=400, detail="Invalid device. Must be 'cpu' or 'cuda'")
    
    if request.device == "cuda" and not gpu_available:
        raise HTTPException(status_code=400, detail="GPU not available")
    
    current_device = request.device
    logger.info(f"Device switched to: {request.device}")
    
    return {"status": "success", "device": request.device}


@app.get("/api/workers")
async def list_workers():
    """List available workers"""
    return {
        "cpu": {"status": "available", "device": "cpu"},
        "gpu": {"status": "available" if gpu_available else "unavailable", "device": "cuda"},
        "current": current_device
    }


@app.post("/api/transcribe")
async def transcribe_audio():
    """Placeholder for transcription"""
    return {"status": "placeholder", "message": "Transcription via worker not implemented yet"}


# Lifecycle Events

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting Qwen ASR API Gateway...")
    logger.info(f"  CPU Worker: {os.getenv('CPU_WORKER_URL', 'http://localhost:8001')}")
    logger.info(f"  GPU Worker: {os.getenv('GPU_WORKER_URL', 'http://localhost:8002')}")
    logger.info(f"  Default Device: {current_device}")
    logger.info("API Gateway started on port 8000")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API Gateway...")


# Main Entry Point

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server"""
    uvicorn.run(
        "qwen_asr_app.api_gateway:app",
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Qwen ASR API Gateway")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    run_server(host=args.host, port=args.port)