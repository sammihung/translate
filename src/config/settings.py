"""
配置管理 - pydantic-settings
支援 LM Studio 及 OpenAI-compatible API
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum


class BackendType(str, Enum):
    LM_STUDIO = "lm_studio"
    OPENAI_COMPAT = "openai_compat"
    CUSTOM = "custom"


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ASR
    asr_backend: BackendType = Field(
        default=BackendType.LM_STUDIO,
        description="ASR 後端 (lm_studio, openai_compat, custom)"
    )
    asr_model: str = Field(
        default="qwen3-asr-1.7b",
        description="ASR 模型 ID"
    )
    asr_api_url: str = Field(
        default="http://localhost:1234/v1",
        description="ASR API URL (LM Studio 預設)"
    )
    asr_api_key: Optional[str] = Field(
        default=None,
        description="ASR API Key (如需要)"
    )
    
    # Translation
    translate_backend: BackendType = Field(
        default=BackendType.LM_STUDIO,
        description="翻譯後端 (lm_studio, openai_compat, custom)"
    )
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
        description="翻譯 API Key (如需要)"
    )
    
    # Device
    device: str = Field(
        default="cuda",
        description="計算設備 (cuda, cpu)"
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
            "asr_backend": self.asr_backend.value,
            "asr_model": self.asr_model,
            "asr_api_url": self.asr_api_url,
            "translate_backend": self.translate_backend.value,
            "translate_model": self.translate_model,
            "translate_api_url": self.translate_api_url,
            "device": self.device
        }


config = AppConfig()


def get_config() -> AppConfig:
    return config