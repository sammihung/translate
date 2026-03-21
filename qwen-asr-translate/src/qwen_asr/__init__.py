"""
Qwen ASR Translate - 企業級語音翻譯系統

Real-time ASR translation with Qwen3 and Ollama
"""

__version__ = "1.0.0"
__author__ = "Qwen ASR Team"

# 只暴露輕量級配置，避免載入 PyTorch 等重型套件
from qwen_asr.config.settings import AppConfig, get_config

__all__ = ["AppConfig", "get_config"]
