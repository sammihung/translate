import numpy as np
from typing import Optional
from core.logging_config import get_logger
from config.settings import config

logger = get_logger(__name__)


class ASREngine:

    def __init__(self, model=None, api_url=None, api_key=None):
        self.model_name = model or config.asr_model
        self.api_url = api_url
        self.api_key = api_key
        self.loaded = False

    def load_model(self):
        if self.loaded:
            return

        if not self.api_url:
            logger.warning("未設定 ASR API URL，請在設定中填寫")
            return

        self.loaded = True
        logger.info(f"ASR API mode: {self.api_url}, model: {self.model_name}")

    def process_audio(self, audio, sample_rate=16000, language=None):
        if not self.loaded:
            self.load_model()

        if not self.loaded:
            return ""

        try:
            audio = np.asarray(audio, dtype=np.float32)
            logger.debug(f"ASR input: samples={len(audio)}, sr={sample_rate}, dtype={audio.dtype}")

            if sample_rate != 16000:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=16000)

            return self._process_api(audio, language)

        except Exception as e:
            logger.error(f"ASR error: {e}", exc_info=True)

        return ""

    def _process_api(self, audio, language):
        import requests
        import io
        import soundfile as sf

        buffer = io.BytesIO()
        sf.write(buffer, audio, 16000, format='WAV')
        buffer.seek(0)

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        files = {
            "file": ("audio.wav", buffer, "audio/wav"),
        }
        data = {
            "model": self.model_name,
        }
        if language:
            data["language"] = language

        logger.debug(f"ASR request: POST {self.api_url}/audio/transcriptions, model={self.model_name}, lang={language or 'auto'}")

        try:
            resp = requests.post(
                f"{self.api_url}/audio/transcriptions",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            logger.debug(f"ASR response: status={resp.status_code}, body={resp.text[:200]}")

            if resp.status_code == 200:
                result = resp.json().get("text", "").strip()
                logger.info(f"ASR result: {result[:100]}")
                return result
            else:
                logger.error(f"ASR API error: {resp.status_code} {resp.text[:300]}")
        except Exception as e:
            logger.warning(f"ASR API failed: {e}", exc_info=True)

        return ""

    def unload_model(self):
        self.loaded = False
        logger.info("ASR engine unloaded")