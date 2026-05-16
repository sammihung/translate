import customtkinter as ctk
import threading
import sys
from pathlib import Path
from tkinter import messagebox

from ui.main_ui import MainUI
from domain.controller import AppController
from core.logging_config import setup_logging, get_logger
from config.settings import config
import logging
import os

os.environ["TRANSFORMERS_VERBOSITY"] = "error"

logger = setup_logging(log_dir="logs", log_level=logging.INFO, console_output=True, file_output=True)


class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("QwenASR Pro")
        self.geometry("1100x750")
        ctk.set_appearance_mode("dark")

        self.controller = AppController()
        self.ui = MainUI(self)
        self.ui.pack(fill="both", expand=True)

        self.ui.on_record_toggle = self._on_record_toggle
        self.ui.on_upload_file = self._on_upload_file
        self.ui.on_save_subtitle = self._on_save_subtitle
        self.ui.on_get_apps = self._on_get_apps

        self.controller.callbacks.on_subtitle_update = self._on_subtitle_update
        self.controller.callbacks.on_translation_complete = self._on_translation_complete
        self.controller.callbacks.on_status_change = self._on_status_change
        self.controller.callbacks.on_audio_level = self._on_audio_level

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(500, self._initialize)

        logger.info("應用程式已啟動")

    def _initialize(self):
        current = self.controller.get_current_config()
        self.ui.asr_model_var.set(current["asr_model"])
        self.ui.asr_url_var.set(current["asr_api_url"])
        self.ui.asr_key_var.set(current["asr_api_key"])
        self.ui.translate_model_var.set(current["translate_model"])
        self.ui.translate_url_var.set(current["translate_api_url"])
        self.ui.translate_key_var.set(current["translate_api_key"])

        self.ui.set_status("連接中...", "#f59e0b")

        def load():
            try:
                success = self.controller.initialize_engines()
                if success:
                    self.ui.set_status("已連接", "#10b981")
                    self.ui.enable_record_button(True)
                    self.ui.settings_view.set_asr_status(True)
                    self.ui.settings_view.set_translate_status(True)
                else:
                    self.ui.set_status("連接失敗", "#ef4444")
            except Exception as ex:
                logger.error(f"初始化失敗：{ex}", exc_info=True)
                self.ui.set_status("錯誤", "#ef4444")

        threading.Thread(target=load, daemon=True).start()

    def _on_record_toggle(self):
        try:
            if self.controller.is_recording:
                self.controller.stop_recording()
                self.ui.update_record_state(False)
            else:
                if not self.controller.is_engines_ready():
                    messagebox.showwarning("警告", "API 未連接")
                    return
                if self.controller.start_recording():
                    self.ui.update_record_state(True)
                else:
                    messagebox.showerror("錯誤", "無法啟動錄音")
        except Exception as ex:
            logger.error(f"錄音錯誤：{ex}", exc_info=True)

    def _on_subtitle_update(self, original, translated, speaker_id):
        try:
            return self.ui.add_chat_bubble(f"SPEAKER #{speaker_id}", original, translated, speaker_id)
        except Exception as ex:
            logger.error(f"字幕更新失敗：{ex}", exc_info=True)
            return ""

    def _on_translation_complete(self, bubble_id, translated):
        self.ui.update_chat_bubble(bubble_id, translated)

    def _on_status_change(self, status, color):
        self.ui.set_status(status, color)

    def _on_audio_level(self, level):
        self.ui.realtime_view.update_audio_level(level)

    def _on_upload_file(self):
        try:
            filepath = self.ui.ask_open_audio_file()
            if not filepath:
                return
            if not self.controller.is_engines_ready():
                self.ui.show_error("錯誤", "API 未連接")
                return

            def process():
                try:
                    self.controller.process_audio_file(filepath)
                except Exception as ex:
                    logger.error(f"處理失敗：{ex}", exc_info=True)

            self.ui.set_status(f"處理 {Path(filepath).name}", "#f59e0b")
            threading.Thread(target=process, daemon=True).start()
        except Exception as ex:
            logger.error(f"上傳失敗：{ex}", exc_info=True)

    def _on_save_subtitle(self):
        try:
            filepath = self.ui.ask_save_file()
            if filepath:
                if self.controller.save_subtitles(filepath):
                    self.ui.show_info("完成", f"已儲存：{filepath}")
                else:
                    self.ui.show_error("錯誤", "儲存失敗")
        except Exception as ex:
            logger.error(f"儲存失敗：{ex}", exc_info=True)

    def _on_get_apps(self):
        try:
            return self.controller.get_audio_apps()
        except Exception as ex:
            logger.error(f"獲取 App 失敗：{ex}", exc_info=True)
            return []

    def on_closing(self):
        try:
            self.controller.cleanup()
            self.destroy()
        except Exception as ex:
            logger.error(f"關閉錯誤：{ex}", exc_info=True)