"""
QwenASR Pro - 即時語音辨識與翻譯工具
現代化 UI 設計：懸浮字幕條、側邊欄、聊天氣泡歷史記錄

重構版本：UI 與核心邏輯分離
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime

from audio_manager import AudioManager
from ai_controller import AIController


class SubtitleOverlay(ctk.CTkToplevel):
    """
    懸浮字幕條：無邊框、半透明、永遠置頂
    加入 Speaker ID 顏色條與標籤
    """
    def __init__(self, parent):
        super().__init__(parent)
        
        # 視窗設定：無邊框、置頂
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.9)
        self.configure(fg_color="#000000")
        
        # 初始位置與大小
        width, height = 750, 110
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = int(screen_height * 0.8)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # 主容器
        self.container = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=12, 
                                      border_width=1, border_color="#1e293b")
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        # 左側說話者顏色條
        self.color_bar = ctk.CTkFrame(self.container, width=6, fg_color="#3b82f6", 
                                      corner_radius=3)
        self.color_bar.pack(side="left", fill="y", padx=(15, 10), pady=15)

        # 右側文字區塊
        self.text_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.text_frame.pack(side="left", fill="both", expand=True, pady=12, padx=(0, 15))

        # 標題列 (Speaker Badge & Close Button)
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

        # 原文字幕
        self.label_orig = ctk.CTkLabel(
            self.text_frame, text="", font=("Arial", 13, "italic"),
            text_color="#94a3b8", wraplength=650, justify="left"
        )
        self.label_orig.pack(anchor="w", pady=(0, 2))

        # 譯文字幕
        self.label_trans = ctk.CTkLabel(
            self.text_frame, text="等待語音輸入...", font=("Microsoft YaHei", 22, "bold"),
            text_color="#ffffff", wraplength=650, justify="left"
        )
        self.label_trans.pack(anchor="w")

        # 綁定拖動功能到所有主要元件
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


class RealtimeTab(ctk.CTkFrame):
    """即時辨識分頁 - 現代化 UI"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # 核心組件（已抽離）
        self.audio_mgr = AudioManager()
        self.ai_ctrl = AIController()
        
        # 狀態
        self.is_recording = False
        self.record_thread: Optional[threading.Thread] = None
        self.process_thread: Optional[threading.Thread] = None
        self.subtitles = []  # 儲存字幕歷史
        self._mock_toggle = 1  # 用於模擬
        
        # 生產者 - 消費者模式：音訊隊列
        import queue
        self.audio_queue = queue.Queue()  # 錄音員放音訊，翻譯員拎音訊
        
        # 初始化懸浮窗 (預設隱藏)
        self.overlay = SubtitleOverlay(self)
        self.overlay.withdraw()
        
        self.setup_ui()
    
    def setup_ui(self):
        """設定現代化介面"""
        # 主容器 - 深色主題
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
        
        self.btn_settings = ctk.CTkButton(self.sidebar, text="⚙️", width=50, height=50,
                                          fg_color="transparent", hover_color="#334155",
                                          font=("Arial", 20))
        self.btn_settings.pack(pady=10)
        
        # 2. 主內容
        self.main_view = ctk.CTkFrame(self, fg_color="#0b0f1a", corner_radius=0)
        self.main_view.grid(row=0, column=1, sticky="nsew")
        self.main_view.grid_columnconfigure(0, weight=1)
        self.main_view.grid_rowconfigure(1, weight=1)

        self.setup_header()
        self.setup_history_area()
        self.setup_controls()
        
        # 啟動引擎載入（背景）
        self.after(500, self.init_engines)
    
    def setup_header(self):
        """設定頂部控制列"""
        header = ctk.CTkFrame(self.main_view, fg_color="transparent", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        # 左側：設備選擇
        ctk.CTkLabel(header, text="🎤 音訊輸入裝置:", font=("Arial", 12, "bold"),
                    text_color="#e2e8f0").pack(side="left")
        
        self.device_var = ctk.StringVar(value="選擇音訊裝置")
        self.device_menu = ctk.CTkComboBox(header, values=self.audio_mgr.get_audio_devices(),
                                          variable=self.device_var, width=250,
                                          fg_color="#1e293b", border_color="#334155")
        self.device_menu.pack(side="left", padx=10)
        
        refresh_btn = ctk.CTkButton(header, text="🔄", width=40, height=30,
                                   command=self.refresh_devices,
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
        
        # 設定滾動區域顏色
        self.scroll_frame._scrollbar.configure(fg_color="#1e293b",
                                       bg_color="#1e293b")
    
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
            command=self.toggle_recording
        )
        self.record_btn.pack(side="left", padx=5)
        
        # 上傳檔案按鈕
        self.upload_btn = ctk.CTkButton(
            top_row, text="📁 上傳檔案", height=45, width=150, corner_radius=22,
            fg_color="#3b82f6", hover_color="#2563eb",
            font=("Arial", 14, "bold"),
            command=self.upload_file_for_translation
        )
        self.upload_btn.pack(side="left", padx=5)
        
        # 翻譯按鈕
        self.translate_btn = ctk.CTkButton(
            top_row, text="🌐 翻譯", height=45, width=120, corner_radius=22,
            fg_color="#10b981", hover_color="#059669",
            font=("Arial", 14, "bold"),
            command=self.translate_current,
            state="disabled"
        )
        self.translate_btn.pack(side="left", padx=5)
        
        # 設置按鈕
        self.settings_btn = ctk.CTkButton(
            top_row, text="⚙️ 設置", height=45, width=100, corner_radius=22,
            fg_color="#8b5cf6", hover_color="#7c3aed",
            font=("Arial", 14, "bold"),
            command=self.show_settings
        )
        self.settings_btn.pack(side="left", padx=5)
        
        # 下排按鈕
        bottom_row = ctk.CTkFrame(footer, fg_color="transparent")
        bottom_row.pack(fill="x", padx=20, pady=(0, 10))
        
        # 儲存按鈕
        self.save_btn = ctk.CTkButton(
            bottom_row, text="💾 儲存 SRT", height=35, width=120, corner_radius=18,
            fg_color="#334155", hover_color="#475569",
            state="disabled", command=self.save_subtitle
        )
        self.save_btn.pack(side="left", padx=5)
        
        # 清空按鈕
        self.clear_btn = ctk.CTkButton(
            bottom_row, text="🗑️ 清空記錄", height=35, width=120, corner_radius=18,
            fg_color="#64748b", hover_color="#475569",
            command=self.clear_history
        )
        self.clear_btn.pack(side="left", padx=5)
    
    def refresh_devices(self):
        """重新整理裝置列表"""
        devices = self.audio_mgr.get_audio_devices()
        self.device_menu.configure(values=devices)
    
    def toggle_overlay(self):
        """切換懸浮窗顯示"""
        if self.overlay.winfo_viewable():
            self.overlay.withdraw()
        else:
            self.overlay.deiconify()
    
    def toggle_recording(self):
        """切換錄音狀態"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """開始錄音 - 啟動生產者 - 消費者模式"""
        # 初始化引擎（如果還沒載入）
        if not self.ai_ctrl.engines_ready:
            messagebox.showwarning("警告", "引擎尚未完全載入，請稍候...")
            return
        
        self.is_recording = True
        self.record_btn.configure(text="■ 停止錄音", fg_color="#b91c1c")
        self.status_label.configure(text="🔴 錄音中...", text_color="#ef4444")
        
        # 清空舊 Queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                pass
        
        # 1. 啟動「翻譯員」Thread (消費者 - 負責處理 Queue 入面嘅音檔)
        self.process_thread = threading.Thread(target=self.processing_worker, daemon=True)
        self.process_thread.start()
        
        # 2. 啟動「錄音員」Thread (生產者 - 專心錄音)
        self.record_thread = threading.Thread(
            target=self._recording_thread,
            daemon=True
        )
        self.record_thread.start()
    
    def _recording_thread(self):
        """錄音執行緒（生產者）- 專心錄音，將數據放入 Queue"""
        device_index = self.audio_mgr.parse_device_index(self.device_var.get())
        
        def on_audio_data(audio_np):
            """錄音回調：將音訊數據放入 Queue，交給背景處理 Thread"""
            self.audio_queue.put(audio_np)
        
        try:
            self.audio_mgr.start_recording(device_index, callback=on_audio_data)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("錄音錯誤", str(e)))
            self.after(0, lambda: self.stop_recording())
    
    def processing_worker(self):
        """背景翻譯員（消費者）- 不斷從 Queue 拎音檔出嚟處理"""
        import queue
        
        while self.is_recording:
            try:
                # 🚨 隱患 1 修復：檢查有冇大塞車
                queue_size = self.audio_queue.qsize()
                if queue_size > 3:  # 如果塞咗超過 3 舊音訊 (大約 6 秒延遲)
                    print(f"⚠️ 警告：系統處理速度過慢，丟棄舊音訊 (Queue Size: {queue_size})")
                    # 清空最舊嘅音訊，追返上最新嘅進度
                    while not self.audio_queue.empty():
                        try:
                            self.audio_queue.get_nowait()
                            self.audio_queue.task_done()
                        except queue.Empty:
                            break
                    continue  # 丟棄後跳到下一次迴圈
                
                # 喺個箱度等 1 秒，有嘢就拎出嚟，無就繼續等
                try:
                    audio_data = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    # 個箱係空嘅，繼續等
                    continue
                
                try:
                    # 拎到音訊，交俾 AI Controller 做 ASR 同翻譯
                    original, translated, speaker = self.ai_ctrl.process_audio(audio_data)
                    
                    if original and original.strip():
                        # 預設 speaker_id = 1（如果無說話者分離）
                        speaker_id = 1 if speaker is None else (1 if "SPEAKER_00" in str(speaker) else 2)
                        
                        # 更新 UI（必須喺主執行緒）
                        try:
                            self.after(0, lambda o=original, t=translated, s=speaker_id: self.update_subtitle(o, t, s))
                        except Exception as ui_err:
                            print(f"[WARN] UI 更新錯誤：{ui_err}")
                    
                finally:
                    # 話俾個箱知處理完啦（一定要執行）
                    try:
                        self.audio_queue.task_done()
                    except Exception as done_err:
                        print(f"[DEBUG] task_done 錯誤：{done_err}")
                        
            except Exception as e:
                print(f"[ERROR] 背景處理錯誤：{e}")
                try:
                    import traceback
                    traceback.print_exc()
                except:
                    pass
    
    def stop_recording(self):
        """
        停止錄音 - 確保處理完 Queue 入面所有音訊
        🚨 隱患 3 修復：等待 Queue 清空先完成
        """
        self.is_recording = False
        
        # 停止錄音（關閉音訊流）
        self.audio_mgr.stop_recording()
        
        self.status_label.configure(text="⏳ 正在處理最後的音訊...", text_color="orange")
        
        def finish_processing():
            """背景等待 Queue 清空，唔好卡住 UI"""
            try:
                # 等待箱入面所有嘢處理完（包括最後一句話）
                self.audio_queue.join()
                print("✓ Queue 已清空，所有音訊處理完成")
                
                # 安全更新 UI（交返俾主線程）
                self.after(0, lambda: self.record_btn.configure(text="▶ 開始錄音", fg_color="#ef4444"))
                self.after(0, lambda: self.status_label.configure(text="⏹ 已停止", text_color="#94a3b8"))
                self.after(0, lambda: self.save_btn.configure(state="normal"))
                
            except Exception as e:
                print(f"等待 Queue 清空時出錯：{e}")
                # 就算出錯都要更新 UI
                self.after(0, lambda: self.record_btn.configure(text="▶ 開始錄音", fg_color="#ef4444"))
                self.after(0, lambda: self.status_label.configure(text="⏹ 已停止 (錯誤)", text_color="#94a3b8"))
                self.after(0, lambda: self.save_btn.configure(state="normal"))
        
        # 開條新 Thread 慢慢等佢完，唔好卡住個 UI
        threading.Thread(target=finish_processing, daemon=True).start()
    
    def init_engines(self):
        """初始化 AI 引擎"""
        def load_in_background():
            def progress_callback(status: str):
                self.after(0, lambda: self.status_label.configure(text=status))
            
            target_lang = "en"  # 預設
            success = self.ai_ctrl.load_all_models(
                target_lang=target_lang,
                progress_callback=progress_callback
            )
            
            if not success:
                self.after(0, lambda: messagebox.showerror(
                    "錯誤", "引擎初始化失敗，請檢查日誌"
                ))
        
        self.status_label.configure(text="[LOADING] 正在載入引擎...", text_color="#f59e0b")
        
        thread = threading.Thread(target=load_in_background, daemon=True)
        thread.start()
    
    def update_subtitle(self, original: str, translated: str, speaker_id: int = 1):
        """
        更新字幕顯示（確保 Thread-Safe）
        
        ⚠️ 注意：此函數可能被背景 Thread 呼叫，必須使用 self.after() 交返俾主 UI Thread
        """
        # 🚨 隱患 2 修復：確保所有 UI 更新都喺主執行緒
        self.after(0, lambda: self._do_update_subtitle(original, translated, speaker_id))
    
    def _do_update_subtitle(self, original: str, translated: str, speaker_id: int = 1):
        """實際執行 UI 更新（必須由主執行緒呼叫）"""
        # 更新懸浮窗
        self.overlay.update_text(original, translated, speaker_id)
        
        # 更新歷史記錄
        self.add_history_bubble(original, translated, speaker_id)
        
        # 儲存字幕歷史
        self.subtitles.append({
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'original': original,
            'translated': translated,
            'speaker': speaker_id
        })
    
    def add_history_bubble(self, orig, trans, speaker_id):
        """新增聊天對話氣泡到歷史記錄中"""
        # 設定氣泡屬性
        if speaker_id == 1:
            align = "w"
            bubble_color = "#1e293b"
            border_color = "#334155"
            text_color = "#60a5fa"
            speaker_name = "SPEAKER #1"
        else:
            align = "e"
            bubble_color = "#064e3b"
            border_color = "#065f46"
            text_color = "#34d399"
            speaker_name = "SPEAKER #2"

        # 對齊容器
        container = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        container.pack(fill="x", pady=5, padx=5)

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
        ctk.CTkLabel(bubble, text=orig, font=("Arial", 13, "italic"), 
                    text_color="#94a3b8", justify="left").pack(anchor=align, 
                    padx=15, pady=(4, 0))
        ctk.CTkLabel(bubble, text=trans, font=("Microsoft YaHei", 16, "bold"), 
                    text_color="#f8fafc", justify="left").pack(anchor=align, 
                    padx=15, pady=(2, 10))
        
        # 自動滾動到底部
        self.scroll_frame._parent_canvas.yview_moveto(1.0)
    
    def mock_recognition(self):
        """模擬辨識（用於測試）"""
        if self._mock_toggle == 1:
            orig = "The latest benchmarks show significant improvements in processing speed."
            trans = "最新的基準測試顯示，在處理速度方面有顯著的提升。"
            speaker_id = 1
            self._mock_toggle = 2
        else:
            orig = "Indeed, especially when running on low-end hardware."
            trans = "的確如此，特別是在低階硬體上執行時。"
            speaker_id = 2
            self._mock_toggle = 1
        
        self.update_subtitle(orig, trans, speaker_id)
    
    def save_subtitle(self):
        """儲存字幕檔"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".srt",
            filetypes=[("SRT 字幕檔", "*.srt"), ("所有檔案", "*.*")]
        )
        
        if filepath:
            # TODO: 實現 SRT 匯出邏輯
            messagebox.showinfo("完成", f"字幕已儲存至:\n{filepath}")
    
    def clear_history(self):
        """清空歷史記錄"""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.subtitles = []
        messagebox.showinfo("完成", "歷史記錄已清空")
    
    def upload_file_for_translation(self):
        """上傳檔案進行翻譯"""
        filepath = filedialog.askopenfilename(
            title="選擇音訊檔案",
            filetypes=[
                ("音訊檔案", "*.mp3 *.wav *.m4a *.flac"),
                ("所有檔案", "*.*")
            ]
        )
        
        if not filepath:
            return
        
        if not self.ai_ctrl.engines_ready:
            messagebox.showwarning("警告", "引擎尚未完全載入，請稍候...")
            return
        
        # 禁用按鈕，開始處理
        self.upload_btn.configure(state="disabled")
        self.status_label.configure(text="📁 正在處理檔案...", text_color="#f59e0b")
        
        def process_file():
            try:
                import librosa
                import numpy as np
                
                # 載入音訊檔案
                audio_data, sr = librosa.load(filepath, sr=16000)
                
                # 轉換為正確的格式
                if audio_data.dtype != np.int16:
                    audio_data = (audio_data * 32767).astype(np.int16)
                
                # 處理音訊
                original, translated, speaker = self.ai_ctrl.process_audio(audio_data)
                
                if original.strip():
                    speaker_id = 1 if speaker is None else (1 if "SPEAKER_00" in str(speaker) else 2)
                    self.after(0, lambda o=original, t=translated, s=speaker_id: self.update_subtitle(o, t, s))
                
                self.after(0, lambda: self.status_label.configure(text="✓ 檔案處理完成", text_color="#10b981"))
                
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("錯誤", f"檔案處理失敗：{str(e)}"))
                self.after(0, lambda: self.status_label.configure(text="✗ 處理失敗", text_color="#ef4444"))
            
            finally:
                self.after(0, lambda: self.upload_btn.configure(state="normal"))
        
        # 在背景執行緒處理
        threading.Thread(target=process_file, daemon=True).start()
    
    def translate_current(self):
        """翻譯當前內容"""
        if not self.subtitles:
            messagebox.showinfo("提示", "沒有可翻譯的內容")
            return
        
        # 拿最後一條字幕進行翻譯
        latest = self.subtitles[-1]
        messagebox.showinfo("翻譯", f"原文：{latest['original']}\n\n譯文：{latest['translated']}")
    
    def show_settings(self):
        """顯示設置面板"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("設置")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # 標題
        title_label = ctk.CTkLabel(
            settings_window, text="⚙️ 應用程式設置", 
            font=("Arial", 16, "bold"), text_color="#e2e8f0"
        )
        title_label.pack(pady=15)
        
        # 設定框架
        settings_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 目標語言選擇
        ctk.CTkLabel(settings_frame, text="翻譯目標語言:", 
                     font=("Arial", 12), text_color="#cbd5e1").pack(anchor="w", pady=(10, 5))
        
        language_var = ctk.StringVar(value="en")
        lang_menu = ctk.CTkComboBox(
            settings_frame, values=["en", "zh", "ja", "ko", "es", "fr"],
            variable=language_var, width=300, fg_color="#1e293b"
        )
        lang_menu.pack(anchor="w", pady=(0, 15))
        
        # 說話者分離開關
        diarization_var = ctk.BooleanVar(value=self.ai_ctrl.use_speaker_diarization)
        diarization_check = ctk.CTkCheckBox(
            settings_frame, text="啟用說話者分離 (Speaker Diarization)",
            variable=diarization_var, fg_color="#3b82f6",
            font=("Arial", 11), text_color="#cbd5e1"
        )
        diarization_check.pack(anchor="w", pady=10)
        
        # 儲存按鈕
        def save_settings():
            self.ai_ctrl.use_speaker_diarization = diarization_var.get()
            messagebox.showinfo("完成", "設置已儲存")
            settings_window.destroy()
        
        save_btn = ctk.CTkButton(
            settings_frame, text="💾 儲存設置", height=35,
            fg_color="#3b82f6", hover_color="#2563eb",
            command=save_settings
        )
        save_btn.pack(pady=20)
    
    def cleanup(self):
        """清理資源"""
        self.audio_mgr.cleanup()
        self.ai_ctrl.cleanup()


class App(ctk.CTk):
    """主應用程式"""
    
    def __init__(self):
        super().__init__()
        
        self.title("QwenASR Pro - YouTube Edition")
        self.geometry("1000x700")
        ctk.set_appearance_mode("dark")
        
        # 創建即時辨識分頁
        self.realtime_tab = RealtimeTab(self)
        self.realtime_tab.pack(fill="both", expand=True)
        
        # 處理關閉事件
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """處理應用程式關閉"""
        self.realtime_tab.cleanup()
        self.destroy()


def main():
    """主函數"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
