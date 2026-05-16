"""
QwenASR Pro - Main UI Component
API-driven configuration, no hardcoded models
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import uuid
import requests
import threading
from typing import Optional, Callable, Dict, Any, List
from functools import wraps
from core.logging_config import get_logger

logger = get_logger(__name__)

BACKEND_OPTIONS = ["lm_studio", "openai_compat", "custom"]

BACKEND_DEFAULTS = {
    "lm_studio": "http://localhost:1234/v1",
    "openai_compat": "",
    "custom": ""
}


def run_in_main_thread(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.after(0, lambda: func(self, *args, **kwargs))
    return wrapper


class MainUI(ctk.CTkFrame):
    """Main UI - API Config Driven"""
    
    def __init__(self, master, controller=None, **kwargs):
        super().__init__(master, **kwargs)
        
        if controller:
            self.controller = controller
        elif hasattr(master, 'controller'):
            self.controller = master.controller
        else:
            self.controller = master
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.colors = {
            "bg_dark": "#0b0f19",
            "bg_panel": "#1e293b",
            "primary": "#3b82f6",
            "primary_hover": "#2563eb",
            "primary_muted": "#1e3a8a",
            "danger": "#ef4444",
            "danger_hover": "#dc2626",
            "success": "#10b981",
            "text_light": "#f8fafc",
            "text_muted": "#94a3b8"
        }
        self.configure(fg_color=self.colors["bg_dark"])
        
        self.font_sizes = {"original": 13, "translated": 16}
        self.cleaned_bubble_ids = set()
        self.max_bubbles = 100
        self.max_floating_bubbles = 50
        
        self.menu_expanded = True
        self.EXPANDED_WIDTH = 200
        self.COLLAPSED_WIDTH = 60
        
        self.device_var = ctk.StringVar(value="請先重新整理裝置...")
        self.src_lang_var = ctk.StringVar(value="auto")
        self.tgt_lang_var = ctk.StringVar(value="zh")
        
        self.asr_backend_var = ctk.StringVar(value="lm_studio")
        self.asr_model_var = ctk.StringVar(value="qwen3-asr-1.7b")
        self.asr_url_var = ctk.StringVar(value="http://localhost:1234/v1")
        self.asr_key_var = ctk.StringVar(value="")
        
        self.translate_backend_var = ctk.StringVar(value="lm_studio")
        self.translate_model_var = ctk.StringVar(value="qwen3.5-9b")
        self.translate_url_var = ctk.StringVar(value="http://localhost:1234/v1")
        self.translate_key_var = ctk.StringVar(value="")
        
        self.vad_duration_var = ctk.DoubleVar(value=1.5)
        
        self.on_record_toggle: Optional[Callable] = None
        self.on_upload_file: Optional[Callable] = None
        self.on_save_subtitle: Optional[Callable] = None
        
        self.floating_mode = False
        self.floating_window: Optional[ctk.CTkToplevel] = None
        
        self._build_sidebar()
        self._build_main_container()
        self.switch_view("realtime")
    
    # ==========================================
    # 1. Sidebar (Collapsible)
    # ==========================================
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=self.EXPANDED_WIDTH, corner_radius=0, fg_color="#0f172a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(5, weight=1) 
        
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(15, 10))
        
        self.toggle_btn = ctk.CTkButton(
            header_frame, text="☰", width=40, height=40, corner_radius=8,
            fg_color="transparent", hover_color=self.colors["bg_panel"], 
            command=self.toggle_menu, font=ctk.CTkFont(size=18)
        )
        self.toggle_btn.pack(side="left")
        
        self.logo_label = ctk.CTkLabel(
            header_frame, text="🌊 QwenASR", font=ctk.CTkFont(size=18, weight="bold"), 
            text_color=self.colors["primary"]
        )
        self.logo_label.pack(side="left", padx=10)
        
        self.nav_buttons = {}
        self.nav_text_labels = {} 
        nav_items = [
            ("realtime", "⚡", "即時翻譯"),
            ("batch", "📁", "批量上傳"),
            ("settings", "⚙️", "系統設定")
        ]
        
        for idx, (view_id, icon, text) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=f"{icon} {text}", font=ctk.CTkFont(size=14), 
                fg_color="transparent", text_color=self.colors["text_muted"],
                hover_color=self.colors["bg_panel"], anchor="w", height=45, 
                corner_radius=8, command=lambda vid=view_id: self.switch_view(vid)
            )
            btn.grid(row=idx, column=0, padx=10, pady=3, sticky="ew")
            self.nav_buttons[view_id] = btn
            self.nav_text_labels[view_id] = {"icon": icon, "text": text}

        # Floating Overlay Mode Button
        self.floating_btn = ctk.CTkButton(
            self.sidebar, text="🪟 浮動字幕模式", font=ctk.CTkFont(size=14), 
            fg_color=self.colors["primary"], text_color=self.colors["text_light"],
            hover_color=self.colors["primary_hover"], anchor="w", height=45, 
            corner_radius=8, command=self.toggle_floating_mode
        )
        self.floating_btn.grid(row=4, column=0, padx=10, pady=3, sticky="ew")

        # Font Size Control Button
        self.font_btn = ctk.CTkButton(
            self.sidebar, text="🔤 文字大小：標準", font=ctk.CTkFont(size=14), 
            fg_color=self.colors["bg_panel"], text_color=self.colors["text_light"],
            hover_color=self.colors["primary"], anchor="w", height=45, 
            corner_radius=8, command=self.cycle_font_size
        )
        self.font_btn.grid(row=5, column=0, padx=10, pady=3, sticky="ew")

        self.status_indicator = ctk.CTkLabel(
            self.sidebar, text="🟢 系統就緒", font=ctk.CTkFont(size=11), 
            text_color=self.colors["success"]
        )
        self.status_indicator.grid(row=6, column=0, padx=20, pady=20, sticky="w")
    
    def toggle_menu(self) -> None:
        """Toggle Sidebar Collapsed/Expanded"""
        self.menu_expanded = not self.menu_expanded
        if self.menu_expanded:
            self.sidebar.configure(width=self.EXPANDED_WIDTH)
            self.logo_label.pack(side="left", padx=10)
            for view_id, btn in self.nav_buttons.items():
                btn.configure(text=f"{self.nav_text_labels[view_id]['icon']} {self.nav_text_labels[view_id]['text']}")
            self.status_indicator.configure(text="🟢 系統就緒")
        else:
            self.sidebar.configure(width=self.COLLAPSED_WIDTH)
            self.logo_label.pack_forget()
            for view_id, btn in self.nav_buttons.items():
                btn.configure(text=self.nav_text_labels[view_id]['icon'])
            self.status_indicator.configure(text="🟢")
    
    # ==========================================
    # 2. Main Container
    # ==========================================
    def _build_main_container(self):
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        self.views = {
            "realtime": self._build_realtime_view(),
            "batch": self._build_batch_view(),
            "settings": self._build_settings_view()
        }
    
    # ==========================================
    # 3. Real-time View
    # ==========================================
    def _build_realtime_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(frame, height=60, fg_color=self.colors["bg_panel"], corner_radius=15)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        device_frame = ctk.CTkFrame(header, fg_color="transparent")
        device_frame.pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(device_frame, text="🎤 音訊:", text_color=self.colors["text_muted"]).pack(side="left", padx=(0, 5))
        self.device_combo = ctk.CTkComboBox(device_frame, variable=self.device_var, values=["載入中..."], width=280, fg_color="#0f172a", border_color="#334155")
        self.device_combo.pack(side="left", padx=5)
        
        # 🔧 FIX 3: Refresh button now works
        ctk.CTkButton(device_frame, text="🔄", width=35, fg_color=self.colors["primary_muted"], 
            hover_color=self.colors["primary"], command=self._on_refresh_devices).pack(side="left", padx=5)

        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.pack(side="right", padx=15, pady=10)
        
        src_langs = {"自動偵測 (Auto)": "auto", "日文 (JA)": "ja", "英文 (EN)": "en", "中文 (ZH)": "zh", "韓文 (KO)": "ko"}
        self.src_lang_combo = ctk.CTkComboBox(lang_frame, values=list(src_langs.keys()), width=130, 
            fg_color="#0f172a", border_color="#334155", command=lambda choice: self.src_lang_var.set(src_langs[choice]))
        self.src_lang_combo.set("自動偵測 (Auto)")
        self.src_lang_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(lang_frame, text="➔", text_color=self.colors["text_muted"]).pack(side="left", padx=2)
        
        tgt_langs = {"繁體中文 (ZH)": "zh", "英文 (EN)": "en", "日文 (JA)": "ja", "韓文 (KO)": "ko"}
        self.tgt_lang_combo = ctk.CTkComboBox(lang_frame, values=list(tgt_langs.keys()), width=130, 
            fg_color="#0f172a", border_color="#334155", command=lambda choice: self.tgt_lang_var.set(tgt_langs[choice]))
        self.tgt_lang_combo.set("繁體中文 (ZH)")
        self.tgt_lang_combo.pack(side="left", padx=5)

        self.chat_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew")

        bottom_bar = ctk.CTkFrame(frame, height=80, fg_color=self.colors["bg_panel"], corner_radius=20)
        bottom_bar.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        
        self.record_btn = ctk.CTkButton(bottom_bar, text="🎤", width=60, height=60, corner_radius=30, 
            font=ctk.CTkFont(size=24), fg_color=self.colors["danger"], hover_color=self.colors["danger_hover"],
            command=self._on_record_click, state="disabled")
        self.record_btn.pack(side="left", padx=20, pady=10)
        
        self.record_status_label = ctk.CTkLabel(bottom_bar, text="準備就緒 (READY)", 
            font=ctk.CTkFont(family="Courier", size=14), text_color=self.colors["text_muted"])
        self.record_status_label.pack(side="left", padx=10)
        
        ctk.CTkButton(bottom_bar, text="匯出 SRT", fg_color=self.colors["primary"], 
            hover_color=self.colors["primary_hover"], width=100, command=self._on_export_click).pack(side="right", padx=20)
        
        return frame
    
    # ==========================================
    # 4. Batch View
    # ==========================================
    def _build_batch_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(frame, text="批量音檔轉字幕", font=ctk.CTkFont(size=24, weight="bold"), 
            text_color=self.colors["text_light"]).pack(anchor="w", pady=(0, 20))
        
        dropzone = ctk.CTkFrame(frame, height=200, fg_color=self.colors["bg_panel"], 
            border_width=2, border_color="#334155")
        dropzone.pack(fill="x", pady=10)
        dropzone.pack_propagate(False)
        ctk.CTkLabel(dropzone, text="☁️\n點擊此處瀏覽檔案\n(支援 MP3, WAV, MP4)", 
            font=ctk.CTkFont(size=16), text_color=self.colors["text_muted"], justify="center").pack(expand=True)
        
        dropzone.bind("<Button-1>", lambda e: self._on_batch_start())
        for child in dropzone.winfo_children():
            child.bind("<Button-1>", lambda e: self._on_batch_start())
        
        settings_panel = ctk.CTkFrame(frame, fg_color=self.colors["bg_panel"], corner_radius=15)
        settings_panel.pack(fill="x", pady=20, ipady=10)
        ctk.CTkCheckBox(settings_panel, text="產生雙語 SRT 字幕檔", 
            text_color=self.colors["text_light"]).pack(anchor="w", padx=20, pady=15)
        
        ctk.CTkButton(frame, text="▶ 選擇檔案並轉換", height=45, fg_color=self.colors["primary"], 
            command=self._on_batch_start).pack(anchor="e", pady=20)
        return frame
    
    # ==========================================
    # 5. Settings View (API Config Form)
    # ==========================================
    def _build_settings_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        ctk.CTkLabel(frame, text="API 配置", font=ctk.CTkFont(size=24, weight="bold"), 
            text_color=self.colors["text_light"]).pack(anchor="w", pady=(0, 20))
        
        panel = ctk.CTkFrame(frame, fg_color=self.colors["bg_panel"], corner_radius=15)
        panel.pack(fill="x", pady=10, ipadx=20, ipady=20)
        
        # ---- ASR Section ----
        ctk.CTkLabel(panel, text="ASR 語音辨識", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        
        row1 = ctk.CTkFrame(panel, fg_color="transparent")
        row1.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row1, text="後端:", width=60).pack(side="left")
        self.asr_backend_combo = ctk.CTkComboBox(
            row1, variable=self.asr_backend_var, values=BACKEND_OPTIONS,
            width=180, fg_color="#0f172a", command=self._on_asr_backend_change
        )
        self.asr_backend_combo.pack(side="left", padx=5)
        
        row2 = ctk.CTkFrame(panel, fg_color="transparent")
        row2.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row2, text="模型 ID:", width=60).pack(side="left")
        self.asr_model_entry = ctk.CTkEntry(
            row2, variable=self.asr_model_var, width=250, fg_color="#0f172a"
        )
        self.asr_model_entry.pack(side="left", padx=5)
        
        row3 = ctk.CTkFrame(panel, fg_color="transparent")
        row3.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row3, text="API URL:", width=60).pack(side="left")
        self.asr_url_entry = ctk.CTkEntry(
            row3, variable=self.asr_url_var, width=250, fg_color="#0f172a"
        )
        self.asr_url_entry.pack(side="left", padx=5)
        
        row4 = ctk.CTkFrame(panel, fg_color="transparent")
        row4.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row4, text="API Key:", width=60).pack(side="left")
        self.asr_key_entry = ctk.CTkEntry(
            row4, variable=self.asr_key_var, width=250, fg_color="#0f172a", show=""
        )
        self.asr_key_entry.pack(side="left", padx=5)
        
        # ---- Translation Section ----
        ctk.CTkLabel(panel, text="翻譯模型", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 5))
        
        row5 = ctk.CTkFrame(panel, fg_color="transparent")
        row5.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row5, text="後端:", width=60).pack(side="left")
        self.translate_backend_combo = ctk.CTkComboBox(
            row5, variable=self.translate_backend_var, values=BACKEND_OPTIONS,
            width=180, fg_color="#0f172a", command=self._on_translate_backend_change
        )
        self.translate_backend_combo.pack(side="left", padx=5)
        
        row6 = ctk.CTkFrame(panel, fg_color="transparent")
        row6.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row6, text="模型 ID:", width=60).pack(side="left")
        self.translate_model_entry = ctk.CTkEntry(
            row6, variable=self.translate_model_var, width=250, fg_color="#0f172a"
        )
        self.translate_model_entry.pack(side="left", padx=5)
        
        row7 = ctk.CTkFrame(panel, fg_color="transparent")
        row7.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row7, text="API URL:", width=60).pack(side="left")
        self.translate_url_entry = ctk.CTkEntry(
            row7, variable=self.translate_url_var, width=250, fg_color="#0f172a"
        )
        self.translate_url_entry.pack(side="left", padx=5)
        
        row8 = ctk.CTkFrame(panel, fg_color="transparent")
        row8.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row8, text="API Key:", width=60).pack(side="left")
        self.translate_key_entry = ctk.CTkEntry(
            row8, variable=self.translate_key_var, width=250, fg_color="#0f172a", show=""
        )
        self.translate_key_entry.pack(side="left", padx=5)
        
        # ---- VAD ----
        ctk.CTkLabel(panel, text="VAD 靜音切割 (秒)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 5))
        slider_frame = ctk.CTkFrame(panel, fg_color="transparent")
        slider_frame.pack(anchor="w", fill="x", padx=20, pady=(0, 15))
        
        vad_slider = ctk.CTkSlider(slider_frame, variable=self.vad_duration_var, from_=0.5, to=3.0,
            number_of_steps=25, width=350)
        vad_slider.pack(side="left", padx=(0, 15))
        
        vad_value_label = ctk.CTkLabel(slider_frame, text="1.5s", font=ctk.CTkFont(family="Courier"))
        vad_value_label.pack(side="left")
        vad_slider.configure(command=lambda val: vad_value_label.configure(text=f"{val:.1f}s"))
        
        # ---- Fetch Models Button ----
        ctk.CTkButton(frame, text="🔄 從 LM Studio 取得模型列表", height=35,
            fg_color=self.colors["primary_muted"], command=self._on_fetch_models).pack(anchor="e", pady=10)
        
        ctk.CTkButton(frame, text="💾 儲存並套用設定", height=45, fg_color=self.colors["primary"],
            command=self._on_save_settings).pack(anchor="e", pady=20)
        return frame
    
    # ==========================================
    # Public Methods
    # ==========================================
    def set_device_list(self, devices: list, default_index: int = 0):
        """更新設備列表 - 直接更新唔使用 after"""
        if devices:
            self.device_combo.configure(values=devices)
            self.device_var.set(devices[default_index])
        else:
            self.device_combo.configure(values=["無可用音訊裝置"])
            self.device_var.set("無可用音訊裝置")
    
    @run_in_main_thread
    def set_status(self, text: str, color: str = None):
        """更新狀態指示器 - Thread-Safe"""
        self.status_indicator.configure(text=text, text_color=color if color else self.colors["text_muted"])

    @run_in_main_thread
    def enable_record_button(self, enabled: bool):
        """啟用/禁用錄音按鈕 - Thread-Safe"""
        self.record_btn.configure(state="normal" if enabled else "disabled")

    def get_selected_device(self) -> str:
        # 🔧 FIX: 強制從 ComboBox 元件抓取目前顯示的文字，避免 StringVar 不同步的問題
        return self.device_combo.get()

    def get_selected_languages(self):
        return self.src_lang_var.get(), self.tgt_lang_var.get()
    
    def switch_view(self, view_id):
        for view in self.views.values(): 
            view.grid_forget()
        for btn in self.nav_buttons.values(): 
            btn.configure(fg_color="transparent", text_color=self.colors["text_muted"])
        self.views[view_id].grid(row=0, column=0, sticky="nsew")
        self.nav_buttons[view_id].configure(fg_color=self.colors["primary_muted"], text_color=self.colors["primary"])
    
    # 🔧 FIX 6: All Button Handlers
    def _on_refresh_devices(self):
        """重新整理設備列表 - 非阻塞"""
        import threading
        
        # UI 立即顯示「搜尋中」
        self.device_combo.configure(values=["搜尋裝置中..."])
        self.device_var.set("搜尋裝置中...")
        
        # 喺背景執行緒獲取設備
        def refresh_thread():
            if self.controller and hasattr(self.controller, 'get_audio_devices'):
                devices = self.controller.get_audio_devices()
                # 使用 after 確保 UI 更新喺主執行緒
                self.after(0, lambda: self.set_device_list(devices))
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def _on_record_click(self):
        if hasattr(self, 'on_record_toggle') and callable(self.on_record_toggle): 
            self.on_record_toggle()
    
    def _on_export_click(self):
        if hasattr(self, 'on_save_subtitle') and callable(self.on_save_subtitle): 
            self.on_save_subtitle()
    
    def _on_batch_start(self):
        if hasattr(self, 'on_upload_file') and callable(self.on_upload_file): 
            self.on_upload_file()
    
    @run_in_main_thread
    def update_record_state(self, is_recording: bool):
        """更新錄音按鈕狀態 - Thread-Safe"""
        if is_recording:
            self.record_btn.configure(text="■", fg_color=self.colors["bg_panel"], hover_color="#334155")
            self.record_status_label.configure(text="LISTENING...", text_color=self.colors["success"])
        else:
            self.record_btn.configure(text="🎤", fg_color=self.colors["danger"], hover_color=self.colors["danger_hover"])
            self.record_status_label.configure(text="PAUSED", text_color=self.colors["text_muted"])
    
    def add_chat_bubble(self, speaker_name: str, original: str, translated: str, speaker_id: int = 1) -> str:
        """新增聊天氣泡 - Thread-Safe (同時更新主窗口同浮動窗口)"""
        bubble_id = str(uuid.uuid4())
        
        # 🔧 FIX: 手動用 after(0, ...) 包裝，唔好用 decorator（因為會返回 None）
        def _update():
            try:
                logger.info(f"💬 [UI_ADD_BUBBLE] 開始建立氣泡，bubble_id={bubble_id}, 原文：'{original[:50]}...'")
                
                if not hasattr(self, 'chat_bubbles'):
                    self.chat_bubbles, self.bubble_containers, self.bubble_order = {}, {}, []
                    logger.info("💬 [UI_ADD_BUBBLE] 初始化 chat_bubbles 字典")
                
                align, bubble_color, text_color = ("w", "#1e293b", self.colors["primary"]) if speaker_id == 1 else ("e", "#064e3b", self.colors["success"])
                
                # 建立容器（主窗口）
                container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
                container.pack(fill="x", pady=10, padx=10)
                logger.info(f"💬 [UI_ADD_BUBBLE] 容器已建立")
                
                # 建立氣泡（主窗口）
                bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=15)
                bubble.pack(anchor=align, ipadx=10, ipady=10)
                logger.info(f"💬 [UI_ADD_BUBBLE] 氣泡已建立")
                
                # 建立標題（主窗口）
                header = ctk.CTkFrame(bubble, fg_color="transparent")
                header.pack(fill="x", padx=10, pady=(5, 5))
                
                side_align = "left" if speaker_id == 1 else "right"
                ctk.CTkLabel(header, text=speaker_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_color).pack(side=side_align)
                ctk.CTkLabel(header, text=datetime.now().strftime("%H:%M:%S"), font=ctk.CTkFont(family="Courier", size=10), text_color=self.colors["text_muted"]).pack(side=side_align, padx=10)
                
                # 建立原文（主窗口）- 使用動態字體大小
                ctk.CTkLabel(bubble, text=original, font=ctk.CTkFont(size=self.font_sizes["original"], slant="italic"), text_color=self.colors["text_muted"], wraplength=500, justify="left").pack(anchor=align, padx=10, pady=(0, 2))
                
                # 建立譯文（主窗口）- 使用動態字體大小
                trans_label = ctk.CTkLabel(bubble, text=translated, font=ctk.CTkFont(size=self.font_sizes["translated"], weight="bold"), text_color=self.colors["text_light"], wraplength=500, justify="left")
                trans_label.pack(anchor=align, padx=10, pady=(0, 5))
                logger.info(f"💬 [UI_ADD_BUBBLE] 譯文標籤已建立")
                
                # 儲存引用（主窗口）
                self.chat_bubbles[bubble_id] = trans_label
                self.bubble_containers[bubble_id] = container
                self.bubble_order.append(bubble_id)
                logger.info(f"✅ [UI_ADD_BUBBLE] 完成！bubble_id={bubble_id}, 總氣泡數={len(self.chat_bubbles)}")
                
                # 🔧 如果浮動模式開啟，同時更新浮動窗口（共用同一個 bubble_id）
                if self.floating_mode:
                    self._add_floating_bubble_with_id(bubble_id, speaker_name, original, translated, speaker_id)
                    
            except Exception as e:
                logger.error(f"❌ [UI_ADD_BUBBLE] 失敗：{e}", exc_info=True)
                raise
            
            # 清理舊氣泡 (超過 100 個)
            if len(self.bubble_order) > self.max_bubbles:
                oldest_id = self.bubble_order.pop(0)
                if oldest_id in self.bubble_containers: 
                    self.bubble_containers[oldest_id].destroy()
                    del self.bubble_containers[oldest_id]
                if oldest_id in self.chat_bubbles: 
                    del self.chat_bubbles[oldest_id]
                # 🔧 記錄已清理的 ID，避免無效更新
                self.cleaned_bubble_ids.add(oldest_id)
                logger.debug(f"🗑️ 已清理舊氣泡：{oldest_id[:8]}，總數={len(self.bubble_order)}")
            
            # 捲動到底部
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
            
            logger.debug(f"已新增氣泡：{bubble_id[:8]}... ({original[:30]}...)")
        
        self.after(0, _update)  # ✅ 手動包裝
        return bubble_id  # ✅ 立即返回 ID
    
    def update_chat_bubble(self, bubble_id: str, new_translated: str) -> None:
        """更新氣泡翻譯（同時更新主窗口同浮動窗口）"""
        def _update():
            # 🔧 FIX: 檢查主窗口氣泡是否存在
            if hasattr(self, 'chat_bubbles') and bubble_id in self.chat_bubbles:
                self.chat_bubbles[bubble_id].configure(text=new_translated)
                self.chat_scroll._parent_canvas.yview_moveto(1.0)
                logger.debug(f"✅ [MAIN_UPDATE] 成功更新主窗口氣泡 {bubble_id[:8]}")
            else:
                logger.debug(f"⚠️ [MAIN_UPDATE] 主窗口氣泡已清理 {bubble_id[:8]}")
            
            # 🔧 同時更新浮動窗口（即使主窗口氣泡被清理）
            if self.floating_mode:
                self.update_floating_bubble(bubble_id, new_translated)
        
        self.after(0, _update)
    
    def ask_open_audio_file(self) -> Optional[str]:
        fp = filedialog.askopenfilename(title="選擇音訊/影片檔案", 
            filetypes=[("媒體檔案", "*.mp3 *.wav *.mp4 *.m4a *.aac *.flac"), ("所有檔案", "*.*")])
        return fp if fp else None
    
    def ask_save_file(self, default_name="subtitle") -> Optional[str]:
        fp = filedialog.asksaveasfilename(title="儲存字幕檔案", initialfile=f"{default_name}.srt", 
            defaultextension=".srt", filetypes=[("SRT 字幕", "*.srt"), ("所有檔案", "*.*")])
        return fp if fp else None

    def show_info(self, title, msg): 
        messagebox.showinfo(title, msg)
    
    def show_error(self, title, msg): 
        messagebox.showerror(title, msg)
    
    # ==========================================
    # Floating Overlay Mode (Transparent Subtitle Window)
    # ==========================================
    def toggle_floating_mode(self) -> None:
        """Toggle Floating Overlay Mode On/Off"""
        if self.floating_mode:
            self._close_floating_window()
        else:
            self._open_floating_window()
    
    def _open_floating_window(self) -> None:
        """Open Floating Transparent Subtitle Window"""
        try:
            # 🔧 FIX: 用標準 Tkinter Toplevel 代替 CustomTkinter
            self.floating_window = tk.Toplevel(self)
            self.floating_window.title("浮動字幕")
            
            # Make window transparent and always on top
            self.floating_window.attributes("-topmost", True)  # Always on top
            self.floating_window.attributes("-alpha", 0.85)  # 85% opacity
            
            # Set window size and position
            self.floating_window.geometry("800x200+100+100")
            
            # Make window resizable
            self.floating_window.resizable(True, True)
            
            # 🔧 FIX: 唔好用 fg_color="transparent"，改用標準背景色
            self.floating_window.configure(bg="#0b0f19")
            
            # 🔧 FIX: 隱藏主窗口以節省資源
            if hasattr(self, 'master') and hasattr(self.master, 'withdraw'):
                self.master.withdraw()  # 隱藏主窗口
                logger.info("🔧 已隱藏主窗口以節省資源")
            
            # Create a frame for subtitles with semi-transparent background
            bubble_frame = ctk.CTkFrame(
                self.floating_window, 
                fg_color="#0b0f19",  # Dark background
                corner_radius=15,
                border_width=2,
                border_color=self.colors["primary"]
            )
            bubble_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create a scrollable label area for subtitles
            self.floating_chat_scroll = ctk.CTkScrollableFrame(
                bubble_frame, 
                fg_color="transparent",
                corner_radius=0
            )
            self.floating_chat_scroll.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Initialize storage for floating bubbles
            self.floating_chat_bubbles = {}
            self.floating_bubble_containers = {}
            self.floating_bubble_order = []
            
            # Handle window close
            self.floating_window.protocol("WM_DELETE_WINDOW", self._close_floating_window)
            
            # Update button text
            self.floating_btn.configure(text="❌ 關閉浮動模式", fg_color=self.colors["danger"])
            
            self.floating_mode = True
            logger.info("✅ 浮動字幕模式已開啟")
            
        except Exception as e:
            logger.error(f"開啟浮動窗口失敗：{e}", exc_info=True)
            self.show_error("錯誤", f"無法開啟浮動模式：{e}")
    
    def _close_floating_window(self) -> None:
        """Close Floating Window"""
        try:
            if self.floating_window and self.floating_window.winfo_exists():
                self.floating_window.destroy()
            
            self.floating_window = None
            self.floating_chat_bubbles = {}
            self.floating_bubble_containers = {}
            self.floating_bubble_order = []
            
            # 🔧 FIX: 重置 cleaned_bubble_ids（避免內存泄漏）
            self.cleaned_bubble_ids.clear()
            
            # 🔧 FIX: 顯示返主窗口
            if hasattr(self, 'master') and hasattr(self.master, 'deiconify'):
                self.master.deiconify()  # 顯示主窗口
                logger.info("🔧 已顯示主窗口")
            
            # Update button text
            self.floating_btn.configure(text="🪟 浮動字幕模式", fg_color=self.colors["primary"])
            
            self.floating_mode = False
            logger.info("✅ 浮動字幕模式已關閉")
            
        except Exception as e:
            logger.error(f"關閉浮動窗口失敗：{e}", exc_info=True)
    
    def cleanup_old_bubble_ids(self) -> None:
        """Periodically clean old bubble IDs to prevent memory growth"""
        # Keep only last 200 cleaned IDs (recent ones that might still get updates)
        if len(self.cleaned_bubble_ids) > 200:
            # Convert to list, keep last 200
            id_list = list(self.cleaned_bubble_ids)
            self.cleaned_bubble_ids = set(id_list[-200:])
            logger.debug(f"🧹 已清理舊 bubble ID 記錄，保留={len(self.cleaned_bubble_ids)}")
    
    # ==========================================
    # Font Size Control
    # ==========================================
    def cycle_font_size(self) -> None:
        """Cycle Through Font Size Presets"""
        # Define presets
        presets = [
            {"original": 11, "translated": 14, "label": "🔤 文字大小：小"},
            {"original": 13, "translated": 16, "label": "🔤 文字大小：標準"},
            {"original": 15, "translated": 18, "label": "🔤 文字大小：大"},
            {"original": 18, "translated": 22, "label": "🔤 文字大小：超大"}
        ]
        
        # Find current preset index
        current_idx = 1  # Default to standard
        for idx, preset in enumerate(presets):
            if preset["original"] == self.font_sizes["original"] and preset["translated"] == self.font_sizes["translated"]:
                current_idx = idx
                break
        
        # Move to next preset (cycle)
        next_idx = (current_idx + 1) % len(presets)
        next_preset = presets[next_idx]
        
        # Update font sizes
        self.font_sizes["original"] = next_preset["original"]
        self.font_sizes["translated"] = next_preset["translated"]
        
        # Update button text
        self.font_btn.configure(text=next_preset["label"])
        
        # Refresh all existing bubbles
        self._refresh_all_bubbles()
        
        logger.info(f"🔤 文字大小已更改：原文={self.font_sizes['original']}px, 譯文={self.font_sizes['translated']}px")
    
    def _refresh_all_bubbles(self) -> None:
        """Refresh All Bubbles with New Font Sizes"""
        def _update():
            try:
                # Refresh main window bubbles
                if hasattr(self, 'chat_bubbles'):
                    for bubble_id, trans_label in self.chat_bubbles.items():
                        # Update translated text font
                        trans_label.configure(font=ctk.CTkFont(size=self.font_sizes["translated"], weight="bold"))
                        
                        # Update original text font (need to find the parent bubble)
                        if bubble_id in self.bubble_containers:
                            bubble = self.bubble_containers[bubble_id]
                            for widget in bubble.winfo_children():
                                if isinstance(widget, ctk.CTkLabel):
                                    current_text = widget.cget("text")
                                    # Check if this is original text (italic)
                                    if widget.cget("font") and "italic" in str(widget.cget("font")):
                                        widget.configure(font=ctk.CTkFont(size=self.font_sizes["original"], slant="italic"))
                
                # Refresh floating window bubbles
                if self.floating_mode and hasattr(self, 'floating_chat_bubbles'):
                    for bubble_id, trans_label in self.floating_chat_bubbles.items():
                        trans_label.configure(font=ctk.CTkFont(size=self.font_sizes["translated"], weight="bold"))
                        
                        if bubble_id in self.floating_bubble_containers:
                            bubble = self.floating_bubble_containers[bubble_id]
                            for widget in bubble.winfo_children():
                                if isinstance(widget, ctk.CTkLabel):
                                    if widget.cget("font") and "italic" in str(widget.cget("font")):
                                        widget.configure(font=ctk.CTkFont(size=self.font_sizes["original"], slant="italic"))
                
                logger.info(f"✅ 已刷新所有氣泡字體大小")
            except Exception as e:
                logger.error(f"❌ 刷新氣泡失敗：{e}", exc_info=True)
        
        self.after(0, _update)
    
    def _add_floating_bubble_with_id(self, bubble_id: str, speaker_name: str, original: str, translated: str, speaker_id: int = 1) -> None:
        """Add bubble to floating window with shared bubble_id (internal use)"""
        if not self.floating_mode or not self.floating_window:
            logger.warning(f"⚠️ [FLOATING_BUBBLE] 浮動模式未開啟或窗口不存在")
            return
        
        logger.info(f"🪟 [FLOATING_BUBBLE] 準備建立浮動氣泡，bubble_id={bubble_id[:8]}, translated='{translated[:50]}...'")
        
        def _update():
            try:
                align = "w" if speaker_id == 1 else "e"
                bubble_color = "#1e293b" if speaker_id == 1 else "#064e3b"
                text_color = self.colors["primary"] if speaker_id == 1 else self.colors["success"]
                
                # Create container
                container = ctk.CTkFrame(self.floating_chat_scroll, fg_color="transparent")
                container.pack(fill="x", pady=5, padx=5)
                logger.debug(f"🪟 [FLOATING_BUBBLE] 容器已建立")
                
                # Create bubble
                bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=10)
                bubble.pack(anchor=align, ipadx=8, ipady=8)
                logger.debug(f"🪟 [FLOATING_BUBBLE] 氣泡已建立")
                
                # Original text (smaller font) - 使用動態字體大小
                ctk.CTkLabel(
                    bubble, text=original, 
                    font=ctk.CTkFont(size=self.font_sizes["original"], slant="italic"), 
                    text_color=self.colors["text_muted"], 
                    wraplength=600, justify="left"
                ).pack(anchor=align, padx=8, pady=(0, 2))
                logger.debug(f"🪟 [FLOATING_BUBBLE] 原文已加入")
                
                # Translated text (larger, bold) - 使用動態字體大小
                trans_label = ctk.CTkLabel(
                    bubble, text=translated, 
                    font=ctk.CTkFont(size=self.font_sizes["translated"], weight="bold"), 
                    text_color=self.colors["text_light"], 
                    wraplength=600, justify="left"
                )
                trans_label.pack(anchor=align, padx=8, pady=(0, 5))
                logger.debug(f"🪟 [FLOATING_BUBBLE] 譯文已加入：'{translated[:50]}...'")
                
                # Store references (USE SHARED bubble_id)
                self.floating_chat_bubbles[bubble_id] = trans_label
                self.floating_bubble_containers[bubble_id] = container
                self.floating_bubble_order.append(bubble_id)
                logger.info(f"✅ [FLOATING_BUBBLE] 完成！bubble_id={bubble_id[:8]}, 總氣泡數={len(self.floating_chat_bubbles)}")
                
                # Auto-scroll to bottom
                self.floating_chat_scroll._parent_canvas.yview_moveto(1.0)
                
                # Cleanup old bubbles (keep last 50)
                if len(self.floating_bubble_order) > self.max_floating_bubbles:
                    oldest_id = self.floating_bubble_order.pop(0)
                    if oldest_id in self.floating_bubble_containers:
                        self.floating_bubble_containers[oldest_id].destroy()
                        del self.floating_bubble_containers[oldest_id]
                    if oldest_id in self.floating_chat_bubbles:
                        del self.floating_chat_bubbles[oldest_id]
                    # 🔧 記錄已清理的 ID
                    self.cleaned_bubble_ids.add(oldest_id)
                    logger.debug(f"🪟 [FLOATING_BUBBLE] 清理舊氣泡：{oldest_id[:8]}，總數={len(self.floating_bubble_order)}")
                
            except Exception as e:
                logger.error(f"❌ [FLOATING_BUBBLE] 失敗：{e}", exc_info=True)
        
        self.after(0, _update)
    
    def update_floating_bubble(self, bubble_id: str, new_translated: str) -> None:
        """Update floating bubble translation - skip if already cleaned"""
        if not self.floating_mode:
            logger.debug(f"⚠️ [FLOATING_UPDATE] 浮動模式未開啟，bubble_id={bubble_id}")
            return
        
        # 🔧 FIX: 如果氣泡已被清理，跳過更新（避免無效操作）
        if bubble_id in self.cleaned_bubble_ids:
            logger.debug(f"⚠️ [FLOATING_UPDATE] 氣泡已清理，跳過更新 bubble_id={bubble_id[:8]}")
            return
        
        logger.debug(f"🪟 [FLOATING_UPDATE] 準備更新浮動氣泡，bubble_id={bubble_id[:8]}, translated='{new_translated[:50]}...'")
        
        def _update():
            try:
                # Check if bubble exists
                if hasattr(self, 'floating_chat_bubbles') and bubble_id in self.floating_chat_bubbles:
                    self.floating_chat_bubbles[bubble_id].configure(text=new_translated)
                    self.floating_chat_scroll._parent_canvas.yview_moveto(1.0)
                    logger.info(f"✅ [FLOATING_UPDATE] 成功更新！bubble_id={bubble_id[:8]}")
                else:
                    # 🔧 FIX: 如果氣泡被清理咗，但仲有更新過嚟（翻譯完成）
                    # 唔好顯示警告，因為係正常嘅（舊氣泡被清理）
                    logger.debug(f"⚠️ [FLOATING_UPDATE] 氣泡已清理（正常），bubble_id={bubble_id[:8]}, 總數={len(self.floating_chat_bubbles) if hasattr(self, 'floating_chat_bubbles') else 0}")
            except Exception as e:
                logger.error(f"❌ [FLOATING_UPDATE] 失敗：{e}", exc_info=True)
        
        self.after(0, _update)
    
    def _on_asr_backend_change(self, choice: str) -> None:
        default_url = BACKEND_DEFAULTS.get(choice, "")
        if default_url:
            self.asr_url_var.set(default_url)
    
    def _on_translate_backend_change(self, choice: str) -> None:
        default_url = BACKEND_DEFAULTS.get(choice, "")
        if default_url:
            self.translate_url_var.set(default_url)
    
    def _on_fetch_models(self) -> None:
        def fetch() -> None:
            try:
                url = self.asr_url_var.get().rstrip("/v1")
                response = requests.get(f"{url}/v1/models", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    model_ids = [m.get("id", "") for m in models]
                    self.after(0, lambda: self.show_info("LM Studio 模型", "\n".join(model_ids)))
                else:
                    self.after(0, lambda: self.show_error("錯誤", f"LM Studio 回應：{response.status_code}"))
            except Exception as e:
                self.after(0, lambda: self.show_error("錯誤", f"無法連接 LM Studio：{e}"))
        threading.Thread(target=fetch, daemon=True).start()
    
    def _on_save_settings(self):
        settings = {
            "asr_backend": self.asr_backend_var.get(),
            "asr_model": self.asr_model_var.get(),
            "asr_api_url": self.asr_url_var.get(),
            "asr_api_key": self.asr_key_var.get(),
            "translate_backend": self.translate_backend_var.get(),
            "translate_model": self.translate_model_var.get(),
            "translate_api_url": self.translate_url_var.get(),
            "translate_api_key": self.translate_key_var.get(),
            "vad_duration": self.vad_duration_var.get()
        }

        if self.controller and hasattr(self.controller, 'set_settings'):
            self.controller.set_settings(settings)
            self.show_info("成功", "設定已儲存！系統正在背景重新連接 API...")
        else:
            self.show_error("錯誤", "無法連接到系統後台")
