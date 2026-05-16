"""
日誌配置模組 - Structured Logging Configuration
提供統一的日誌管理，替代所有 print() 呼叫
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    log_format: str = "detailed",
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    設置日誌系統
    
    Args:
        log_dir: 日誌檔案目錄
        log_level: 日誌級別 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 日誌格式 ("simple" | "detailed" | "json")
        console_output: 是否輸出到控制台
        file_output: 是否輸出到檔案
        
    Returns:
        配置好的 logger 物件
    """
    # 創建日誌目錄
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 生成日誌檔案名稱 (包含日期)
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = log_path / f"qwen_asr_{date_str}.log"
    
    # 獲取根 logger
    logger = logging.getLogger("qwen_asr")
    logger.setLevel(log_level)
    
    # 清除現有的 handlers (避免重複)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 定義日誌格式
    if log_format == "simple":
        formatter = logging.Formatter(
            "%(levelname)s: %(message)s",
            datefmt="%H:%M:%S"
        )
    elif log_format == "json":
        # JSON 格式需要額外安裝 python-json-logger
        try:
            from pythonjsonlogger import jsonlogger
            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        except ImportError:
            # 如果沒有安裝，退回使用詳細格式
            formatter = _get_detailed_formatter()
    else:  # detailed
        formatter = _get_detailed_formatter()
    
    # 添加控制台 Handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加檔案 Handler (自動輪轉)
    if file_output:
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,  # 保留 5 個舊檔案
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 添加異常處理 Hook (自動記錄未捕獲的異常)
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            return
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception
    
    logger.info(f"日誌系統已初始化，日誌檔：{log_file}")
    return logger


def _get_detailed_formatter() -> logging.Formatter:
    """獲取詳細的日誌格式"""
    return logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)-8s | "
        "%(pathname)s:%(lineno)d | %(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    獲取子模組 logger
    
    Args:
        name: 模組名稱 (通常使用 __name__)
        
    Returns:
        配置好的 logger 物件
    """
    if name is None:
        return logging.getLogger("qwen_asr")
    
    return logging.getLogger(f"qwen_asr.{name}")


# 快速訪問函數 (可選，方便遷移)
def debug(msg: str, *args, **kwargs):
    """記錄 DEBUG 級別日誌"""
    logger = get_logger()
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """記錄 INFO 級別日誌"""
    logger = get_logger()
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """記錄 WARNING 級別日誌"""
    logger = get_logger()
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """記錄 ERROR 級別日誌"""
    logger = get_logger()
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """記錄 CRITICAL 級別日誌"""
    logger = get_logger()
    logger.critical(msg, *args, **kwargs)


# 如果使用 loguru (可選)
def setup_loguru(log_dir: str = "logs", level: str = "DEBUG"):
    """
    使用 loguru 設置日誌 (更現代的替代方案)
    
    安裝：pip install loguru
    
    Args:
        log_dir: 日誌檔案目錄
        level: 日誌級別
    """
    try:
        from loguru import logger
        
        # 移除預設 handler
        logger.remove()
        
        # 添加控制台 handler
        logger.add(
            sys.stdout,
            level=level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True
        )
        
        # 添加檔案 handler (自動輪轉)
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path / "qwen_asr_{time:YYYYMMDD}.log",
            level=level,
            rotation="10 MB",
            retention=5,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            encoding="utf-8"
        )
        
        logger.info("Loguru 日誌系統已初始化")
        return logger
        
    except ImportError:
        print("[WARNING] loguru 未安裝，使用標準 logging 模組")
        return setup_logging(log_dir=log_dir)
