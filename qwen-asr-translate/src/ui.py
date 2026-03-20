import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime

class MainUI(ctk.CTkFrame):
    def __init__(self, master, controller=None, **kwargs):
        super().__init__(master, **kwargs)
        
        # 如果冇特別指定 controller，預設 master (app.py) 就係 controller
        self.controller = controller if controller else master
        
        # 設定整體 Grid 佈局 (1 行 2 列：Sidebar + MainContent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # 定義顏色主題 (模仿網頁版嘅深藍色調)
        self.colors = {
            "bg_dark": "#0b0f19",       # 最深底色
            "bg_panel": "#1e293b",      # 面板底色
            "primary": "#3b82f6",       # 藍色 (按鈕/高亮)
            "primary_hover": "#2563eb",
            "primary_muted": "#1e3a8a", # 模擬半透明藍色底 (Tkinter 唔支援 8 位 hex)
            "danger": "#ef4444",        # 紅色 (錄音)
            "danger_hover": "#dc2626",
            "success": "#10b981",       # 綠色
            "text_light": "#f8fafc",
            "text_muted": "#94a3b8"
        }
        
        # 設置主背景色
        self.configure(fg_color=self.colors["bg_dark"])
        
        self._build_sidebar()
        self._build_main_container()
        
        # 初始化視圖
        self.switch_view("realtime")

    # ==========================================
    # 1. 構建左側導覽列 (Sidebar)
    # ==========================================
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#0f172a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1) # 將底部推落去
        
        # Logo 區域
        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="🌊 QwenASR", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.colors["primary"]
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30))
        
        # 導覽按鈕
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

        # 系統狀態標籤 (底部)
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
        
        # 預先建立三個畫面，但預設隱藏
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
        
        ctk.CTkLabel(header, text="音訊輸入:", text_color=self.colors["text_muted"]).pack(side="left", padx=(20, 10), pady=15)
        self.device_combo = ctk.CTkComboBox(header, values=["🎵 系統音源 (Stereo Mix)", "🎤 內建麥克風"], width=250, fg_color="#0f172a", border_color="#334155")
        self.device_combo.pack(side="left", padx=5)
        
        self.lang_info = ctk.CTkLabel(header, text="日文 (JA) ➔ 繁體中文 (ZH-HK)", font=ctk.CTkFont(weight="bold"), text_color=self.colors["text_light"])
        self.lang_info.pack(side="right", padx=20)

        # --- 對話/字幕顯示區 ---
        self.chat_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew")

        # --- 底部控制列 (圓角懸浮感) ---
        bottom_bar = ctk.CTkFrame(frame, height=80, fg_color=self.colors["bg_panel"], corner_radius=20)
        bottom_bar.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        
        # 錄音大按鈕 (圓形)
        self.record_btn = ctk.CTkButton(
            bottom_bar, text="🎤", width=60, height=60, corner_radius=30,
            font=ctk.CTkFont(size=24), fg_color=self.colors["danger"], hover_color=self.colors["danger_hover"],
            command=self._on_record_click
        )
        self.record_btn.pack(side="left", padx=20, pady=10)
        
        # 狀態文字
        self.record_status_label = ctk.CTkLabel(bottom_bar, text="準備就緒 (READY)", font=ctk.CTkFont(family="Courier", size=14), text_color=self.colors["text_muted"])
        self.record_status_label.pack(side="left", padx=10)
        
        # 動作按鈕
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
        
        # 模擬拖曳區
        dropzone = ctk.CTkFrame(frame, height=200, fg_color=self.colors["bg_panel"], border_width=2, border_color="#334155")
        dropzone.pack(fill="x", pady=10)
        dropzone.pack_propagate(False)
        
        ctk.CTkLabel(dropzone, text="☁️\n拖曳音檔或影片到此處\n(支援 MP3, WAV, MP4)", font=ctk.CTkFont(size=16), text_color=self.colors["text_muted"], justify="center").pack(expand=True)
        
        # 設定區
        settings_panel = ctk.CTkFrame(frame, fg_color=self.colors["bg_panel"], corner_radius=15)
        settings_panel.pack(fill="x", pady=20, ipady=10)
        
        ctk.CTkCheckBox(settings_panel, text="產生雙語 SRT 字幕檔", text_color=self.colors["text_light"]).pack(anchor="w", padx=20, pady=15)
        ctk.CTkCheckBox(settings_panel, text="啟用說話者分離 (Speaker Diarization)", text_color=self.colors["text_light"]).pack(anchor="w", padx=20, pady=5)
        
        start_btn = ctk.CTkButton(frame, text="▶ 開始批次轉換", height=45, fg_color=self.colors["primary"])
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
        
        ctk.CTkLabel(panel, text="ASR 語音辨識模型", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        ctk.CTkComboBox(panel, values=["Qwen3-ASR-0.6B (速度快)", "Qwen3-ASR-1.7B (高準確)"], width=400, fg_color="#0f172a").pack(anchor="w", pady=(0, 20))
        
        ctk.CTkLabel(panel, text="最小靜音切割長度 (VAD Duration)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        vad_slider = ctk.CTkSlider(panel, from_=0.5, to=3.0, number_of_steps=25, width=400)
        vad_slider.pack(anchor="w", pady=(0, 20))
        
        save_btn = ctk.CTkButton(frame, text="💾 儲存設定", height=45, fg_color=self.colors["primary"])
        save_btn.pack(anchor="e", pady=20)
        
        return frame

    # ==========================================
    # UI 互動邏輯
    # ==========================================
    def switch_view(self, view_id):
        """切換主畫面"""
        # 隱藏所有視圖
        for view in self.views.values():
            view.grid_forget()
            
        # 重置側邊欄按鈕顏色
        for btn in self.nav_buttons.values():
            btn.configure(fg_color="transparent", text_color=self.colors["text_muted"])
            
        # 顯示選擇嘅視圖
        self.views[view_id].grid(row=0, column=0, sticky="nsew")
        self.nav_buttons[view_id].configure(fg_color=self.colors["primary_muted"], text_color=self.colors["primary"]) # 使用實色深藍模擬半透明

    def _on_record_click(self):
        """處理錄音按鈕點擊"""
        # 檢查 controller 是否有 toggle_recording 方法
        if self.controller and hasattr(self.controller, 'toggle_recording'):
            self.controller.toggle_recording()
        else:
            # 如果無 Controller，用嚟預覽 UI 效果
            self.update_record_state(not hasattr(self, 'is_rec') or not self.is_rec)
            if self.is_rec:
                self.add_chat_bubble("Speaker #1", "The UI layout has been updated beautifully.", "介面排版已經更新得非常漂亮了。", 1)

    def update_record_state(self, is_recording: bool):
        """更新錄音按鈕狀態 (由 Controller 呼叫)"""
        self.is_rec = is_recording
        if is_recording:
            self.record_btn.configure(text="■", fg_color=self.colors["bg_panel"], hover_color="#334155")
            self.record_status_label.configure(text="LISTENING...", text_color=self.colors["success"])
        else:
            self.record_btn.configure(text="🎤", fg_color=self.colors["danger"], hover_color=self.colors["danger_hover"])
            self.record_status_label.configure(text="PAUSED", text_color=self.colors["text_muted"])

    def add_chat_bubble(self, speaker_name: str, original: str, translated: str, speaker_id: int = 1):
        """加入對話氣泡"""
        # 根據 Speaker ID 決定顏色同對齊方向
        if speaker_id == 1:
            align = "w"  # 靠左
            bubble_color = "#1e293b" # 深藍灰
            text_color = self.colors["primary"]
        else:
            align = "e"  # 靠右
            bubble_color = "#064e3b" # 深綠
            text_color = self.colors["success"]

        # 氣泡外層容器
        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", pady=10, padx=10)

        # 氣泡本體
        bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=15)
        bubble.pack(anchor=align, ipadx=10, ipady=10)

        # 標題 (名字 + 時間)
        time_str = datetime.now().strftime("%H:%M:%S")
        header = ctk.CTkFrame(bubble, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(5, 5))
        
        if speaker_id == 1:
            ctk.CTkLabel(header, text=speaker_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_color).pack(side="left")
            ctk.CTkLabel(header, text=time_str, font=ctk.CTkFont(family="Courier", size=10), text_color=self.colors["text_muted"]).pack(side="left", padx=10)
        else:
            ctk.CTkLabel(header, text=speaker_name, font=ctk.CTkFont(size=11, weight="bold"), text_color=text_color).pack(side="right")
            ctk.CTkLabel(header, text=time_str, font=ctk.CTkFont(family="Courier", size=10), text_color=self.colors["text_muted"]).pack(side="right", padx=10)

        # 內文
        ctk.CTkLabel(bubble, text=original, font=ctk.CTkFont(size=13, slant="italic"), text_color=self.colors["text_muted"], wraplength=500, justify="left").pack(anchor=align, padx=10, pady=(0, 2))
        ctk.CTkLabel(bubble, text=translated, font=ctk.CTkFont(size=16, weight="bold"), text_color=self.colors["text_light"], wraplength=500, justify="left").pack(anchor=align, padx=10, pady=(0, 5))

        # 自動捲動到底部
        self.chat_scroll._parent_canvas.yview_moveto(1.0)

# 獨立運行測試 (如果直接執行此檔案)
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    root.title("QwenASR Pro UI Preview")
    root.geometry("1050x700")
    
    app = MainUI(master=root)
    app.pack(fill="both", expand=True)
    
    root.mainloop()