import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import uuid
from typing import Optional, Callable, Dict, Any, List
from logging_config import get_logger

logger = get_logger(__name__)

class MainUI(ctk.CTkFrame):
    def __init__(self, master, controller=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # 綁定邏輯控制器 (app.py 或 controller.py)
        self.controller = controller if controller else master
        
        # 設定整體 Grid 佈局 (1 行 2 列：Sidebar + MainContent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # 定義顏色主題 (深藍色調)
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
        
        # UI 變數 (用嚟儲存使用者嘅選擇，俾 Controller 讀取)
        self.device_var = ctk.StringVar(value="請先重新整理裝置...")
        self.src_lang_var = ctk.StringVar(value="auto")
        self.tgt_lang_var = ctk.StringVar(value="zh")
        self.asr_model_var = ctk.StringVar(value="Qwen3-ASR-0.6B")
        self.compute_device_var = ctk.StringVar(value="CPU")
        self.vad_duration_var = ctk.DoubleVar(value=1.5)
        self.use_full_model_var = ctk.BooleanVar(value=False)
        
        self._build_sidebar()
        self._build_main_container()
        
        self.switch_view("realtime")

    # ==========================================
    # 1. 構建左側導覽列 (Sidebar)
    # ==========================================
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#0f172a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1) 
        
        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="🌊 QwenASR", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.colors["primary"]
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))
        
        self.nav_buttons = {}
        nav_items = [
            ("realtime", "⚡ 即時翻譯"),
            ("batch", "📁 批量上傳"),
            ("settings", "⚙️ 系統設定")
        ]
        
        for idx, (view_id, text) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=text, font=ctk.CTkFont(size=15),
                fg_color="transparent", text_color=self.colors["text_muted"],
                hover_color=self.colors["bg_panel"], anchor="w", height=45,
                command=lambda vid=view_id: self.switch_view(vid)
            )
            btn.grid(row=idx, column=0, padx=15, pady=5, sticky="ew")
            self.nav_buttons[view_id] = btn

        self.status_indicator = ctk.CTkLabel(
            self.sidebar, text="🟢 系統就緒", font=ctk.CTkFont(size=12), text_color=self.colors["success"]
        )
        self.status_indicator.grid(row=6, column=0, padx=20, pady=20, sticky="w")

    # ==========================================
    # 2. 構建主內容區 (Main Container)
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
    # 3. 視圖：即時翻譯 (Real-time View)
    # ==========================================
    def _build_realtime_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # --- 頂部控制列 ---
        header = ctk.CTkFrame(frame, height=60, fg_color=self.colors["bg_panel"], corner_radius=15)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        # 音訊裝置選擇區
        device_frame = ctk.CTkFrame(header, fg_color="transparent")
        device_frame.pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(device_frame, text="🎤 音訊:", text_color=self.colors["text_muted"]).pack(side="left", padx=(0, 5))
        self.device_combo = ctk.CTkComboBox(device_frame, variable=self.device_var, values=["載入中..."], width=280, fg_color="#0f172a", border_color="#334155")
        self.device_combo.pack(side="left", padx=5)
        
        # 重新整理按鈕
        refresh_btn = ctk.CTkButton(device_frame, text="🔄", width=35, fg_color=self.colors["primary_muted"], hover_color=self.colors["primary"], command=self._on_refresh_devices)
        refresh_btn.pack(side="left", padx=5)

        # 語言選擇區
        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.pack(side="right", padx=15, pady=10)
        
        # 來源語言
        src_langs = {"自動偵測 (Auto)": "auto", "日文 (JA)": "ja", "英文 (EN)": "en", "中文 (ZH)": "zh", "韓文 (KO)": "ko"}
        self.src_lang_combo = ctk.CTkComboBox(lang_frame, values=list(src_langs.keys()), width=130, fg_color="#0f172a", border_color="#334155", 
                                              command=lambda choice: self.src_lang_var.set(src_langs[choice]))
        self.src_lang_combo.set("自動偵測 (Auto)")
        self.src_lang_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(lang_frame, text="➔", text_color=self.colors["text_muted"]).pack(side="left", padx=2)
        
        # 目標語言
        tgt_langs = {"繁體中文 (ZH)": "zh", "英文 (EN)": "en", "日文 (JA)": "ja", "韓文 (KO)": "ko"}
        self.tgt_lang_combo = ctk.CTkComboBox(lang_frame, values=list(tgt_langs.keys()), width=130, fg_color="#0f172a", border_color="#334155",
                                              command=lambda choice: self.tgt_lang_var.set(tgt_langs[choice]))
        self.tgt_lang_combo.set("繁體中文 (ZH)")
        self.tgt_lang_combo.pack(side="left", padx=5)

        # --- 對話/字幕顯示區 ---
        self.chat_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew")

        # --- 底部控制列 ---
        bottom_bar = ctk.CTkFrame(frame, height=80, fg_color=self.colors["bg_panel"], corner_radius=20)
        bottom_bar.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        
        self.record_btn = ctk.CTkButton(
            bottom_bar, text="🎤", width=60, height=60, corner_radius=30,
            font=ctk.CTkFont(size=24), fg_color=self.colors["danger"], hover_color=self.colors["danger_hover"],
            command=self._on_record_click,
            state="disabled" # 預設停用，等引擎載入完先解鎖
        )
        self.record_btn.pack(side="left", padx=20, pady=10)
        
        self.record_status_label = ctk.CTkLabel(bottom_bar, text="準備就緒 (READY)", font=ctk.CTkFont(family="Courier", size=14), text_color=self.colors["text_muted"])
        self.record_status_label.pack(side="left", padx=10)
        
        export_btn = ctk.CTkButton(bottom_bar, text="匯出 SRT", fg_color=self.colors["primary"], hover_color=self.colors["primary_hover"], width=100)
        export_btn.pack(side="right", padx=20)
        
        return frame

    # ==========================================
    # 4. 視圖：批量上傳 (Batch View)
    # ==========================================
    def _build_batch_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        title = ctk.CTkLabel(frame, text="批量音檔轉字幕", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors["text_light"])
        title.pack(anchor="w", pady=(0, 20))
        
        dropzone = ctk.CTkFrame(frame, height=200, fg_color=self.colors["bg_panel"], border_width=2, border_color="#334155")
        dropzone.pack(fill="x", pady=10)
        dropzone.pack_propagate(False)
        ctk.CTkLabel(dropzone, text="☁️\n點擊瀏覽或拖曳檔案到此處\n(支援 MP3, WAV, MP4)", font=ctk.CTkFont(size=16), text_color=self.colors["text_muted"], justify="center").pack(expand=True)
        
        settings_panel = ctk.CTkFrame(frame, fg_color=self.colors["bg_panel"], corner_radius=15)
        settings_panel.pack(fill="x", pady=20, ipady=10)
        ctk.CTkCheckBox(settings_panel, text="產生雙語 SRT 字幕檔", text_color=self.colors["text_light"]).pack(anchor="w", padx=20, pady=15)
        
        start_btn = ctk.CTkButton(frame, text="▶ 開始轉換", height=45, fg_color=self.colors["primary"])
        start_btn.pack(anchor="e", pady=20)
        return frame

    # ==========================================
    # 5. 視圖：系統設定 (Settings View)
    # ==========================================
    def _build_settings_view(self):
        frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        title = ctk.CTkLabel(frame, text="系統偏好設定", font=ctk.CTkFont(size=24, weight="bold"), text_color=self.colors["text_light"])
        title.pack(anchor="w", pady=(0, 20))
        
        panel = ctk.CTkFrame(frame, fg_color=self.colors["bg_panel"], corner_radius=15)
        panel.pack(fill="x", pady=10, ipadx=20, ipady=20)
        
        # ASR 模型選擇
        ctk.CTkLabel(panel, text="ASR 語音辨識模型", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        models = ["Qwen3-ASR-0.6B", "Qwen3-ASR-1.7B"]
        ctk.CTkComboBox(panel, variable=self.asr_model_var, values=models, width=400, fg_color="#0f172a").pack(anchor="w", pady=(0, 20))
        
        # 設備選擇
        ctk.CTkLabel(panel, text="硬體加速 (Compute Device)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        devices = ["CPU", "CUDA", "Vulkan (OpenVINO)"]
        ctk.CTkComboBox(panel, variable=self.compute_device_var, values=devices, width=400, fg_color="#0f172a").pack(anchor="w", pady=(0, 20))
        
        # VAD 靜音長度
        ctk.CTkLabel(panel, text="最小靜音切割長度 (VAD Duration - 秒)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        
        slider_frame = ctk.CTkFrame(panel, fg_color="transparent")
        slider_frame.pack(anchor="w", fill="x", pady=(0, 20))
        
        vad_slider = ctk.CTkSlider(slider_frame, variable=self.vad_duration_var, from_=0.5, to=3.0, number_of_steps=25, width=350)
        vad_slider.pack(side="left", padx=(0, 15))
        
        vad_value_label = ctk.CTkLabel(slider_frame, text="1.5s", font=ctk.CTkFont(family="Courier"))
        vad_value_label.pack(side="left")
        
        # 綁定 Slider 更新數值 Label
        vad_slider.configure(command=lambda val: vad_value_label.configure(text=f"{val:.1f}s"))
        
        ctk.CTkLabel(panel, text="翻譯模型進階設定", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 5))
        
        self.full_model_checkbox = ctk.CTkCheckBox(
            panel, 
            text="啟用滿血版翻譯模型 (fp16) - ⚠️ 建議僅在有獨立 GPU 時開啟", 
            variable=self.use_full_model_var,
            text_color=self.colors["text_light"]
        )
        self.full_model_checkbox.pack(anchor="w", pady=(0, 20))
        
        save_btn = ctk.CTkButton(frame, text="💾 儲存設定", height=45, fg_color=self.colors["primary"], 
                                 command=self._on_save_settings)
        save_btn.pack(anchor="e", pady=20)
        
        return frame

    # ==========================================
    # UI 公開方法 (供 Controller 呼叫/獲取資料)
    # (全部使用 self.after 包裝，確保跨執行緒安全)
    # ==========================================
    def set_device_list(self, devices: list, default_index: int = 0):
        """由 Controller 呼叫，更新音訊裝置清單"""
        def _update():
            if devices:
                self.device_combo.configure(values=devices)
                self.device_var.set(devices[default_index])
            else:
                self.device_combo.configure(values=["無可用音訊裝置"])
                self.device_var.set("無可用音訊裝置")
        self.after(0, _update)
            
    def set_status(self, text: str, color: str = None):
        """由 Controller 呼叫，更新左下角系統狀態指示器"""
        def _update():
            if color:
                self.status_indicator.configure(text=text, text_color=color)
            else:
                self.status_indicator.configure(text=text, text_color=self.colors["text_muted"])
        self.after(0, _update)

    def enable_record_button(self, enabled: bool):
        """由 Controller 呼叫，啟用或停用錄音按鈕"""
        def _update():
            state = "normal" if enabled else "disabled"
            self.record_btn.configure(state=state)
        self.after(0, _update)

    def get_selected_device(self) -> str:
        return self.device_var.get()

    def get_selected_languages(self):
        """回傳 (來源語言代碼, 目標語言代碼)"""
        return self.src_lang_var.get(), self.tgt_lang_var.get()
        
    def get_settings(self):
        """回傳系統設定"""
        return {
            "model": self.asr_model_var.get(),
            "device": self.compute_device_var.get(),
            "vad_duration": self.vad_duration_var.get(),
            "use_full_model": self.use_full_model_var.get() # <--- 新增呢行
        }

    # ==========================================
    # UI 互動邏輯
    # ==========================================
    def switch_view(self, view_id):
        for view in self.views.values():
            view.grid_forget()
        for btn in self.nav_buttons.values():
            btn.configure(fg_color="transparent", text_color=self.colors["text_muted"])
            
        self.views[view_id].grid(row=0, column=0, sticky="nsew")
        self.nav_buttons[view_id].configure(fg_color=self.colors["primary_muted"], text_color=self.colors["primary"])

    def _on_refresh_devices(self):
        """點擊重新整理按鈕"""
        self.device_combo.configure(values=["搜尋裝置中..."])
        self.device_var.set("搜尋裝置中...")
        self.update() # 強制刷新 UI
        if self.controller and hasattr(self.controller, 'refresh_devices'):
            self.controller.refresh_devices()

    def _on_record_click(self):
        """處理錄音按鈕點擊"""
        # 修正為呼叫由 app.py 綁定過來的 on_record_toggle
        if hasattr(self, 'on_record_toggle') and callable(self.on_record_toggle):
            self.on_record_toggle()

    def update_record_state(self, is_recording: bool):
        def _update():
            self.is_rec = is_recording
            if is_recording:
                self.record_btn.configure(text="■", fg_color=self.colors["bg_panel"], hover_color="#334155")
                self.record_status_label.configure(text="LISTENING...", text_color=self.colors["success"])
            else:
                self.record_btn.configure(text="🎤", fg_color=self.colors["danger"], hover_color=self.colors["danger_hover"])
                self.record_status_label.configure(text="PAUSED", text_color=self.colors["text_muted"])
        self.after(0, _update)

    # 記得喺 ui.py 最頂部加入: import uuid

    def add_chat_bubble(self, speaker_name: str, original: str, translated: str, speaker_id: int = 1) -> str:
        """新增對話氣泡，並回傳專屬的 bubble_id"""
        import uuid
        bubble_id = str(uuid.uuid4())
        
        def _update(s_id=speaker_id, s_name=speaker_name, orig=original, trans=translated, b_id=bubble_id):
            if not hasattr(self, 'chat_bubbles'):
                self.chat_bubbles = {}
                
            # 呢度已經全部改用 s_id，唔會再報錯
            if s_id == 1:
                align, bubble_color, text_color = "w", "#1e293b", self.colors["primary"]
            else:
                align, bubble_color, text_color = "e", "#064e3b", self.colors["success"]

            container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
            container.pack(fill="x", pady=10, padx=10)

            bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=15)
            bubble.pack(anchor=align, ipadx=10, ipady=10)

            time_str = datetime.now().strftime("%H:%M:%S")
            header = ctk.CTkFrame(bubble, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(5, 5))
            
            # 呢度都全部改用咗 s_id 同 s_name
            if s_id == 1:
                ctk.CTkLabel(header, text=s_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_color).pack(side="left")
                ctk.CTkLabel(header, text=time_str, font=ctk.CTkFont(family="Courier", size=10), text_color=self.colors["text_muted"]).pack(side="left", padx=10)
            else:
                ctk.CTkLabel(header, text=s_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_color).pack(side="right")
                ctk.CTkLabel(header, text=time_str, font=ctk.CTkFont(family="Courier", size=10), text_color=self.colors["text_muted"]).pack(side="right", padx=10)

            ctk.CTkLabel(bubble, text=orig, font=ctk.CTkFont(size=13, slant="italic"), text_color=self.colors["text_muted"], wraplength=500, justify="left").pack(anchor=align, padx=10, pady=(0, 2))
            
            trans_label = ctk.CTkLabel(bubble, text=trans, font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["text_light"], wraplength=500, justify="left")
            trans_label.pack(anchor=align, padx=10, pady=(0, 5))
            
            self.chat_bubbles[b_id] = trans_label
            self.chat_scroll._parent_canvas.yview_moveto(1.0)
            
        self.after(0, _update)
        return bubble_id
    
    def update_chat_bubble(self, bubble_id: str, new_translated: str) -> None:
        """根據 bubble_id 更新譯文內容"""
        def _update() -> None:
            if hasattr(self, 'chat_bubbles') and bubble_id in self.chat_bubbles:
                # 找到對應的氣泡，只更新文字內容
                self.chat_bubbles[bubble_id].configure(text=new_translated)
                # 畫面自動捲動到最底
                self.chat_scroll._parent_canvas.yview_moveto(1.0)
            else:
                logger.warning(f"找不到 bubble_id: {bubble_id}")
                
        self.after(0, _update)
    
    def _on_save_settings(self):
        """當使用者點擊『儲存設定』時觸發"""
        # 1. 喺 UI 攞返晒所有變數嘅最新數值
        settings = {
            "model": self.asr_model_var.get(),
            "device": self.compute_device_var.get(),
            "vad_duration": self.vad_duration_var.get(),
            "use_full_model": self.use_full_model_var.get()
        }

        # 2. 透過 Controller 將設定傳落去 AI 引擎
        if hasattr(self.controller, 'set_settings'):
            # 喺 controller.py 入面我哋寫咗對應嘅處理邏輯
            self.controller.set_settings(settings)
            
            # 3. 彈個通知話俾用家聽搞掂咗
            messagebox.showinfo("Success", "Settings updated! The AI engines will reload with new parameters.")
        else:
            print("[ERROR] Controller 冇 set_settings 呢個方法，請檢查 controller.py")