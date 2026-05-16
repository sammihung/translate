import customtkinter as ctk
import threading
import sys
from pathlib import Path
from typing import Optional
from tkinter import messagebox

from ui.main_ui import MainUI
from domain.controller import AppController
from core.logging_config import setup_logging, get_logger
from config.settings import config
import logging
import os

os.environ["TRANSFORMERS_VERBOSITY"] = "error"

logger = setup_logging(
    log_dir="logs",
    log_level=logging.INFO,
    console_output=True,
    file_output=True
)


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("QwenASR Pro")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")

        self.controller: AppController = AppController()
        self.ui: MainUI = MainUI(self)
        self.ui.pack(fill="both", expand=True)

        self.ui.on_record_toggle = self._on_record_toggle
        self.ui.on_upload_file = self._on_upload_file
        self.ui.on_save_subtitle = self._on_save_subtitle

        self.controller.callbacks.on_subtitle_update = self._on_subtitle_update
        self.controller.callbacks.on_translation_complete = self._on_translation_complete
        self.controller.callbacks.on_status_change = self._on_status_change

        self.ui.realtime_view.src_lang_combo.configure(command=self._on_lang_change)
        self.ui.realtime_view.tgt_lang_combo.configure(command=self._on_lang_change)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(500, self._initialize)

        logger.info("應用程式已啟動")

    def _on_lang_change(self, choice):
        src, tgt = self.ui.get_selected_languages()
        self.controller.src_lang = src
        self.controller.tgt_lang = tgt

        if self.controller.ai_ctrl.translate_engine:
            self.controller.ai_ctrl.translate_engine.target_lang = tgt

        logger.info(f"語言已切換：來源={src}, 目標={tgt}")

    def _initialize(self):
        try:
            devices = self.controller.get_audio_devices()
            self.ui.set_device_list(devices)

            current = self.controller.get_current_config()
            self.ui.asr_model_var.set(current["asr_model"])
            self.ui.asr_url_var.set(current["asr_api_url"])
            self.ui.asr_key_var.set(current["asr_api_key"])
            self.ui.translate_model_var.set(current["translate_model"])
            self.ui.translate_url_var.set(current["translate_api_url"])
            self.ui.translate_key_var.set(current["translate_api_key"])

            self.ui.set_status("[LOADING] 正在連接 API...", "#f59e0b")

            def load_engines():
                try:
                    def progress_callback(status):
                        self.ui.set_status(status, "#f59e0b")

                    success = self.controller.initialize_engines(
                        progress_callback=progress_callback
                    )

                    if success:
                        self.ui.set_status("[OK] API 已連接", "#10b981")
                        self.ui.enable_record_button(True)
                    else:
                        self.ui.set_status("[ERROR] API 連接失敗", "#ef4444")
                        self.ui.enable_record_button(False)
                except Exception as e:
                    logger.error(f"引擎初始化異常：{e}", exc_info=True)
                    self.ui.set_status(f"[ERROR] {str(e)}", "#ef4444")
                    self.ui.enable_record_button(False)

            threading.Thread(target=load_engines, daemon=True).start()
        except Exception as e:
            logger.error(f"初始化失敗：{e}", exc_info=True)
            self.ui.set_status(f"[ERROR] {str(e)}", "#ef4444")

    def _on_record_toggle(self):
        try:
            if self.controller.is_recording:
                self._stop_recording()
            else:
                self._start_recording()
        except Exception as e:
            logger.error(f"錄音切換失敗：{e}", exc_info=True)
            messagebox.showerror("錯誤", f"錄音操作失敗：{str(e)}")

    def _start_recording(self):
        try:
            if not self.controller.is_engines_ready():
                messagebox.showwarning("警告", "引擎尚未連接，請先在設定中配置 API")
                return

            device_name = self.ui.get_selected_device()
            device_index = self.controller.audio_mgr.parse_device_index(device_name)

            if self.controller.start_recording(device_index):
                self.ui.update_record_state(True)
            else:
                messagebox.showerror("錯誤", "啟動錄音失敗")
        except Exception as e:
            logger.error(f"開始錄音失敗：{e}", exc_info=True)
            messagebox.showerror("錯誤", f"無法開始錄音：{str(e)}")

    def _stop_recording(self):
        try:
            self.controller.stop_recording()
            self.ui.update_record_state(False)
        except Exception as e:
            logger.error(f"停止錄音失敗：{e}", exc_info=True)

    def _on_subtitle_update(self, original, translated, speaker_id):
        try:
            speaker_name = f"SPEAKER #{speaker_id}"
            bubble_id = self.ui.add_chat_bubble(speaker_name, original, translated, speaker_id)
            return bubble_id
        except Exception as e:
            logger.error(f"字幕更新失敗：{e}", exc_info=True)
            return ""

    def _on_translation_complete(self, bubble_id, translated):
        try:
            self.ui.update_chat_bubble(bubble_id, translated)
        except Exception as e:
            logger.error(f"更新翻譯失敗：{e}", exc_info=True)

    def _on_status_change(self, status, color):
        try:
            self.ui.set_status(status, color)
        except Exception as e:
            logger.error(f"更新狀態失敗：{e}", exc_info=True)

    def _on_upload_file(self):
        try:
            filepath = self.ui.ask_open_audio_file()
            if not filepath:
                return

            if not self.controller.is_engines_ready():
                self.ui.show_error("警告", "引擎尚未連接")
                return

            def process():
                try:
                    self.controller.process_audio_file(filepath)
                except Exception as e:
                    logger.error(f"檔案處理失敗：{e}", exc_info=True)

            self.ui.set_status(f"處理檔案：{Path(filepath).name}", "#f59e0b")
            threading.Thread(target=process, daemon=True).start()
        except Exception as e:
            logger.error(f"上傳檔案失敗：{e}", exc_info=True)

    def _on_save_subtitle(self):
        try:
            filepath = self.ui.ask_save_file()
            if filepath:
                if self.controller.save_subtitles(filepath):
                    self.ui.show_info("完成", f"字幕已儲存至：\n{filepath}")
                else:
                    self.ui.show_error("錯誤", "保存字幕失敗")
        except Exception as e:
            logger.error(f"保存字幕失敗：{e}", exc_info=True)

    def on_closing(self):
        try:
            self.controller.cleanup()
            self.destroy()
        except Exception as e:
            logger.error(f"關閉時出錯：{e}", exc_info=True)