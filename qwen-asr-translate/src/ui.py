"""
QwenASR Pro - Main UI Component
Professional-grade UI with collapsible sidebar, proper controller connection, and complete button events
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import uuid
from typing import Optional, Callable, Dict, Any, List
from logging_config import get_logger

logger = get_logger(__name__)


class MainUI(ctk.CTkFrame):
    """Main UI Component - Professional Grade"""
    
    def __init__(self, master, controller=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # 🔧 FIX 1: Proper Controller Connection
        if controller:
            self.controller = controller
        elif hasattr(master, 'controller'):
            self.controller = master.controller
        else:
            self.controller = master
        
        # Setup Grid Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Color Theme (Dark Blue)
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
        
        # 🔧 FIX 2: Correct Model Paths (Qwen3-ASR, NOT old Qwen-Audio)
        self.asr_repo_map = {
            "Qwen3-ASR-0.6B (極速/省 RAM)": "Qwen/Qwen3-ASR-0.6B",
            "Qwen3-ASR-1.7B (高準確度)": "Qwen/Qwen3-ASR-1.7B"
        }
        self.device_map = {
            "CPU": "cpu",
            "CUDA (Nvidia GPU)": "cuda"
        }
        
        # UI Variables
        self.device_var = ctk.StringVar(value="請先重新整理裝置...")
        self.src_lang_var = ctk.StringVar(value="auto")
        self.tgt_lang_var = ctk.StringVar(value="zh")
        self.asr_model_var = ctk.StringVar(value=list(self.asr_repo_map.keys())[1])
        self.compute_device_var = ctk.StringVar(value="CUDA (Nvidia GPU)")
        self.vad_duration_var = ctk.DoubleVar(value=1.5)
        self.use_full_model_var = ctk.BooleanVar(value=False)
        
        # Callback Hooks (bound by app.py)
        self.on_record_toggle: Optional[Callable] = None
        self.on_upload_file: Optional[Callable] = None
        self.on_save_subtitle: Optional[Callable] = None
        
        # Build UI
        self._build_sidebar()
        self._build_main_container()
        self.switch_view("realtime")
    
    # ==========================================
    # 1. Sidebar (Collapsible)
    # ==========================================
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#0f172a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)  # 🔧 FIX 3: Lock width to prevent text expansion
        self.sidebar.grid_rowconfigure(5, weight=1) 
        
        self.menu_expanded = True
        
        # Header (Hamburger + Logo)
        self.sidebar_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_header.grid(row=0, column=0, pady=(20, 20), sticky="ew")
        
        self.toggle_btn = ctk.CTkButton(
            self.sidebar_header, text="☰", width=40, height=40, font=ctk.CTkFont(size=20),
            fg_color="transparent", hover_color=self.colors["bg_panel"], command=self.toggle_menu
        )
        self.toggle_btn.pack(side="left", padx=10)
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar_header, text="QwenASR", font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors["primary"]
        )
        self.logo_label.pack(side="left", padx=5)
        
        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("realtime", "⚡", "即時翻譯"),
            ("batch", "📁", "批量上傳"),
            ("settings", "⚙️", "系統設定")
        ]
        
        for idx, (view_id, icon, text) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=f"{icon} {text}", font=ctk.CTkFont(size=15),
                fg_color="transparent", text_color=self.colors["text_muted"],
                hover_color=self.colors["bg_panel"], anchor="w", height=45,
                command=lambda vid=view_id: self.switch_view(vid)
            )
            btn.grid(row=idx, column=0, padx=10, pady=5, sticky="ew")
            self.nav_buttons[view_id] = btn

        self.status_indicator = ctk.CTkLabel(
            self.sidebar, text="🟢 系統就緒", font=ctk.CTkFont(size=12), text_color=self.colors["success"]
        )
        self.status_indicator.grid(row=6, column=0, padx=20, pady=20, sticky="w")
    
    def toggle_menu(self):
        """Toggle Sidebar Collapsed/Expanded State"""
        self.menu_expanded = not self.menu_expanded
        
        if self.menu_expanded:
            # Expand
            self.sidebar.configure(width=200)
            self.logo_label.pack(side="left", padx=5)
            self.nav_buttons["realtime"].configure(text="⚡ 即時翻譯")
            self.nav_buttons["batch"].configure(text="📁 批量上傳")
            self.nav_buttons["settings"].configure(text="⚙️ 系統設定")
            self.status_indicator.configure(text="🟢 系統就緒")
        else:
            # Collapse
            self.sidebar.configure(width=65)
            self.logo_label.pack_forget()
            self.nav_buttons["realtime"].configure(text="⚡")
            self.nav_buttons["batch"].configure(text="📁")
            self.nav_buttons["settings"].configure(text="⚙️")
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
        
        # Header (Device + Language)
        header = ctk.CTkFrame(frame, height=60, fg_color=self.colors["bg_panel"], corner_radius=15)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        # Device Selection
        device_frame = ctk.CTkFrame(header, fg_color="transparent")
        device_frame.pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(device_frame, text="🎤 音訊:", text_color=self.colors["text_muted"]).pack(side="left", padx=(0, 5))
        self.device_combo = ctk.CTkComboBox(device_frame, variable=self.device_var, values=["載入中..."], width=280, fg_color="#0f172a", border_color="#334155")
        self.device_combo.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(device_frame, text="🔄", width=35, fg_color=self.colors["primary_muted"], hover_color=self.colors["primary"], command=self._on_refresh_devices)
        refresh_btn.pack(side="left", padx=5)

        # Language Selection
        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.pack(side="right", padx=15, pady=10)
        
        src_langs = {"自動偵測 (Auto)": "auto", "日文 (JA)": "ja", "英文 (EN)": "en", "中文 (ZH)": "zh", "韓文 (KO)": "ko"}
        self.src_lang_combo = ctk.CTkComboBox(lang_frame, values=list(src_langs.keys()), width=130, fg_color="#0f172a", border_color="#334155", 
            command=lambda choice: self.src_lang_var.set(src_langs[choice]))
        self.src_lang_combo.set("自動偵測 (Auto)")
        self.src_lang_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(lang_frame, text="➔", text_color=self.colors["text_muted"]).pack(side="left", padx=2)
        
        tgt_langs = {"繁體中文 (ZH)": "zh", "英文 (EN)": "en", "日文 (JA)": "ja", "韓文 (KO)": "ko"}
        self.tgt_lang_combo = ctk.CTkComboBox(lang_frame, values=list(tgt_langs.keys()), width=130, fg_color="#0f172a", border_color="#334155",
            command=lambda choice: self.tgt_lang_var.set(tgt_langs[choice]))
        self.tgt_lang_combo.set("繁體中文 (ZH)")
        self.tgt_lang_combo.pack(side="left", padx=5)

        # Chat Area
        self.chat_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew")

        # Bottom Bar (Record + Export)
        bottom_bar = ctk.CTkFrame(frame, height=80, fg_color=self.colors["bg_panel"], corner_radius=20)
        bottom_bar.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        
        self.record_btn = ctk.CTkButton(
            bottom_bar, text="🎤", width=60, height=60, corner_radius=30,
            font=ctk.CTkFont(size=24), fg_color=self.colors["danger"], hover_color=self.colors["danger_hover"],
            command=self._on_record_click, state="disabled"
        )
        self.record_btn.pack(side="left", padx=20, pady=10)
        
        self.record_status_label = ctk.CTkLabel(bottom_bar, text="準備就緒 (READY)", font=ctk.CTkFont(family="Courier", size=14), text_color=self.colors["text_muted"])
        self.record_status_label.pack(side="left", padx=10)
        
        # 🔧 FIX 4: Reconnect Export Button
        export_btn = ctk.CTkButton(bottom_bar, text="匯出 SRT", fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"], width=100, command=self._on_export_click)
        export_btn.pack(side="right", padx=20)
        
        return frame
    
    # ==========================================
    # 4. Batch View
    # ==========================================
    def _build_batch_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        title = ctk.CTkLabel(frame, text="批量音檔轉字幕", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors["text_light"])
        title.pack(anchor="w", pady=(0, 20))
        
        dropzone = ctk.CTkFrame(frame, height=200, fg_color=self.colors["bg_panel"], border_width=2, border_color="#334155")
        dropzone.pack(fill="x", pady=10)
        dropzone.pack_propagate(False)
        ctk.CTkLabel(dropzone, text="☁️\n點擊此處瀏覽檔案\n(支援 MP3, WAV, MP4)", font=ctk.CTkFont(size=16), text_color=self.colors["text_muted"], justify="center").pack(expand=True)
        
        # 🔧 FIX 5: Reconnect Dropzone Click
        dropzone.bind("<Button-1>", lambda e: self._on_batch_start())
        for child in dropzone.winfo_children():
            child.bind("<Button-1>", lambda e: self._on_batch_start())
        
        settings_panel = ctk.CTkFrame(frame, fg_color=self.colors["bg_panel"], corner_radius=15)
        settings_panel.pack(fill="x", pady=20, ipady=10)
        ctk.CTkCheckBox(settings_panel, text="產生雙語 SRT 字幕檔", text_color=self.colors["text_light"]).pack(anchor="w", padx=20, pady=15)
        
        # 🔧 FIX 6: Reconnect Start Button
        start_btn = ctk.CTkButton(frame, text="▶ 選擇檔案並轉換", height=45, fg_color=self.colors["primary"], command=self._on_batch_start)
        start_btn.pack(anchor="e", pady=20)
        return frame
    
    # ==========================================
    # 5. Settings View
    # ==========================================
    def _build_settings_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        title = ctk.CTkLabel(frame, text="系統偏好設定", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors["text_light"])
        title.pack(anchor="w", pady=(0, 20))
        
        panel = ctk.CTkFrame(frame, fg_color=self.colors["bg_panel"], corner_radius=15)
        panel.pack(fill="x", pady=10, ipadx=20, ipady=20)
        
        # ASR Model Selection
        ctk.CTkLabel(panel, text="ASR 語音辨識模型", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkComboBox(panel, variable=self.asr_model_var, values=list(self.asr_repo_map.keys()), width=400, fg_color="#0f172a").pack(anchor="w", pady=(0, 20))
        
        # Device Selection
        ctk.CTkLabel(panel, text="硬體加速 (Compute Device)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkComboBox(panel, variable=self.compute_device_var, values=list(self.device_map.keys()), width=400, fg_color="#0f172a").pack(anchor="w", pady=(0, 20))
        
        # VAD Duration
        ctk.CTkLabel(panel, text="最小靜音切割長度 (VAD Duration - 秒)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
        slider_frame = ctk.CTkFrame(panel, fg_color="transparent")
        slider_frame.pack(anchor="w", fill="x", pady=(0, 20))
        
        vad_slider = ctk.CTkSlider(slider_frame, variable=self.vad_duration_var, from_=0.5, to=3.0, number_of_steps=25, width=350)
        vad_slider.pack(side="left", padx=(0, 15))
        
        vad_value_label = ctk.CTkLabel(slider_frame, text="1.5s", font=ctk.CTkFont(family="Courier"))
        vad_value_label.pack(side="left")
        vad_slider.configure(command=lambda val: vad_value_label.configure(text=f"{val:.1f}s"))
        
        # Translation Model
        ctk.CTkLabel(panel, text="翻譯模型進階設定", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 5))
        
        self.full_model_checkbox = ctk.CTkCheckBox(
            panel, text="啟用滿血版翻譯模型 (fp16) - ⚠️ 建議僅在有獨立 GPU 時開啟", 
            variable=self.use_full_model_var, text_color=self.colors["text_light"]
        )
        self.full_model_checkbox.pack(anchor="w", pady=(0, 20))
        
        # 🔧 FIX 7: Reconnect Save Button
        save_btn = ctk.CTkButton(frame, text="💾 儲存並套用設定", height=45, fg_color=self.colors["primary"], command=self._on_save_settings)
        save_btn.pack(anchor="e", pady=20)
        
        return frame
    
    # ==========================================
    # Public Methods (for Controller)
    # ==========================================
    def set_device_list(self, devices: list, default_index: int = 0):
        def _update():
            if devices:
                self.device_combo.configure(values=devices)
                self.device_var.set(devices[default_index])
            else:
                self.device_combo.configure(values=["無可用音訊裝置"])
                self.device_var.set("無可用音訊裝置")
            self.after(0, _update)
    
    def set_status(self, text: str, color: str = None):
        def _update():
            if color:
                self.status_indicator.configure(text=text, text_color=color)
            else:
                self.status_indicator.configure(text=text, text_color=self.colors["text_muted"])
            self.after(0, _update)

    def enable_record_button(self, enabled: bool):
        def _update():
            state = "normal" if enabled else "disabled"
            self.record_btn.configure(state=state)
            self.after(0, _update)

    def get_selected_device(self) -> str:
        return self.device_var.get()

    def get_selected_languages(self):
        return self.src_lang_var.get(), self.tgt_lang_var.get()
    
    # ==========================================
    # UI Interaction Logic
    # ==========================================
    def switch_view(self, view_id):
        for view in self.views.values():
            view.grid_forget()
        for btn in self.nav_buttons.values():
            btn.configure(fg_color="transparent", text_color=self.colors["text_muted"])
        
        self.views[view_id].grid(row=0, column=0, sticky="nsew")
        self.nav_buttons[view_id].configure(fg_color=self.colors["primary_muted"], text_color=self.colors["primary"])
    
    # 🔧 FIX 8: All Button Event Handlers
    def _on_refresh_devices(self):
        """Refresh Device List"""
        self.device_combo.configure(values=["搜尋裝置中..."])
        self.device_var.set("搜尋裝置中...")
        self.update()
        if self.controller and hasattr(self.controller, 'get_audio_devices'):
            devices = self.controller.get_audio_devices()
            self.set_device_list(devices)
    
    def _on_record_click(self):
        """Record Button Click"""
        if hasattr(self, 'on_record_toggle') and callable(self.on_record_toggle):
            self.on_record_toggle()
    
    def _on_export_click(self):
        """Export SRT Button Click"""
        if hasattr(self, 'on_save_subtitle') and callable(self.on_save_subtitle):
            self.on_save_subtitle()
    
    def _on_batch_start(self):
        """Batch Upload Button Click"""
        if hasattr(self, 'on_upload_file') and callable(self.on_upload_file):
            self.on_upload_file()
    
    def update_record_state(self, is_recording: bool):
        def _update():
            if is_recording:
                self.record_btn.configure(text="■", fg_color=self.colors["bg_panel"], hover_color="#334155")
                self.record_status_label.configure(text="LISTENING...", text_color=self.colors["success"])
            else:
                self.record_btn.configure(text="🎤", fg_color=self.colors["danger"], hover_color=self.colors["danger_hover"])
                self.record_status_label.configure(text="PAUSED", text_color=self.colors["text_muted"])
            self.after(0, _update)
    
    def add_chat_bubble(self, speaker_name: str, original: str, translated: str, speaker_id: int = 1) -> str:
        """Add Chat Bubble with Auto-Cleanup"""
        bubble_id = str(uuid.uuid4())
        
        def _update(s_id=speaker_id, s_name=speaker_name, orig=original, trans=translated, b_id=bubble_id):
            if not hasattr(self, 'chat_bubbles'):
                self.chat_bubbles = {}
                self.bubble_containers = {} 
                self.bubble_order = [] 
            
            align, bubble_color, text_color = ("w", "#1e293b", self.colors["primary"]) if s_id == 1 else ("e", "#064e3b", self.colors["success"])

            container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
            container.pack(fill="x", pady=10, padx=10)

            bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=15)
            bubble.pack(anchor=align, ipadx=10, ipady=10)

            time_str = datetime.now().strftime("%H:%M:%S")
            header = ctk.CTkFrame(bubble, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(5, 5))
            
            side_align = "left" if s_id == 1 else "right"
            ctk.CTkLabel(header, text=s_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_color).pack(side=side_align)
            ctk.CTkLabel(header, text=time_str, font=ctk.CTkFont(family="Courier", size=10), text_color=self.colors["text_muted"]).pack(side=side_align, padx=10)

            ctk.CTkLabel(bubble, text=orig, font=ctk.CTkFont(size=13, slant="italic"), text_color=self.colors["text_muted"], wraplength=500, justify="left").pack(anchor=align, padx=10, pady=(0, 2))
            trans_label = ctk.CTkLabel(bubble, text=trans, font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["text_light"], wraplength=500, justify="left")
            trans_label.pack(anchor=align, padx=10, pady=(0, 5))
            
            self.chat_bubbles[b_id] = trans_label
            self.bubble_containers[b_id] = container
            self.bubble_order.append(b_id)
            
            # Auto-cleanup (max 100 bubbles)
            MAX_BUBBLES = 100
            if len(self.bubble_order) > MAX_BUBBLES:
                oldest_id = self.bubble_order.pop(0)
                if oldest_id in self.bubble_containers:
                    self.bubble_containers[oldest_id].destroy()
                    del self.bubble_containers[oldest_id]
                if oldest_id in self.chat_bubbles:
                    del self.chat_bubbles[oldest_id]
            
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
            
            self.after(0, _update)
        return bubble_id
    
    def update_chat_bubble(self, bubble_id: str, new_translated: str) -> None:
        """Update Existing Chat Bubble"""
        def _update() -> None:
            if hasattr(self, 'chat_bubbles') and bubble_id in self.chat_bubbles:
                self.chat_bubbles[bubble_id].configure(text=new_translated)
                self.chat_scroll._parent_canvas.yview_moveto(1.0)
            self.after(0, _update)
    
    # 🔧 FIX 9: File Dialog Helpers
    def ask_open_audio_file(self) -> Optional[str]:
        """Open File Dialog for Audio Files"""
        filepath = filedialog.askopenfilename(
            title="選擇音訊/影片檔案",
            filetypes=[("媒體檔案", "*.mp3 *.wav *.mp4 *.m4a *.aac *.flac"), ("所有檔案", "*.*")]
        )
        return filepath if filepath else None
    
    def ask_save_file(self, default_name="subtitle") -> Optional[str]:
        """Save File Dialog"""
        filepath = filedialog.asksaveasfilename(
            title="儲存字幕檔案",
            initialfile=f"{default_name}.srt",
            defaultextension=".srt",
            filetypes=[("SRT 字幕", "*.srt"), ("所有檔案", "*.*")]
        )
        return filepath if filepath else None

    def show_info(self, title, msg):
        """Show Info Message Box"""
        messagebox.showinfo(title, msg)
    
    def show_error(self, title, msg):
        """Show Error Message Box"""
        messagebox.showerror(title, msg)
    
    # 🔧 FIX 10: Save Settings with Correct Model Paths
    def _on_save_settings(self):
        """Save Settings with Model Path Mapping"""
        selected_ui_model = self.asr_model_var.get()
        real_model_repo = self.asr_repo_map.get(selected_ui_model, "Qwen/Qwen3-ASR-0.6B")
        
        selected_ui_device = self.compute_device_var.get()
        real_device = self.device_map.get(selected_ui_device, "cpu")

        settings = {
            "model": real_model_repo,  # ✅ Correct PyTorch path
            "device": real_device,     # ✅ "cpu" or "cuda"
            "vad_duration": self.vad_duration_var.get(),
            "use_full_model": self.use_full_model_var.get()
        }

        if self.controller and hasattr(self.controller, 'set_settings'):
            self.controller.set_settings(settings)
            self.show_info("成功", "設定已儲存！\n系統正在背景重新載入模型...")
        else:
            logger.error("Controller 找不到 set_settings 函數")
            self.show_error("錯誤", "無法連接到系統後台，請重啟應用程式。")
