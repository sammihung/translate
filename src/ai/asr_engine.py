import numpy as np
import torch
from typing import Optional
from core.logging_config import get_logger
from config.settings import config

logger = get_logger(__name__)


class ASREngine:

    def __init__(self, model=None, api_url=None, api_key=None):
        self.model_name = model or config.asr_model or "medium"
        self.api_url = api_url
        self.api_key = api_key
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.loaded = False
        self._model_type = None

    def load_model(self):
        if self.loaded:
            return

        # Priority: Whisper (reliable) -> Transformers -> API
        if self._load_whisper():
            return

        if self._load_transformers():
            return

        if self.api_url:
            self._model_type = "api"
            self.loaded = True
            logger.info("Using API mode")

    def _load_whisper(self):
        try:
            import whisper
            
            # Map model names
            model_size = self.model_name.lower()
            if "large" in model_size:
                model_size = "large-v3"
            elif "medium" in model_size or "whisper-medium" in model_size:
                model_size = "medium"
            elif "small" in model_size:
                model_size = "small"
            elif "base" in model_size:
                model_size = "base"
            elif "tiny" in model_size:
                model_size = "tiny"
            else:
                # Default based on VRAM
                if torch.cuda.is_available():
                    vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    model_size = "medium" if vram >= 5 else "small"
                else:
                    model_size = "small"
            
            logger.info(f"Loading Whisper {model_size} on {self.device}...")
            
            self.model = whisper.load_model(model_size, device=self.device)
            self._model_type = "whisper"
            self.loaded = True
            
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / (1024**3)
                logger.info(f"[OK] Whisper loaded, VRAM: {allocated:.1f}GB")
            else:
                logger.info(f"[OK] Whisper {model_size} loaded on CPU")
            
            return True

        except ImportError:
            logger.error("whisper not installed: pip install openai-whisper")
            return False
        except Exception as e:
            logger.error(f"Whisper load failed: {e}")
            return False

    def _load_transformers(self):
        try:
            from transformers import AutoModel, AutoProcessor
            
            model_name = self.model_name
            if "whisper" in model_name.lower():
                model_name = "openai/whisper-medium"
            
            logger.info(f"Loading Transformers: {model_name}")
            
            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            
            if self.device == "cuda":
                self.model = self.model.cuda()
            
            self.model.eval()
            self._model_type = "transformers"
            self.loaded = True
            logger.info("[OK] Transformers model loaded")
            return True

        except Exception as e:
            logger.warning(f"Transformers load failed: {e}")
            return False

    def process_audio(self, audio, sample_rate=16000, language=None):
        if not self.loaded:
            self.load_model()

        if not self.loaded:
            return ""

        try:
            audio = np.asarray(audio, dtype=np.float32)

            if sample_rate != 16000:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=16000)

            if self._model_type == "whisper":
                return self._process_whisper(audio, language)
            elif self._model_type == "transformers":
                return self._process_transformers(audio, language)
            elif self._model_type == "api":
                return self._process_api(audio, language)

        except Exception as e:
            logger.error(f"ASR error: {e}")
        
        return ""

    def _process_whisper(self, audio, language):
        try:
            # Whisper expects float32 audio
            result = self.model.transcribe(
                audio,
                language=language,
                fp16=self.device == "cuda",
                temperature=0.0,
                best_of=1,
                condition_on_previous_text=False
            )
            
            text = result.get("text", "").strip()
            if text:
                logger.debug(f"ASR: {text[:80]}...")
            return text
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return ""

    def _process_transformers(self, audio, language):
        try:
            with torch.no_grad():
                inputs = self.processor(
                    audio=audio,
                    sampling_rate=16000,
                    return_tensors="pt"
                )
                
                if self.device == "cuda":
                    inputs = {k: v.cuda() for k, v in inputs.items()}
                
                output_ids = self.model.generate(**inputs, max_new_tokens=256)
                text = self.processor.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
                
                return text
                
        except Exception as e:
            logger.error(f"Transformers transcription failed: {e}")
            return ""

    def _process_api(self, audio, language):
        import requests
        import io
        import soundfile as sf
        
        buffer = io.BytesIO()
        sf.write(buffer, audio, 16000, format='WAV')
        buffer.seek(0)
        
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        
        try:
            resp = requests.post(
                f"{self.api_url}/audio/transcriptions",
                files={"file": ("audio.wav", buffer, "audio/wav")},
                data={"model": self.model_name, "language": language or ""},
                headers=headers,
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get("text", "").strip()
        except Exception as e:
            logger.warning(f"API failed: {e}")
        
        return ""

    def unload_model(self):
        if self.model is not None:
            del self.model
            self.model = None
        
        if hasattr(self, 'processor'):
            del self.processor
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.loaded = False
        logger.info("ASR model unloaded")