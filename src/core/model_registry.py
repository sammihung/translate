"""
模型配置註冊表 - Model Registry
用戶可自定義模型配置，連接 LM Studio 或其他 OpenAI-compatible 服務
"""

from typing import Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class BackendType(Enum):
    LM_STUDIO = "lm_studio"
    OPENAI_COMPAT = "openai_compat"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    name: str
    model_id: str
    backend: BackendType
    api_url: str = ""
    api_key: str = ""
    description: str = ""


@dataclass
class AppConfig:
    asr_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        name="Qwen3-ASR-1.7B",
        model_id="qwen3-asr-1.7b",
        backend=BackendType.LM_STUDIO,
        api_url="http://localhost:1234/v1",
        description="語音辨識模型"
    ))
    
    translate_model: ModelConfig = field(default_factory=lambda: ModelConfig(
        name="Qwen3.5-9B",
        model_id="qwen3.5-9b",
        backend=BackendType.LM_STUDIO,
        api_url="http://localhost:1234/v1",
        description="翻譯模型"
    ))
    
    device: str = "cuda"
    
    def to_dict(self) -> dict:
        return {
            "asr_model": self.asr_model.model_id,
            "translate_model": self.translate_model.model_id,
            "backend": self.asr_model.backend.value,
            "api_url": self.asr_model.api_url,
            "device": self.device
        }


DEFAULT_CONFIG = AppConfig()

DEFAULT_BACKENDS = {
    BackendType.LM_STUDIO: {
        "name": "LM Studio",
        "default_url": "http://localhost:1234/v1",
        "requires_key": False
    },
    BackendType.OPENAI_COMPAT: {
        "name": "OpenAI Compatible",
        "default_url": "",
        "requires_key": True
    },
    BackendType.CUSTOM: {
        "name": "Custom API",
        "default_url": "",
        "requires_key": False
    }
}