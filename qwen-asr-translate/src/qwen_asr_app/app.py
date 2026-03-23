"""
QwenASR Pro - YouTube Edition
主應用程式入口

架構分層：
- UI Layer (ui.py) - 使用者介面組件
- Controller Layer (controller.py) - 業務邏輯調控
- Model Layer (ai_controller.py, audio_manager.py) - 數據和模型
"""

import customtkinter as ctk
import threading
import sys
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from tkinter import messagebox
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from qwen_asr_app.ui.ui import MainUI
from qwen_asr_app.domain.controller import AppController
from qwen_asr_app.core.logging_config import setup_logging, get_logger
import logging
# 抑制 Transformers 過度輸出
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

# 初始化日誌系統
logger = setup_logging(
    log_dir="logs",
    log_level=logging.INFO,
    console_output=True,
    file_output=True
)


class App(ctk.CTk):
    """主應用程式 - 連接 UI 和 Controller"""
    
    def __init__(self) -> None:
        super().__init__()
        
        self.title("QwenASR Pro - YouTube Edition")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        
        # 創建控制器
        self.controller: AppController = AppController()
        
        # 創建 UI
        self.ui: MainUI = MainUI(self)
        self.ui.pack(fill="both", expand=True)
        
        # 連接 UI 回調
        self.ui.on_record_toggle: Optional[Callable] = self._on_record_toggle
        self.ui.on_upload_file: Optional[Callable] = self._on_upload_file
        self.ui.on_clear_history: Optional[Callable] = self._on_clear_history
        self.ui.on_translate_click: Optional[Callable] = self._on_translate_click
        self.ui.on_save_subtitle: Optional[Callable] = self._on_save_subtitle
        self.ui.on_settings_open: Optional[Callable] = self._on_settings_open
        
        # 連接 Controller 回調
        self.controller.on_subtitle_update = self._on_subtitle_update
        self.controller.on_translation_complete = self._on_translation_complete
        self.controller.on_status_change = self._on_status_change
        
        # 綁定語言切換事件
        self.ui.src_lang_combo.configure(command=self._on_lang_change)
        self.ui.tgt_lang_combo.configure(command=self._on_lang_change)
        
        # 處理關閉事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化
        self.after(500, self._initialize)
        
        logger.info("應用程式已啟動")
    
    def _on_lang_change(self, choice: str) -> None:
        """處理語言切換"""
        src: str
        tgt: str
        src, tgt = self.ui.get_selected_languages()
        self.controller.src_lang = src
        self.controller.tgt_lang = tgt
        
        # 關鍵修復：直接將目標語言 (tgt) 更新入去 Ollama 翻譯引擎度
        if hasattr(self.controller, 'ai_ctrl') and self.controller.ai_ctrl.translate_engine:
            self.controller.ai_ctrl.translate_engine.target_lang = tgt
            
        logger.info(f"語言已切換：來源={src}, 目標={tgt}")
    
    def _initialize(self) -> None:
        """初始化應用程式 - 統一由 Controller 決定模式"""
        try:
            # 更新設備列表
            devices: list[str] = self.controller.get_audio_devices()
            self.ui.set_device_list(devices)
            
            # ✅ 直接從 Controller 獲取已經判定好的模式並更新 UI
            asr_repo, translate_model = self.controller.get_current_model_config()
            tier_name = self.controller.current_tier.display_name
            
            # 尋找 UI 中對應的顯示名稱
            for display_name, repo in self.ui.asr_repo_map.items():
                if repo == asr_repo:
                    self.ui.asr_model_var.set(display_name)
                    break
            
            # 同步翻譯模型
            for display_name, model in self.ui.translate_map.items():
                if model == translate_model:
                    self.ui.translate_model_var.set(display_name)
                    break
            
            # 同步計算設備
            if self.controller.has_gpu:
                self.ui.compute_device_var.set("🚀 CUDA (Nvidia GPU)")
            else:
                self.ui.compute_device_var.set("💻 CPU (通用，相容性高)")
            
            logger.info(f"UI 已同步 Controller 效能模式：{tier_name}")
            
            # 啟動引擎載入
            self.ui.set_status("[LOADING] 正在載入引擎...", "#f59e0b")
            
            def load_engines() -> None:
                """背景載入引擎 - 添加詳細錯誤日誌"""
                try:
                    def progress_callback(status: str) -> None:
                        self.ui.set_status(status, "#f59e0b")
                    
                    logger.info("開始初始化引擎...")
                    success: bool = self.controller.initialize_engines(
                        progress_callback=progress_callback
                    )
                    
                    if success:
                        logger.info("引擎初始化成功，啟用錄音按鈕")
                        self.ui.set_status("[OK] 所有引擎已就緒", "#10b981")
                        self.ui.enable_record_button(True)
                    else:
                        logger.error("引擎初始化失敗 (success=False)")
                        self.ui.set_status("[ERROR] 引擎初始化失敗", "#ef4444")
                        self.ui.enable_record_button(False)
                except Exception as e:
                    logger.error(f"引擎初始化異常：{e}", exc_info=True)
                    self.ui.set_status(f"[ERROR] {str(e)}", "#ef4444")
                    self.ui.enable_record_button(False)
            
            threading.Thread(target=load_engines, daemon=True).start()
            
        except Exception as e:
            logger.error(f"初始化失敗：{e}", exc_info=True)
            self.ui.set_status(f"[ERROR] {str(e)}", "#ef4444")
    
    def _on_record_toggle(self) -> None:
        """切換錄音"""
        try:
            if self.controller.is_recording:
                self._stop_recording()
            else:
                self._start_recording()
        except Exception as e:
            logger.error(f"錄音切換失敗：{e}", exc_info=True)
            messagebox.showerror("錯誤", f"錄音操作失敗：{str(e)}")
    
    def _start_recording(self) -> None:
        """開始錄音"""
        try:
            if not self.controller.is_engines_ready():
                messagebox.showwarning("警告", "引擎尚未完全載入，請稍候...")
                return
            
            # 🔧 FIX: 使用安全的方法獲取設備名稱，避免 StringVar 不同步
            device_name: str = self.ui.get_selected_device()
            device_index: Optional[int] = self.controller.audio_mgr.parse_device_index(device_name)
            
            if self.controller.start_recording(device_index):
                self.ui.update_record_state(True)
                logger.info("開始錄音")
            else:
                messagebox.showerror("錯誤", "啟動錄音失敗，請檢查音訊設備")
                logger.error("啟動錄音失敗")
        except Exception as e:
            logger.error(f"開始錄音失敗：{e}", exc_info=True)
            messagebox.showerror("錯誤", f"無法開始錄音：{str(e)}")
    
    def _stop_recording(self) -> None:
        """停止錄音"""
        try:
            self.controller.stop_recording()
            self.ui.update_record_state(False)
            logger.info("停止錄音")
        except Exception as e:
            logger.error(f"停止錄音失敗：{e}", exc_info=True)
    
    def _on_subtitle_update(self, original: str, translated: str, speaker_id: int) -> str:
        """字幕更新回調 (注意：現在會回傳 bubble_id)"""
        try:
            speaker_name: str = f"SPEAKER #{speaker_id}"
            logger.info(f"💬 [_on_subtitle_update] 調用 add_chat_bubble，原文：'{original[:50]}...'")
            bubble_id: str = self.ui.add_chat_bubble(speaker_name, original, translated, speaker_id)
            logger.info(f"✅ [_on_subtitle_update] 成功，bubble_id={bubble_id}")
            return bubble_id
        except Exception as e:
            logger.error(f"❌ [_on_subtitle_update] 失敗：{e}", exc_info=True)
            return ""
        
    def _on_translation_complete(self, bubble_id: str, translated: str) -> None:
        """背景翻譯完成回調"""
        try:
            self.ui.update_chat_bubble(bubble_id, translated)
            logger.debug(f"翻譯完成：{translated[:50]}...")
        except Exception as e:
            logger.error(f"更新翻譯失敗：{e}", exc_info=True)
    
    def _on_status_change(self, status: str, color: str) -> None:
        """狀態變化回調"""
        try:
            self.ui.set_status(status, color)
        except Exception as e:
            logger.error(f"更新狀態失敗：{e}", exc_info=True)
    
    def _on_clear_history(self) -> None:
        """清空歷史記錄"""
        try:
            self.controller.clear_history()
            self.ui.clear_history()
            self.ui.show_info("完成", "歷史記錄已清空")
            logger.info("歷史記錄已清空")
        except Exception as e:
            logger.error(f"清空歷史失敗：{e}", exc_info=True)
    
    def _on_upload_file(self) -> None:
        """上傳檔案進行翻譯"""
        try:
            filepath: Optional[str] = self.ui.ask_open_audio_file()
            
            if not filepath:
                return
            
            if not self.controller.is_engines_ready():
                self.ui.show_error("警告", "引擎尚未完全載入，請稍候...")
                return
            
            # 在背景處理檔案
            def process() -> None:
                try:
                    self.controller.process_audio_file(filepath)
                    logger.info(f"檔案處理完成：{filepath}")
                except Exception as e:
                    logger.error(f"檔案處理失敗：{e}", exc_info=True)
            
            self.ui.set_status(f"📁 正在處理檔案：{Path(filepath).name}", "#f59e0b")
            threading.Thread(target=process, daemon=True).start()
            
        except Exception as e:
            logger.error(f"上傳檔案失敗：{e}", exc_info=True)
    
    def _on_translate_click(self) -> None:
        """翻譯按鈕點擊"""
        try:
            if not self.controller.subtitles:
                self.ui.show_info("提示", "沒有可翻譯的內容")
                return
            
            # 顯示最後一條字幕
            latest: dict[str, Any] = self.controller.subtitles[-1]
            self.ui.show_info(
                "翻譯",
                f"原文：{latest['original']}\n\n譯文：{latest['translated']}"
            )
        except Exception as e:
            logger.error(f"翻譯按鈕點擊失敗：{e}", exc_info=True)
    
    def _on_save_subtitle(self) -> None:
        """保存字幕"""
        try:
            filepath: Optional[str] = self.ui.ask_save_file(default_name="subtitle")
            
            if filepath:
                if self.controller.save_subtitles(filepath):
                    self.ui.show_info("完成", f"字幕已儲存至：\n{filepath}")
                    logger.info(f"字幕已保存：{filepath}")
                else:
                    self.ui.show_error("錯誤", "保存字幕失敗")
                    logger.error("保存字幕失敗")
        except Exception as e:
            logger.error(f"保存字幕失敗：{e}", exc_info=True)
    
    def _on_settings_open(self) -> None:
        """打開設置面板"""
        try:
            def on_settings_save(settings: dict[str, Any]) -> None:
                try:
                    self.controller.set_settings(settings)
                    self.ui.show_info("完成", "設置已保存")
                    logger.info(f"設置已更新：{settings}")
                except Exception as e:
                    logger.error(f"保存設置失敗：{e}", exc_info=True)
                    self.ui.show_error("錯誤", f"保存設置失敗：{str(e)}")
            
            self.ui.show_settings_panel(on_save=on_settings_save)
        except Exception as e:
            logger.error(f"打開設置面板失敗：{e}", exc_info=True)
    
    def on_closing(self) -> None:
        """應用程式關閉"""
        try:
            logger.info("應用程式正在關閉...")
            self.controller.cleanup()
            self.destroy()
            logger.info("應用程式已關閉")
        except Exception as e:
            logger.error(f"關閉時出錯：{e}", exc_info=True)

