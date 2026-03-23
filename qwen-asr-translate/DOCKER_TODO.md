# Docker Migration TODO

## ✅ Completed

1. Created Dockerfiles:
   - `Dockerfile.app` - App container (UI + API, no torch)
   - `Dockerfile.cpu` - CPU worker (CPU-only torch)
   - `Dockerfile.gpu` - GPU worker (CUDA torch)

2. Updated `docker-compose.yml`:
   - App service (port 8000)
   - CPU worker service (port 8001)
   - GPU worker service (port 8001, GPU access)
   - Ollama service (port 11434)
   - Named volumes for model caching
   - Health checks for all services

3. Created new modules:
   - `src/qwen_asr_app/worker.py` - Worker API (FastAPI)
   - `src/qwen_asr_app/ai/worker_client.py` - Worker client + manager

4. Configuration files:
   - `.env.example` - Updated with worker URLs
   - `.dockerignore` - Optimized build
   - `README.Docker.md` - Full documentation
   - `docker-start.bat` - Quick start script

## 📋 Next Steps

### 1. Integrate Worker with Existing ASR Engine

**File**: `src/qwen_asr_app/worker.py`

Replace placeholder transcription logic with actual ASR engine:

```python
# In load_model()
from .ai.asr_engine import QwenASREngine

asr_engine = QwenASREngine(device=worker_device)
asr_engine.load_model()

# In transcribe_audio()
result = asr_engine.transcribe(audio_data)
```

### 2. Update App Controller to Use Worker Client

**File**: `src/qwen_asr_app/domain/controller.py`

Add worker manager initialization:

```python
from ..ai.worker_client import WorkerManager

class Controller:
    def __init__(self):
        self.worker_manager = WorkerManager()
    
    async def switch_device(self, device: str):
        return await self.worker_manager.switch_device(device)
    
    async def transcribe(self, audio_data: bytes):
        return await self.worker_manager.transcribe_with_fallback(audio_data)
```

### 3. Add Device Switch API to App

**File**: `src/qwen_asr_app/app.py` or main FastAPI app

Add endpoints:
```python
@app.post("/api/device")
async def switch_device(request: DeviceSwitchRequest):
    result = await controller.worker_manager.switch_device(request.device)
    return result

@app.get("/health")
async def health():
    return await controller.worker_manager.health_check_all()
```

### 4. Update UI for Device Selection

Add device selector dropdown in the UI that calls `/api/device` endpoint.

### 5. Test Locally

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Check logs
docker-compose logs -f cpu-worker
docker-compose logs -f gpu-worker

# Test health
curl http://localhost:8000/health

# Test device switch
curl -X POST http://localhost:8000/api/device \
  -H "Content-Type: application/json" \
  -d '{"device": "cpu"}'
```

### 6. Download Ollama Model

```bash
docker-compose exec ollama ollama pull translategemma:4b-it-q4_K_M
```

## 🎯 Benefits

1. **Smaller App Image** - No torch/CUDA in app container (~200MB vs ~5GB)
2. **Independent Scaling** - Can run multiple CPU/GPU workers
3. **Clean Separation** - UI logic separate from inference logic
4. **Easy Updates** - Update workers without touching app
5. **Resource Efficiency** - Stop GPU worker when not needed
6. **Flexible Deployment** - Deploy workers on different machines

## 📊 Image Sizes (Estimated)

- App: ~200MB
- CPU Worker: ~2GB
- GPU Worker: ~4GB
- Ollama: ~500MB + model size

## 🔧 Development Workflow

### Local Development (without Docker)
```bash
# Use existing setup
python main.py
```

### Docker Development
```bash
# Rebuild after code changes
docker-compose build cpu-worker
docker-compose up -d cpu-worker

# View logs
docker-compose logs -f cpu-worker
```

### Production
```bash
# Build optimized images
docker-compose build --no-cache

# Start with GPU
docker-compose up -d

# Monitor
docker-compose ps
watch -n 1 nvidia-smi
```

## ⚠️ Gotchas

1. **Model Download** - First run will download models (can take 10-30 min)
2. **GPU Drivers** - Ensure NVIDIA drivers are up to date
3. **Port Conflicts** - Check ports 8000, 8001, 11434 are free
4. **Disk Space** - Models cache can grow to 10GB+
5. **Windows WSL2** - May need to increase WSL2 memory limit

## 📚 References

- Docker Compose: https://docs.docker.com/compose/
- NVIDIA Container Toolkit: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/
- FastAPI: https://fastapi.tiangolo.com/
