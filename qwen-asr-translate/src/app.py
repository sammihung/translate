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
from pathlib import Path

from ui import MainUI
from controller import AppController
from tkinter import messagebox
import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

class App(ctk.CTk):
    """主應用程式 - 連接 UI 和 Controller"""
    
    def __init__(self):
        super().__init__()
        
        self.title("QwenASR Pro - YouTube Edition")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        
        # 創建控制器
        self.controller = AppController()
        
        # 創建 UI
        self.ui = MainUI(self)
        self.ui.pack(fill="both", expand=True)
        
        # 連接 UI 回調
        self.ui.on_record_toggle = self._on_record_toggle
        self.ui.on_upload_file = self._on_upload_file
        self.ui.on_clear_history = self._on_clear_history
        self.ui.on_translate_click = self._on_translate_click
        self.ui.on_save_subtitle = self._on_save_subtitle
        self.ui.on_settings_open = self._on_settings_open
        
        # 連接 Controller 回調
        self.controller.on_subtitle_update = self._on_subtitle_update
        self.controller.on_translation_complete = self._on_translation_complete # <--- 新增呢行
        self.controller.on_status_change = self._on_status_change
        
        # 新增：綁定語言切換事件
        self.ui.src_lang_combo.configure(command=self._on_lang_change)
        self.ui.tgt_lang_combo.configure(command=self._on_lang_change)
        
        # 處理關閉事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 初始化
        self.after(500, self._initialize)
    
    def _on_lang_change(self, choice):
        """處理語言切換"""
        src, tgt = self.ui.get_selected_languages()
        self.controller.src_lang = src
        self.controller.tgt_lang = tgt
        
        # 關鍵修復：直接將目標語言 (tgt) 更新入去 Ollama 翻譯引擎度！
        if hasattr(self.controller, 'ai_ctrl') and self.controller.ai_ctrl.translate_engine:
            self.controller.ai_ctrl.translate_engine.target_lang = tgt
            
        print(f"[Language] 已切換: 來源={src}, 目標={tgt}")
    
    def _initialize(self):
        """初始化應用程式"""
        # 更新設備列表
        devices = self.controller.get_audio_devices()
        self.ui.set_device_list(devices)
        self.ui.use_full_model_var.set(self.controller.use_full_model)
        
        # 如果冇 GPU，我哋仲可以將個 Checkbox 變灰或者加個警告字眼
        if not self.controller.has_gpu:
            print("⚠️ Note: No GPU detected, Full Model might be very slow.")
        # 啟動引擎載入
        self.ui.set_status("[LOADING] 正在載入引擎...", "#f59e0b")
        
        def load_engines():
            def progress_callback(status: str):
                self.ui.set_status(status, "#f59e0b")
            
            success = self.controller.initialize_engines(
                progress_callback=progress_callback
            )
            
            if success:
                self.ui.set_status("[OK] 所有引擎已就緒", "#10b981")
                self.ui.enable_record_button(True)
            else:
                self.ui.set_status("[ERROR] 引擎初始化失敗", "#ef4444")
                self.ui.enable_record_button(False)
        
        threading.Thread(target=load_engines, daemon=True).start()
    
    def _on_record_toggle(self):
        """切換錄音"""
        if self.controller.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _start_recording(self):
        """開始錄音"""
        if not self.controller.is_engines_ready():
            messagebox.showwarning("警告", "引擎尚未完全載入，請稍候...")
            return
        
        device_name = self.ui.device_var.get()
        device_index = self.controller.audio_mgr.parse_device_index(device_name)
        
        if self.controller.start_recording(device_index):
            # 修正：ui.py 中的方法已經改名為 update_record_state
            self.ui.update_record_state(True)
        else:
            messagebox.showerror("錯誤", "啟動錄音失敗，請檢查音訊設備")
    
    def _stop_recording(self):
        """停止錄音"""
        self.controller.stop_recording()
        # 修正：ui.py 中的方法已經改名為 update_record_state
        self.ui.update_record_state(False)
        # 移除舊版不存在的 UI 呼叫，例如 enable_save_button
        
    def _on_subtitle_update(self, original: str, translated: str, speaker_id: int) -> str:
        """字幕更新回調 (注意：現在會回傳 bubble_id)"""
        speaker_name = f"SPEAKER #{speaker_id}"
        # 回傳 ID 俾 Controller 記住
        return self.ui.add_chat_bubble(speaker_name, original, translated, speaker_id)
        
    def _on_translation_complete(self, bubble_id: str, translated: str):
        """背景翻譯完成回調"""
        self.ui.update_chat_bubble(bubble_id, translated)
    
    def _on_status_change(self, status: str, color: str):
        """狀態變化回調"""
        self.ui.set_status(status, color)
    
    def _on_clear_history(self):
        """清空歷史記錄"""
        self.controller.clear_history()
        self.ui.clear_history()
        self.ui.show_info("完成", "歷史記錄已清空")
    
    def _on_upload_file(self):
        """上傳檔案進行翻譯"""
        filepath = self.ui.ask_open_audio_file()
        
        if not filepath:
            return
        
        if not self.controller.is_engines_ready():
            self.ui.show_error("警告", "引擎尚未完全載入，請稍候...")
            return
        
        # 在背景處理檔案
        def process():
            self.controller.process_audio_file(filepath)
        
        self.ui.set_status("📁 正在處理檔案...", "#f59e0b")
        threading.Thread(target=process, daemon=True).start()
    
    def _on_translate_click(self):
        """翻譯按鈕點擊"""
        if not self.controller.subtitles:
            self.ui.show_info("提示", "沒有可翻譯的內容")
            return
        
        # 顯示最後一條字幕
        latest = self.controller.subtitles[-1]
        self.ui.show_info(
            "翻譯",
            f"原文：{latest['original']}\n\n譯文：{latest['translated']}"
        )
    
    def _on_save_subtitle(self):
        """保存字幕"""
        filepath = self.ui.ask_save_file(default_name="subtitle")
        
        if filepath:
            if self.controller.save_subtitles(filepath):
                self.ui.show_info("完成", f"字幕已儲存至：\n{filepath}")
            else:
                self.ui.show_error("錯誤", "保存字幕失敗")
    
    def _on_settings_open(self):
        """打開設置面板"""
        def on_settings_save(settings: dict):
            self.controller.set_settings(settings)
            self.ui.show_info("完成", "設置已保存")
        
        self.ui.show_settings_panel(on_save=on_settings_save)
    
    def on_closing(self):
        """應用程式關閉"""
        self.controller.cleanup()
        self.destroy()


def main():
    """主函數"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
