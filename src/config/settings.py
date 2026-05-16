"""
配置管理 - OpenAI-compatible API (LM Studio / 任何兼容服務)
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ASR
    asr_model: str = Field(
        default="qwen3-asr-1.7b",
        description="ASR 模型 ID"
    )
    asr_api_url: str = Field(
        default="http://localhost:1234/v1",
        description="ASR API URL"
    )
    asr_api_key: Optional[str] = Field(
        default=None,
        description="API Key (如需要)"
    )
    
    # Translation
    translate_model: str = Field(
        default="qwen3.5-9b",
        description="翻譯模型 ID"
    )
    translate_api_url: str = Field(
        default="http://localhost:1234/v1",
        description="翻譯 API URL"
    )
    translate_api_key: Optional[str] = Field(
        default=None,
        description="API Key (如需要)"
    )
    
    # Audio source
    audio_source: str = Field(
        default="mic",
        description="Audio source: mic, system, per-app"
    )
    target_app: str = Field(
        default="",
        description="Target app name for per-app capture"
    )
    
    # VAD
    vad_rms_threshold: float = Field(default=150.0)
    vad_silence_duration: float = Field(default=1.5)
    vad_max_chunk_duration: float = Field(default=8.0)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/qwen_asr.log")
    
    def to_dict(self) -> dict:
        return {
            "asr_model": self.asr_model,
            "asr_api_url": self.asr_api_url,
            "asr_api_key": self.asr_api_key or "",
            "translate_model": self.translate_model,
            "translate_api_url": self.translate_api_url,
            "translate_api_key": self.translate_api_key or ""
        }


config = AppConfig()


def get_config() -> AppConfig:
    return config