"""
Worker Client - HTTP client for communicating with ASR workers
"""

import os
import logging
from typing import Optional, Dict, Any
import httpx
import base64

logger = logging.getLogger(__name__)


class WorkerClient:
    """Client for communicating with ASR worker containers"""
    
    def __init__(self, worker_url: str, timeout: float = 60.0):
        self.worker_url = worker_url.rstrip('/')
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check worker health status"""
        try:
            response = await self._client.get(f"{self.worker_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get worker status"""
        try:
            response = await self._client.get(f"{self.worker_url}/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return {"error": str(e)}
    
    async def load_model(self, device: Optional[str] = None, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Load model on worker"""
        try:
            params = {}
            if device:
                params['device'] = device
            if model_name:
                params['model_name'] = model_name
            
            response = await self._client.post(
                f"{self.worker_url}/load-model",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def unload_model(self) -> Dict[str, Any]:
        """Unload model from worker"""
        try:
            response = await self._client.post(f"{self.worker_url}/unload-model")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Model unload failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def transcribe(self, audio_data: bytes, sample_rate: int = 16000, language: str = "auto") -> Dict[str, Any]:
        """Transcribe audio data"""
        try:
            # Encode audio as base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            response = await self._client.post(
                f"{self.worker_url}/transcribe",
                json={
                    "audio_data": audio_base64,
                    "sample_rate": sample_rate,
                    "language": language
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """Close HTTP client"""
        await self._client.aclose()


class WorkerManager:
    """Manages multiple ASR workers (CPU and GPU)"""
    
    def __init__(self):
        self.cpu_url = os.getenv("CPU_WORKER_URL", "http://localhost:8001")
        self.gpu_url = os.getenv("GPU_WORKER_URL", "http://localhost:8002")
        self.default_device = os.getenv("DEFAULT_DEVICE", "cpu")
        
        self.cpu_client = WorkerClient(self.cpu_url)
        self.gpu_client = WorkerClient(self.gpu_url)
        self.current_device = self.default_device
    
    def get_client(self, device: Optional[str] = None) -> WorkerClient:
        """Get worker client for specified device"""
        if device == "cuda":
            return self.gpu_client
        return self.cpu_client
    
    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all workers"""
        cpu_health = await self.cpu_client.health_check()
        gpu_health = await self.gpu_client.health_check()
        
        return {
            "cpu": cpu_health,
            "gpu": gpu_health,
            "current": self.current_device
        }
    
    async def switch_device(self, device: str) -> Dict[str, Any]:
        """Switch to specified device"""
        if device not in ["cpu", "cuda"]:
            return {"error": "Invalid device. Must be 'cpu' or 'cuda'"}
        
        client = self.get_client(device)
        status = await client.health_check()
        
        if status.get("status") == "healthy":
            self.current_device = device
            logger.info(f"Switched to {device} worker")
            return {"status": "success", "device": device}
        else:
            return {"error": f"{device} worker not healthy", "details": status}
    
    async def transcribe_with_fallback(self, audio_data: bytes, **kwargs) -> Dict[str, Any]:
        """Transcribe with automatic fallback"""
        # Try current device first
        client = self.get_client(self.current_device)
        result = await client.transcribe(audio_data, **kwargs)
        
        if "error" not in result:
            return result
        
        # Fallback to other device
        fallback_device = "cuda" if self.current_device == "cpu" else "cpu"
        logger.warning(f"{self.current_device} failed, trying {fallback_device}")
        
        fallback_client = self.get_client(fallback_device)
        return await fallback_client.transcribe(audio_data, **kwargs)
    
    async def close_all(self):
        """Close all clients"""
        await self.cpu_client.close()
        await self.gpu_client.close()
