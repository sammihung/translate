# Docker Deployment Guide

## Architecture

This project uses a microservices architecture with 4 containers:

```
┌──────────────┐      ┌──────────────┐
│   App        │─────►│  CPU Worker  │
│  (Port 8000) │      │  (Port 8001) │
│  UI + API    │      │  ASR CPU     │
└──────┬───────┘      └──────────────┘
       │
       ├─────►┌──────────────┐
       │      │  GPU Worker  │
       │      │  (Port 8001) │
       │      │  ASR CUDA    │
       │      └──────────────┘
       │
       └─────►┌──────────────┐
              │   Ollama     │
              │  (Port 11434)│
              │  Translation │
              └──────────────┘
```

### Containers

1. **App** (`qwen_asr_app`)
   - Web UI and API gateway
   - Routes requests to CPU or GPU worker
   - Port: 8000

2. **CPU Worker** (`qwen_asr_cpu_worker`)
   - ASR inference on CPU only
   - Uses CPU-only PyTorch (smaller image)
   - Port: 8001

3. **GPU Worker** (`qwen_asr_gpu_worker`)
   - ASR inference with CUDA
   - Requires NVIDIA GPU
   - Port: 8001

4. **Ollama** (`ollama_server`)
   - Translation model serving
   - Port: 11434

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker + Docker Compose (Linux)
- NVIDIA GPU + NVIDIA Container Toolkit (for GPU worker)
- At least 8GB RAM (16GB recommended)
- 10GB free disk space

## Quick Start

### 1. Clone and Configure

```bash
cd qwen-asr-translate
cp .env.example .env
```

Edit `.env` to set your preferences:
```env
DEFAULT_DEVICE=cpu
PERFORMANCE_MODE=balanced
```

### 2. Build and Start

```bash
# Build all containers
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Access the App

Open your browser: http://localhost:8000

### 4. Stop Services

```bash
docker-compose down
```

## Device Switching

### Via UI
- Use the device selector in the app UI
- Switch between CPU and GPU on the fly

### Via API
```bash
# Check worker health
curl http://localhost:8000/health

# Switch to GPU
curl -X POST http://localhost:8000/api/device \
  -H "Content-Type: application/json" \
  -d '{"device": "cuda"}'

# Switch to CPU
curl -X POST http://localhost:8000/api/device \
  -H "Content-Type: application/json" \
  -d '{"device": "cpu"}'
```

## GPU Support

### Windows (Docker Desktop)
- Docker Desktop automatically enables GPU support
- Ensure WSL2 backend is enabled
- Install latest NVIDIA drivers

### Linux
1. Install NVIDIA Container Toolkit:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

2. Test GPU access:
```bash
docker-compose run --rm gpu-worker nvidia-smi
```

## Model Caching

Models are cached in Docker volumes:
- `cpu_models`: CPU worker model cache
- `gpu_models`: GPU worker model cache
- `ollama_data`: Ollama translation models

To clear caches:
```bash
docker-compose down -v  # WARNING: Deletes all volumes
```

## Logs

View logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f cpu-worker
docker-compose logs -f gpu-worker
docker-compose logs -f ollama
```

Log files are also mounted to `./logs` directory.

## Development

### Rebuild after code changes

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Run locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Run app
python main.py
```

## Troubleshooting

### GPU worker not starting
```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Out of memory
- Reduce model size in `.env`
- Close other GPU applications
- Use CPU worker instead

### Ollama model not found
```bash
# Pull the translation model
docker-compose exec ollama ollama pull translategemma:4b-it-q4_K_M
```

### Health check failing
```bash
# Check service status
docker-compose ps

# View specific service logs
docker-compose logs cpu-worker
```

## Performance Tips

1. **Use GPU for production** - 5-10x faster inference
2. **Keep models cached** - Don't delete volumes between runs
3. **Adjust batch size** - Larger batches = better GPU utilization
4. **Monitor VRAM** - Use `nvidia-smi` to track GPU memory

## Backup and Restore

### Backup model caches
```bash
docker run --rm -v qwen-asr-translate_cpu_models:/data -v $(pwd)/backup:/backup ubuntu tar czf /backup/cpu-models.tar.gz -C /data .
docker run --rm -v qwen-asr-translate_gpu_models:/data -v $(pwd)/backup:/backup ubuntu tar czf /backup/gpu-models.tar.gz -C /data .
```

### Restore model caches
```bash
docker run --rm -v qwen-asr-translate_cpu_models:/data -v $(pwd)/backup:/backup ubuntu tar xzf /backup/cpu-models.tar.gz -C /data
docker run --rm -v qwen-asr-translate_gpu_models:/data -v $(pwd)/backup:/backup ubuntu tar xzf /backup/gpu-models.tar.gz -C /data
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_DEVICE` | `cpu` | Default device (cpu/cuda) |
| `CPU_WORKER_URL` | `http://cpu-worker:8001` | CPU worker URL |
| `GPU_WORKER_URL` | `http://gpu-worker:8001` | GPU worker URL |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API URL |
| `PERFORMANCE_MODE` | `balanced` | fast/balanced/full |
| `ASR_MODEL` | `Qwen/Qwen3-ASR-1.7B` | ASR model name |

## Next Steps

1. Configure `.env` for your setup
2. Run `docker-compose up -d`
3. Open http://localhost:8000
4. Start transcribing!
