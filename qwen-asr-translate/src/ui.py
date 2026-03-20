"""
UI Layer - 所有使用者介面組件
負責顯示和使用者互動，與業務邏輯分離
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Callable, Optional, List
from datetime import datetime


class SubtitleOverlay(ctk.CTkToplevel):
    """懸浮字幕條：無邊框、半透明、永遠置頂"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        self.configure(fg_color="#000000")
        
        width, height = 750, 110
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = int(screen_height * 0.8)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.container = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=12, 
                                      border_width=1, border_color="#1e293b")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        self.color_bar = ctk.CTkFrame(self.container, width=6, fg_color="#3b82f6", 
                                      corner_radius=3)
        self.color_bar.pack(side="left", fill="y", padx=(15, 10), pady=15)

        self.text_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.text_frame.pack(side="left", fill="both", expand=True, pady=12, padx=(0, 15))

        self.header_frame = ctk.CTkFrame(self.text_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 4))

        self.speaker_badge = ctk.CTkLabel(
            self.header_frame, text="SPEAKER #1", font=("Arial", 10, "bold"),
            fg_color="#1e3a8a", text_color="#60a5fa", corner_radius=4, padx=6, pady=2
        )
        self.speaker_badge.pack(side="left")

        self.close_btn = ctk.CTkLabel(self.header_frame, text="×", font=("Arial", 16), 
                                      text_color="#64748b", cursor="hand2")
        self.close_btn.pack(side="right")
        self.close_btn.bind("<Button-1>", lambda e: self.withdraw())

        self.label_orig = ctk.CTkLabel(
            self.text_frame, text="", font=("Arial", 13, "italic"),
            text_color="#94a3b8", wraplength=650, justify="left"
        )
        self.label_orig.pack(anchor="w", pady=(0, 2))

        self.label_trans = ctk.CTkLabel(
            self.text_frame, text="等待語音輸入...", font=("Microsoft YaHei", 22, "bold"),
            text_color="#ffffff", wraplength=650, justify="left"
        )
        self.label_trans.pack(anchor="w")

        for element in [self.container, self.text_frame, self.header_frame, 
                        self.label_orig, self.label_trans]:
            element.bind("<Button-1>", self.start_move)
            element.bind("<B1-Motion>", self.do_move)

    def start_move(self, event):
        self._x = event.x_root - self.winfo_x()
        self._y = event.y_root - self.winfo_y()

    def do_move(self, event):
        x = event.x_root - self._x
        y = event.y_root - self._y
        self.geometry(f"+{x}+{y}")

    def update_text(self, orig, trans, speaker_id=1):
        """根據 Speaker ID 動態改變顏色與文字"""
        if speaker_id == 1:
            color_main = "#3b82f6"  # 藍色
            color_bg = "#1e3a8a"
            speaker_name = "SPEAKER 1"
        else:
            color_main = "#10b981"  # 綠色
            color_bg = "#064e3b"
            speaker_name = "SPEAKER 2"

        self.color_bar.configure(fg_color=color_main)
        self.speaker_badge.configure(text=speaker_name, fg_color=color_bg, 
                                     text_color=color_main)
        self.label_orig.configure(text=orig)
        self.label_trans.configure(text=trans)


class SettingsPanel(ctk.CTkToplevel):
    """設置面板 - 系統偏好設定"""
    
    def __init__(self, parent, on_save: Optional[Callable] = None):
        super().__init__(parent)
        self.title("設置")
        self.geometry("500x400")
        self.resizable(False, False)
        self.on_save = on_save
        
        # 標題
        title_label = ctk.CTkLabel(
            self, text="⚙️ 應用程式設置", 
            font=("Arial", 16, "bold"), text_color="#e2e8f0"
        )
        title_label.pack(pady=15)
        
        # 設定框架
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 目標語言選擇
        ctk.CTkLabel(settings_frame, text="翻譯目標語言:", 
                     font=("Arial", 12), text_color="#cbd5e1").pack(anchor="w", pady=(10, 5))
        
        self.language_var = ctk.StringVar(value="en")
        lang_menu = ctk.CTkComboBox(
            settings_frame, values=["en (English)", "zh (中文)", "ja (日本語)", "ko (한국어)", "es (Español)", "fr (Français)"],
            variable=self.language_var, width=350, fg_color="#1e293b"
        )
        lang_menu.pack(anchor="w", pady=(0, 15))
        
        # 說話者分離開關
        self.diarization_var = ctk.BooleanVar(value=True)
        diarization_check = ctk.CTkCheckBox(
            settings_frame, text="啟用說話者分離 (Speaker Diarization)",
            variable=self.diarization_var, fg_color="#3b82f6",
            font=("Arial", 11), text_color="#cbd5e1"
        )
        diarization_check.pack(anchor="w", pady=10)
        
        # 雙語字幕開關
        self.bilingual_var = ctk.BooleanVar(value=True)
        bilingual_check = ctk.CTkCheckBox(
            settings_frame, text="產生雙語 SRT 字幕檔",
            variable=self.bilingual_var, fg_color="#3b82f6",
            font=("Arial", 11), text_color="#cbd5e1"
        )
        bilingual_check.pack(anchor="w", pady=10)
        
        # ASR 模型選擇
        ctk.CTkLabel(settings_frame, text="ASR 模型:", 
                     font=("Arial", 12), text_color="#cbd5e1").pack(anchor="w", pady=(15, 5))
        
        self.asr_model_var = ctk.StringVar(value="qwen3-0.6b")
        asr_menu = ctk.CTkComboBox(
            settings_frame, values=["Qwen3-ASR-0.6B (快速)", "Qwen3-ASR-1.7B (準確)"],
            variable=self.asr_model_var, width=350, fg_color="#1e293b"
        )
        asr_menu.pack(anchor="w", pady=(0, 20))
        
        # 儲存按鈕
        save_btn = ctk.CTkButton(
            settings_frame, text="💾 儲存設置", height=35,
            fg_color="#3b82f6", hover_color="#2563eb",
            command=self.save_settings
        )
        save_btn.pack(pady=10)
    
    def save_settings(self):
        """保存設置並調用回調"""
        if self.on_save:
            settings = {
                "language": self.language_var.get().split()[0],  # 提取語言代碼
                "diarization": self.diarization_var.get(),
                "bilingual": self.bilingual_var.get(),
                "asr_model": self.asr_model_var.get()
            }
            self.on_save(settings)
        messagebox.showinfo("完成", "設置已儲存")
        self.destroy()


class MainUI(ctk.CTkFrame):
    """主 UI 框架 - 現代化設計"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # 回調函數
        self.on_record_toggle: Optional[Callable] = None
        self.on_upload_file: Optional[Callable] = None
        self.on_settings_open: Optional[Callable] = None
        self.on_clear_history: Optional[Callable] = None
        self.on_translate_click: Optional[Callable] = None
        self.on_save_subtitle: Optional[Callable] = None
        
        self.subtitles = []
        
        # 初始化懸浮窗 (預設隱藏)
        self.overlay = SubtitleOverlay(self)
        self.overlay.withdraw()
        
        self.setup_ui()
    
    def setup_ui(self):
        """設定現代化介面"""
        self.configure(fg_color="#0b0f1a")
        
        # UI 佈局
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. 側邊欄
        self.sidebar = ctk.CTkFrame(self, width=70, corner_radius=0, fg_color="#070a13")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 側邊欄按鈕
        self.btn_home = ctk.CTkButton(self.sidebar, text="🏠", width=50, height=50,
                                      fg_color="#1e293b", hover_color="#334155",
                                      font=("Arial", 20))
        self.btn_home.pack(pady=10)
        
        self.btn_settings_sidebar = ctk.CTkButton(self.sidebar, text="⚙️", width=50, height=50,
                                                  fg_color="transparent", hover_color="#334155",
                                                  font=("Arial", 20),
                                                  command=self._on_settings)
        self.btn_settings_sidebar.pack(pady=10)
        
        # 2. 主內容
        self.main_view = ctk.CTkFrame(self, fg_color="#0b0f1a", corner_radius=0)
        self.main_view.grid(row=0, column=1, sticky="nsew")
        self.main_view.grid_columnconfigure(0, weight=1)
        self.main_view.grid_rowconfigure(1, weight=1)

        self.setup_header()
        self.setup_history_area()
        self.setup_controls()
    
    def setup_header(self):
        """設定頂部控制列"""
        header = ctk.CTkFrame(self.main_view, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        # 左側：設備選擇
        ctk.CTkLabel(header, text="🎤 音訊輸入裝置:", font=("Arial", 12, "bold"),
                    text_color="#e2e8f0").pack(side="left")
        
        self.device_var = ctk.StringVar(value="選擇音訊裝置")
        self.device_menu = ctk.CTkComboBox(header, values=[],
                                          variable=self.device_var, width=250,
                                          fg_color="#1e293b", border_color="#334155")
        self.device_menu.pack(side="left", padx=10)
        
        refresh_btn = ctk.CTkButton(header, text="🔄", width=40, height=30,
                                   fg_color="#334155", hover_color="#475569")
        refresh_btn.pack(side="left", padx=5)
        
        # 右側：懸浮窗開關
        self.btn_overlay = ctk.CTkButton(
            header, text="🖼️ 懸浮窗", width=120, height=30, 
            fg_color="#3b82f6", hover_color="#2563eb",
            command=self.toggle_overlay
        )
        self.btn_overlay.pack(side="right")
        
        # 狀態顯示
        self.status_label = ctk.CTkLabel(header, text="⏹ 就緒", 
                                        text_color="#94a3b8", font=("Arial", 11))
        self.status_label.pack(side="right", padx=20)
    
    def setup_history_area(self):
        """設定歷史記錄區域（聊天氣泡風格）"""
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_view, fg_color="transparent",
                                                   label_text="📝 即時對話記錄")
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
    
    def setup_controls(self):
        """設定底部控制列"""
        footer = ctk.CTkFrame(self.main_view, fg_color="#070a13", height=120)
        footer.grid(row=2, column=0, sticky="ew")
        
        # 上排按鈕
        top_row = ctk.CTkFrame(footer, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(10, 5))
        
        # 錄音按鈕
        self.record_btn = ctk.CTkButton(
            top_row, text="▶ 開始錄音", height=45, width=150, corner_radius=22,
            fg_color="#ef4444", hover_color="#dc2626",
            font=("Arial", 16, "bold"),
            command=self._on_record_toggle
        )
        self.record_btn.pack(side="left", padx=5)
        
        # 上傳檔案按鈕
        self.upload_btn = ctk.CTkButton(
            top_row, text="📁 上傳檔案", height=45, width=150, corner_radius=22,
            fg_color="#3b82f6", hover_color="#2563eb",
            font=("Arial", 14, "bold"),
            command=self._on_upload_file
        )
        self.upload_btn.pack(side="left", padx=5)
        
        # 翻譯按鈕
        self.translate_btn = ctk.CTkButton(
            top_row, text="🌐 翻譯", height=45, width=120, corner_radius=22,
            fg_color="#10b981", hover_color="#059669",
            font=("Arial", 14, "bold"),
            command=self._on_translate_click,
            state="disabled"
        )
        self.translate_btn.pack(side="left", padx=5)
        
        # 設置按鈕
        self.settings_btn = ctk.CTkButton(
            top_row, text="⚙️ 設置", height=45, width=100, corner_radius=22,
            fg_color="#8b5cf6", hover_color="#7c3aed",
            font=("Arial", 14, "bold"),
            command=self._on_settings
        )
        self.settings_btn.pack(side="left", padx=5)
        
        # 下排按鈕
        bottom_row = ctk.CTkFrame(footer, fg_color="transparent")
        bottom_row.pack(fill="x", padx=20, pady=(0, 10))
        
        # 儲存按鈕
        self.save_btn = ctk.CTkButton(
            bottom_row, text="💾 儲存 SRT", height=35, width=120, corner_radius=18,
            fg_color="#334155", hover_color="#475569",
            state="disabled", command=self._on_save_subtitle
        )
        self.save_btn.pack(side="left", padx=5)
        
        # 清空按鈕
        self.clear_btn = ctk.CTkButton(
            bottom_row, text="🗑️ 清空記錄", height=35, width=120, corner_radius=18,
            fg_color="#64748b", hover_color="#475569",
            command=self._on_clear_history
        )
        self.clear_btn.pack(side="left", padx=5)
    
    def toggle_overlay(self):
        """切換懸浮窗顯示"""
        if self.overlay.winfo_viewable():
            self.overlay.withdraw()
        else:
            self.overlay.deiconify()
    
    def set_device_list(self, devices: List[str]):
        """設置音訊設備列表"""
        self.device_menu.configure(values=devices)
    
    def set_status(self, status: str, color: str = "#94a3b8"):
        """設置狀態標籤"""
        self.status_label.configure(text=status, text_color=color)
    
    def enable_record_button(self, enable: bool = True):
        """啟用/禁用錄音按鈕"""
        self.record_btn.configure(state="normal" if enable else "disabled")
    
    def set_record_button_state(self, recording: bool):
        """設置錄音按鈕狀態"""
        if recording:
            self.record_btn.configure(text="■ 停止錄音", fg_color="#b91c1c")
        else:
            self.record_btn.configure(text="▶ 開始錄音", fg_color="#ef4444")
    
    def add_history_bubble(self, original: str, translated: str, speaker_id: int = 1):
        """添加歷史記錄氣泡"""
        # 確定顯示風格
        if speaker_id == 1:
            bubble_color = "#475569"
            text_color = "#3b82f6"
            speaker_name = "Speaker 1"
            border_color = "#334155"
            align = "w"
        else:
            bubble_color = "#334155"
            text_color = "#10b981"
            speaker_name = "Speaker 2"
            border_color = "#1e293b"
            align = "e"

        # 容器
        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=5)

        # 實際氣泡
        bubble = ctk.CTkFrame(container, fg_color=bubble_color, border_width=1, 
                             border_color=border_color, corner_radius=12)
        bubble.pack(anchor=align, padx=10, pady=5)

        # 標題列
        header = ctk.CTkFrame(bubble, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 0))

        time_str = datetime.now().strftime("%H:%M:%S")
        
        if speaker_id == 1:
            ctk.CTkLabel(header, text=speaker_name, font=("Arial", 11, "bold"), 
                        text_color=text_color).pack(side="left")
            ctk.CTkLabel(header, text=time_str, font=("Courier", 10), 
                        text_color="#64748b").pack(side="left", padx=(10, 0))
        else:
            ctk.CTkLabel(header, text=speaker_name, font=("Arial", 11, "bold"), 
                        text_color=text_color).pack(side="right")
            ctk.CTkLabel(header, text=time_str, font=("Courier", 10), 
                        text_color="#64748b").pack(side="right", padx=(0, 10))

        # 文字內容
        ctk.CTkLabel(bubble, text=original, font=("Arial", 13, "italic"), 
                    text_color="#94a3b8", justify="left").pack(anchor=align, 
                    padx=15, pady=(4, 0))
        ctk.CTkLabel(bubble, text=translated, font=("Microsoft YaHei", 16, "bold"), 
                    text_color="#f8fafc", justify="left").pack(anchor=align, 
                    padx=15, pady=(2, 10))
        
        # 自動滾動到底部
        self.scroll_frame._parent_canvas.yview_moveto(1.0)
    
    def update_overlay(self, original: str, translated: str, speaker_id: int = 1):
        """更新懸浮窗內容"""
        self.overlay.update_text(original, translated, speaker_id)
    
    def enable_translate_button(self, enable: bool = True):
        """啟用/禁用翻譯按鈕"""
        self.translate_btn.configure(state="normal" if enable else "disabled")
    
    def enable_save_button(self, enable: bool = True):
        """啟用/禁用儲存按鈕"""
        self.save_btn.configure(state="normal" if enable else "disabled")
    
    def clear_history(self):
        """清空歷史記錄"""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.subtitles = []
    
    def ask_save_file(self, default_name: str = "output") -> Optional[str]:
        """詢問保存檔案位置"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".srt",
            initialfile=f"{default_name}.srt",
            filetypes=[("SRT 字幕檔", "*.srt"), ("所有檔案", "*.*")]
        )
        return filepath if filepath else None
    
    def ask_open_audio_file(self) -> Optional[str]:
        """詢問打開音訊檔案"""
        filepath = filedialog.askopenfilename(
            title="選擇音訊檔案",
            filetypes=[
                ("音訊檔案", "*.mp3 *.wav *.m4a *.flac *.mp4 *.mkv"),
                ("所有檔案", "*.*")
            ]
        )
        return filepath if filepath else None
    
    def show_error(self, title: str, message: str):
        """顯示錯誤對話框"""
        messagebox.showerror(title, message)
    
    def show_info(self, title: str, message: str):
        """顯示信息對話框"""
        messagebox.showinfo(title, message)
    
    def show_settings_panel(self, on_save: Optional[Callable] = None):
        """顯示設置面板"""
        SettingsPanel(self, on_save=on_save)
    
    # 內部回調方法
    def _on_record_toggle(self):
        if self.on_record_toggle:
            self.on_record_toggle()
    
    def _on_upload_file(self):
        if self.on_upload_file:
            self.on_upload_file()
    
    def _on_settings(self):
        if self.on_settings_open:
            self.on_settings_open()
    
    def _on_clear_history(self):
        if self.on_clear_history:
            self.on_clear_history()
    
    def _on_translate_click(self):
        if self.on_translate_click:
            self.on_translate_click()
    
    def _on_save_subtitle(self):
        if self.on_save_subtitle:
            self.on_save_subtitle()
