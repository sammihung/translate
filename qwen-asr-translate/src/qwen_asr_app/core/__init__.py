"""
核心層 - 日誌、模型註冊表
"""

from qwen_asr_app.core.logging_config import setup_logging, get_logger
from qwen_asr_app.core.model_registry import (
    PerformanceMode,
    PerformanceTier,
    get_performance_tier,
    get_all_tiers,
    get_tier_by_display_name,
    AVAILABLE_MODELS
)

__all__ = [
    "setup_logging",
    "get_logger",
    "PerformanceMode",
    "PerformanceTier",
    "get_performance_tier",
    "get_all_tiers",
    "get_tier_by_display_name",
    "AVAILABLE_MODELS"
]
