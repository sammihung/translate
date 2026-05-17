"""
配置管理 - Qwen3-ASR 本地推理
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ASR Model (local inference)
    asr_model: Literal["Qwen/Qwen3-ASR-1.7B", "Qwen/Qwen3-ASR-0.6B", "Qwen/Qwen3-ASR-1.7B-8bit"] = Field(
        default="Qwen/Qwen3-ASR-1.7B",
        description="ASR model: Qwen/Qwen3-ASR-1.7B, Qwen/Qwen3-ASR-0.6B, or Qwen/Qwen3-ASR-1.7B-8bit"
    )
    
    # Translation (LM Studio API)
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
    
    # VAD (Silero)
    vad_silence_duration: float = Field(default=0.8)
    vad_speech_duration: float = Field(default=2.0)
    vad_max_chunk_duration: float = Field(default=4.0)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/qwen_asr.log")
    
    def to_dict(self) -> dict:
        return {
            "asr_model": self.asr_model,
            "translate_model": self.translate_model,
            "translate_api_url": self.translate_api_url,
            "translate_api_key": self.translate_api_key or ""
        }


config = AppConfig()


def get_config() -> AppConfig:
    return config