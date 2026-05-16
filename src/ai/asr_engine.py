import numpy as np
import torch
from typing import Optional
from core.logging_config import get_logger

logger = get_logger(__name__)


class ASREngine:

    def __init__(self, model=None, api_url=None, api_key=None):
        self.model_path = model or "Qwen/Qwen3-ASR-1.7B"
        self.model = None
        self.loaded = False

    def load_model(self):
        if self.loaded:
            return

        logger.info(f"Loading {self.model_path}...")
        try:
            from qwen_asr import Qwen3ASRModel

            self.model = Qwen3ASRModel.from_pretrained(
                self.model_path,
                dtype=torch.bfloat16,
                device_map="cuda:0",
                max_new_tokens=256,
            )
            self.loaded = True
            logger.info("[OK] Qwen3-ASR loaded!")
        except Exception as e:
            logger.error(f"Model load failed: {e}", exc_info=True)

    def process_audio(self, audio, sample_rate=16000, language=None):
        if not self.loaded:
            self.load_model()

        if not self.loaded or self.model is None:
            return ""

        try:
            audio_np = np.asarray(audio, dtype=np.float32)
            logger.debug(f"ASR input: samples={len(audio_np)}, sr={sample_rate}")

            results = self.model.transcribe(
                audio=(audio_np, sample_rate),
                language=None,
            )

            if results and len(results) > 0:
                text = results[0].text.strip()
                if text:
                    logger.info(f"ASR: {text[:100]}")
                return text
            return ""

        except Exception as e:
            logger.error(f"ASR error: {e}", exc_info=True)
            return ""

    def unload_model(self):
        if self.model is not None:
            del self.model
            torch.cuda.empty_cache()
        self.loaded = False
        logger.info("ASR engine unloaded")