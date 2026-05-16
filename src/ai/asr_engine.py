import numpy as np
import io
import requests
from typing import Optional
from core.logging_config import get_logger
from config.settings import config

logger = get_logger(__name__)


class ASREngine:

    def __init__(self, model=None, api_url=None, api_key=None):
        self.model = model or config.asr_model
        self.api_url = api_url or config.asr_api_url
        self.api_key = api_key or config.asr_api_key
        self.loaded = False
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

    def load_model(self):
        if self.loaded:
            return

        logger.info(f"Connecting to ASR API: {self.api_url}")

        try:
            response = self.session.get(f"{self.api_url}/models", timeout=5)
            if response.status_code == 200:
                self.loaded = True
                logger.info(f"[OK] API connected, model: {self.model}")
            else:
                logger.warning(f"API 回應異常：{response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"無法連接 API：{self.api_url}")
        except Exception as e:
            logger.error(f"API 連接失敗：{e}")

    def process_audio(self, audio, sample_rate=16000, language=None):
        if not self.loaded:
            self.load_model()

        if not self.loaded:
            logger.warning("ASR API 未連接")
            return ""

        try:
            audio = audio.astype(np.float32)

            if sample_rate != 16000:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=16000)

            wav_buffer = self._audio_to_wav_buffer(audio)

            response = self.session.post(
                f"{self.api_url}/audio/transcriptions",
                files={"file": ("audio.wav", wav_buffer, "audio/wav")},
                data={"model": self.model, "language": language or "auto"},
                timeout=60
            )

            if response.status_code == 200:
                text = response.json().get("text", "").strip()
                logger.debug(f"ASR 結果：{text[:100]}...")
                return text
            else:
                logger.warning(f"API 錯誤：{response.status_code} - {response.text[:200]}")
                return ""

        except Exception as e:
            logger.error(f"ASR 辨識錯誤：{e}", exc_info=True)
            return ""

    def _audio_to_wav_buffer(self, audio):
        import soundfile as sf

        buffer = io.BytesIO()
        sf.write(buffer, audio, 16000, format='WAV')
        buffer.seek(0)
        return buffer.read()

    def unload_model(self):
        self.loaded = False
        logger.info("ASR 引擎已卸載")