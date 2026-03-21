"""
企業級配置管理 - 使用 pydantic-settings

所有配置都應該從呢個 Config 物件注入，唔應該寫死喺代碼入面。
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum


class PerformanceMode(str, Enum):
    """效能模式列舉"""
    FAST = "fast"
    BALANCED = "balanced"
    FULL = "full"


class AppConfig(BaseSettings):
    """
    應用程式配置
    
    所有配置優先級：
    1. 環境變數 (最高優先級)
    2. .env 文件
    3. 預設值 (最低優先級)
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 忽略未定義嘅環境變數
    )
    
    # =========================================================================
    # AI 模型配置
    # =========================================================================
    
    asr_model_name: str = Field(
        default="Qwen/Qwen3-ASR-1.7B",
        description="ASR 模型名稱 (HuggingFace repo)"
    )
    
    asr_device: str = Field(
        default="cuda",
        description="ASR 設備 (cuda, cpu)"
    )
    
    asr_use_int8: bool = Field(
        default=True,
        description="是否使用 INT8 量化 (節省 VRAM)"
    )
    
    translate_model_name: str = Field(
        default="translategemma:4b-it-q4_K_M",
        description="翻譯模型名稱 (Ollama)"
    )
    
    ollama_api_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API URL"
    )
    
    ollama_timeout: int = Field(
        default=60,
        description="Ollama API 超時時間 (秒)"
    )
    
    # =========================================================================
    # VAD 配置
    # =========================================================================
    
    vad_rms_threshold: float = Field(
        default=150.0,
        description="VAD RMS 靜音閾值"
    )
    
    vad_silence_duration: float = Field(
        default=1.5,
        description="VAD 靜音持續時間 (秒)"
    )
    
    vad_max_chunk_duration: float = Field(
        default=8.0,
        description="VAD 最大切片時長 (秒)"
    )
    
    # =========================================================================
    # 效能配置
    # =========================================================================
    
    performance_mode: PerformanceMode = Field(
        default=PerformanceMode.BALANCED,
        description="效能模式 (fast, balanced, full)"
    )
    
    translate_pool_max_workers: int = Field(
        default=3,
        description="翻譯 Thread Pool 最大工作數"
    )
    
    # =========================================================================
    # HuggingFace 配置
    # =========================================================================
    
    hf_token: Optional[str] = Field(
        default=None,
        description="HuggingFace Token (用於 Speaker Diarization)"
    )
    
    use_speaker_diarization: bool = Field(
        default=False,
        description="是否啟用說話者分離"
    )
    
    # =========================================================================
    # 日誌配置
    # =========================================================================
    
    log_level: str = Field(
        default="INFO",
        description="日誌級別 (DEBUG, INFO, WARNING, ERROR)"
    )
    
    log_file: str = Field(
        default="logs/qwen_asr.log",
        description="日誌文件路徑"
    )
    
    log_max_bytes: int = Field(
        default=10485760,  # 10MB
        description="日誌文件最大大小 (bytes)"
    )
    
    log_backup_count: int = Field(
        default=5,
        description="日誌備份數量"
    )
    
    # =========================================================================
    # UI 配置
    # =========================================================================
    
    ui_theme: str = Field(
        default="dark",
        description="UI 主題 (dark, light)"
    )
    
    ui_accent_color: str = Field(
        default="#3b82f6",
        description="UI 強調色"
    )
    
    ui_language: str = Field(
        default="zh_TW",
        description="UI 語言 (zh_TW, en_US)"
    )
    
    # =========================================================================
    # 輔助方法
    # =========================================================================
    
    @property
    def gpu_vram_limit_gb(self) -> float:
        """根據效能模式返回 VRAM 限制"""
        limits = {
            PerformanceMode.FAST: 4.0,
            PerformanceMode.BALANCED: 8.0,
            PerformanceMode.FULL: 16.0
        }
        return limits.get(self.performance_mode, 8.0)
    
    @property
    def batch_max_chars(self) -> int:
        """Batching 最大字數"""
        return 50
    
    @property
    def batch_timeout(self) -> float:
        """Batching 超時時間 (秒)"""
        return 1.0
    
    def to_dict(self) -> dict:
        """轉換為字典 (用於日誌記錄)"""
        return {
            "asr_model": self.asr_model_name,
            "asr_device": self.asr_device,
            "asr_int8": self.asr_use_int8,
            "translate_model": self.translate_model_name,
            "performance_mode": self.performance_mode.value,
            "vad_threshold": self.vad_rms_threshold,
            "log_level": self.log_level,
        }


# 全域配置實例 (Singleton)
# 使用方法：from qwen_asr.config import config
config = AppConfig()


def get_config() -> AppConfig:
    """獲取配置實例 (Dependency Injection)"""
    return config
