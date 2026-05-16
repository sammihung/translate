"""
配置層 - 環境變數、應用設定

使用 pydantic-settings 管理所有配置
"""

from config.settings import AppConfig, get_config, config

__all__ = ["AppConfig", "get_config", "config"]
