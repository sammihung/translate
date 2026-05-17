import requests
from typing import Optional, List, Dict
from core.logging_config import get_logger
from config.settings import config

logger = get_logger(__name__)


class TranslationEngine:

    def __init__(self, model=None, api_url=None, api_key=None, target_lang="zh"):
        self.model = model or config.translate_model
        self.api_url = api_url or config.translate_api_url
        self.api_key = api_key or config.translate_api_key
        self.target_lang = target_lang
        self.loaded = False
        self.history: List[str] = []
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})

        self.lang_map: Dict[str, str] = {
            "zh": "Traditional Chinese (繁體中文)",
            "en": "English",
            "ja": "Japanese",
            "ko": "Korean"
        }

    def load_model(self):
        if self.loaded:
            return

        logger.info(f"Connecting to Translation API: {self.api_url}")

        try:
            response = self.session.get(f"{self.api_url}/models", timeout=5)
            if response.status_code == 200:
                self.loaded = True
                logger.info(f"[OK] Translation API connected, model: {self.model}")
            else:
                logger.warning(f"Translation API 回應異常：{response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Translation API 無法連接：{self.api_url} (Is LM Studio running?)")
        except Exception as e:
            logger.error(f"Translation API 連接失敗：{e}")

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""

        if not self.loaded:
            self.load_model()

        if not self.loaded:
            logger.warning("翻譯 API 未連接")
            return text

        try:
            tgt_lang = self.lang_map.get(self.target_lang, "Traditional Chinese (繁體中文)")
            context = " ".join(self.history[-3:]) if self.history else "None"

            prompt = (
                f"Context: {context}\n\n"
                f"Translate to {tgt_lang}. Only output the translation, no explanations:\n\n{text}"
            )

            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 1024
            }

            response = self.session.post(
                f"{self.api_url}/chat/completions",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                translated = result["choices"][0]["message"]["content"].strip()

                self.history.append(text)
                if len(self.history) > 3:
                    self.history.pop(0)

                logger.debug(f"翻譯結果：{translated[:50]}...")
                return translated
            else:
                logger.warning(f"API 錯誤：{response.status_code}")
                return text

        except Exception as e:
            logger.error(f"翻譯錯誤：{e}")
            return text

    def unload_model(self):
        self.loaded = False
        self.history = []
        logger.info("翻譯引擎已卸載")