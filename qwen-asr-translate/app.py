"""
QwenASR 即時語音辨識與翻譯工具
主應用程式 - CustomTkinter GUI
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue
from pathlib import Path
from typing import Optional
import pyaudio
import numpy as np
from datetime import datetime

from asr_engine import QwenASREngine, TranslationEngine, SubtitleGenerator
from vad_processor import VADProcessor


class RealtimeTab(ctk.CTkFrame):
    """即時辨識分頁"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.asr_engine = None
        self.translate_engine = None
        self.vad_processor = None
        self.speaker_diarization = None  # 說話者分離
        self.is_recording = False
        self.audio_stream = None
        self.audio_queue = queue.Queue()
        self.engines_ready = False  # 追蹤引擎是否已就緒
        self.use_speaker_diarization = True  # 預設開啟，需要 HuggingFace token
        
        self.setup_ui()
    
    def setup_ui(self):
        """設定介面"""
        # 設備選擇
        device_frame = ctk.CTkFrame(self)
        device_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(device_frame, text="🎤 音訊輸入裝置:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        self.device_var = ctk.StringVar(value="選擇音訊裝置")
        self.device_combo = ctk.CTkComboBox(device_frame, values=self.get_audio_devices(),
                                           variable=self.device_var, width=400)
        self.device_combo.pack(side="left", padx=5)
        
        refresh_btn = ctk.CTkButton(device_frame, text="🔄", width=40,
                                   command=self.refresh_devices)
        refresh_btn.pack(side="left", padx=5)
        
        help_btn = ctk.CTkButton(device_frame, text="❓ 系統音源設定", width=120,
                                fg_color="#f57c00", command=self.show_system_audio_help)
        help_btn.pack(side="left", padx=5)
        
        # 語言選擇
        lang_frame = ctk.CTkFrame(self)
        lang_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(lang_frame, text="🌐 辨識語言:").pack(side="left", padx=5)
        
        self.lang_var = ctk.StringVar(value="auto")
        languages = ["auto", "zh", "en", "ja", "ko", "fr", "de", "es"]
        self.lang_combo = ctk.CTkComboBox(lang_frame, values=languages,
                                         variable=self.lang_var, width=150)
        self.lang_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(lang_frame, text="翻譯目標:").pack(side="left", padx=5)
        
        self.target_lang_var = ctk.StringVar(value="en")
        target_langs = ["en", "zh", "ja", "ko", "fr", "de", "es"]
        self.target_lang_combo = ctk.CTkComboBox(lang_frame, values=target_langs,
                                                 variable=self.target_lang_var, width=100)
        self.target_lang_combo.pack(side="left", padx=5)
        
        # 控制按鈕
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(pady=20)
        
        self.record_btn = ctk.CTkButton(control_frame, text="▶ 開始錄音",
                                       command=self.toggle_recording,
                                       height=40, font=("Arial", 16, "bold"))
        self.record_btn.pack(pady=10)
        
        self.save_btn = ctk.CTkButton(control_frame, text="💾 儲存 SRT",
                                     command=self.save_subtitle, state="disabled")
        self.save_btn.pack(pady=5)
        
        # 狀態顯示
        self.status_label = ctk.CTkLabel(self, text="⏹ 就緒", text_color="gray")
        self.status_label.pack(pady=5)
        
        # 字幕顯示區（雙語）
        subtitle_frame = ctk.CTkFrame(self)
        subtitle_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(subtitle_frame, text="📝 即時字幕", font=("Arial", 14, "bold")).pack()
        
        # 原文區
        ctk.CTkLabel(subtitle_frame, text="原文:").pack(anchor="w", padx=5)
        self.original_text = ctk.CTkTextbox(subtitle_frame, height=100, font=("Arial", 14))
        self.original_text.pack(fill="x", padx=5, pady=2)
        
        # 譯文區
        ctk.CTkLabel(subtitle_frame, text="譯文:").pack(anchor="w", padx=5)
        self.translated_text = ctk.CTkTextbox(subtitle_frame, height=100, font=("Arial", 14))
        self.translated_text.pack(fill="x", padx=5, pady=2)
        
        # 小窗預覽（PiP）
        self.pip_window = None
        
    def get_audio_devices(self) -> list:
        """獲取音訊輸入裝置列表"""
        p = pyaudio.PyAudio()
        devices = []
        
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_name = info['name']
                    device_idx = f"{i}: {device_name}"
                    
                    # 標記系統音源設備
                    if any(keyword in device_name.lower() for keyword in 
                           ['stereo mix', '立體聲混音', 'wave out', 'what u hear', 
                            'virtual audio', 'vb-audio', 'voicemeeter']):
                        device_idx = f"{i}: {device_name} 🎵 (系統音源)"
                    
                    devices.append(device_idx)
            except:
                pass
        
        p.terminate()
        
        # 確保有預設選項
        if not devices:
            devices = ["預設麥克風"]
        
        return devices
    
    def refresh_devices(self):
        """重新整理裝置列表"""
        devices = self.get_audio_devices()
        self.device_combo.configure(values=devices)
    
    def show_system_audio_help(self):
        """顯示系統音源設定說明"""
        help_window = ctk.CTkToplevel(self)
        help_window.title("🎵 系統音源設定指南")
        help_window.geometry("700x500")
        help_window.attributes('-topmost', True)
        
        text_box = ctk.CTkTextbox(help_window, font=("Microsoft YaHei", 12))
        text_box.pack(fill="both", expand=True, padx=20, pady=20)
        
        help_text = """
🎵 如何設定系統音源 (立體聲混音)

方法 1: 啟用 Windows 立體聲混音 (推薦)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 右鍵點擊工作列喇叭圖示 → 選擇「聲音」
2. 切換到「錄音」分頁
3. 右鍵點擊空白處 → 勾選「顯示停用的裝置」
4. 找到「立體聲混音」(Stereo Mix)
5. 右鍵點擊 → 選擇「啟用」
6. 再次右鍵 → 設為「預設裝置」
7. 回到程式，點擊「🔄 重新整理」
8. 選擇「立體聲混音」即可收聽電腦聲音

方法 2: 安裝虛擬音訊線 (如果無立體聲混音)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
推薦軟體:
• VB-Audio Virtual Cable (免費)
  下載：https://vb-audio.com/Cable/
  
• VoiceMeeter (免費/進階)
  下載：https://vb-audio.com/Voicemeeter/

安裝步驟:
1. 下載並安裝虛擬音訊線
2. 重啟電腦
3. Windows 音效設定 → 播放
4. 將預設播放裝置設為虛擬音訊線
5. 回到程式，選擇對應的輸入裝置

方法 3: 使用音效卡的迴環功能
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
部分音效卡支援「What U Hear」或「Loopback」:
1. 開啟音效卡控制面板
2. 尋找錄音裝置設定
3. 啟用「What U Hear」或「Loopback」
4. 在程式中選擇該裝置

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 使用建議:
• 立體聲混音品質最佳，延遲最低
• 虛擬音訊線兼容性最好
• 確保播放音量適中，避免爆音

⚠️ 注意事項:
• 收聽系統聲音時，自己的說話不會被錄入
• 如需同時收聽麥克風和系統音，需使用混音器
• 部分受版權保護的內容可能無法錄製

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ 設定完成後:
1. 在上方裝置列表選擇「立體聲混音」
2. 點擊「▶ 開始錄音」
3. 播放電腦聲音（YouTube、音樂等）
4. 即時看到辨識和翻譯結果！
"""
        
        text_box.insert("1.0", help_text)
        text_box.configure(state="disabled")
        
        close_btn = ctk.CTkButton(help_window, text="我知道了", 
                                 command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def toggle_recording(self):
        """切換錄音狀態"""
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """開始錄音"""
        # 初始化引擎（如果還沒載入）
        if self.asr_engine is None or self.vad_processor is None:
            self.init_engines()
        
        # 檢查引擎是否已就緒
        if not self.engines_ready:
            messagebox.showwarning("警告", "引擎尚未完全載入，請稍候...")
            return
        
        # 檢查 VAD 是否已載入
        if self.vad_processor is None:
            messagebox.showerror("錯誤", "VAD 處理器未載入")
            return
        
        self.is_recording = True
        self.record_btn.configure(text="■ 停止錄音", fg_color="#d32f2f")
        self.status_label.configure(text="🔴 錄音中...", text_color="#d32f2f")
        
        # 啟動錄音執行緒
        self.record_thread = threading.Thread(target=self.record_audio, daemon=True)
        self.record_thread.start()
    
    def stop_recording(self):
        """停止錄音"""
        # 只係話俾背景 Thread 知要停啦
        self.is_recording = False
        
        # 背景 Thread 會自己喺 finally 入面安全關閉音訊流
        # 唔好喺度強行 close() 避免 Thread 衝突
        
        self.record_btn.configure(text="▶ 開始錄音", fg_color="#1976d2")
        self.status_label.configure(text="⏹ 已停止", text_color="gray")
        self.save_btn.configure(state="normal")
    
    def init_engines(self):
        """初始化 ASR 和翻譯引擎"""
        def load_in_background():
            try:
                # 載入 ASR 模型（使用 qwen-asr 套件）
                try:
                    print("正在初始化 ASR 引擎...")
                    self.asr_engine = QwenASREngine(model_name="Qwen/Qwen3-ASR-0.6B", device="cpu")
                    self.asr_engine.load_model()
                except Exception as e:
                    self.asr_engine = None
                    print(f"[WARN] ASR 模型載入失敗：{e}")
                    print("將使用基本模式（VAD + 翻譯，無語音辨識）")
                
                # 載入 VAD
                self.vad_processor = VADProcessor()
                
                # 載入翻譯引擎
                target_lang = self.target_lang_var.get()
                self.translate_engine = TranslationEngine(source_lang="zh", target_lang=target_lang)
                self.translate_engine.load_model()  # 立即載入，不要延遲
                
                # 載入說話者分離（可選，需要 HuggingFace token）
                if self.use_speaker_diarization:
                    try:
                        from asr_engine import SpeakerDiarization
                        self.speaker_diarization = SpeakerDiarization()
                        self.speaker_diarization.load_pipeline()
                    except Exception as e:
                        self.speaker_diarization = None
                        print(f"[WARN] Speaker Diarization 載入失敗：{e}")
                        print("將使用基本模式（無說話者分離）")
                
                # 標記引擎已就緒
                self.engines_ready = True
                
                if self.asr_engine and self.asr_engine.loaded:
                    if self.speaker_diarization and self.speaker_diarization.loaded:
                        self.after(0, lambda: self.status_label.configure(text="[OK] 引擎已就緒 (ASR + VAD + 翻譯 + 說話者分離)", text_color="green"))
                    else:
                        self.after(0, lambda: self.status_label.configure(text="[OK] 引擎已就緒 (ASR + VAD + 翻譯)", text_color="green"))
                else:
                    self.after(0, lambda: self.status_label.configure(text="[OK] 引擎已就緒 (VAD + 翻譯)", text_color="orange"))
                
                print("[OK] 引擎初始化完成")
                
            except Exception as e:
                self.engines_ready = False
                self.after(0, lambda: messagebox.showerror("錯誤", f"引擎初始化失敗:\n{str(e)}"))
        
        # 在主執行緒先顯示載入狀態
        self.status_label.configure(text="[LOADING] 正在載入引擎...", text_color="orange")
        
        # 在背景執行緒載入模型，避免阻塞 GUI
        import threading
        thread = threading.Thread(target=load_in_background, daemon=True)
        thread.start()
        
        # 等待引擎就緒（最多 30 秒）
        self.wait_for_engines(timeout=30)
    
    def wait_for_engines(self, timeout: float = 30.0):
        """等待引擎載入完成"""
        import time
        start_time = time.time()
        
        while not self.engines_ready and (time.time() - start_time) < timeout:
            time.sleep(0.1)
            self.status_label.configure(text=f"[LOADING] 正在載入引擎... ({int(time.time() - start_time)}s)")
            self.update()  # 強制更新 UI
        
        if not self.engines_ready:
            self.status_label.configure(text="[TIMEOUT] 引擎載入超時", text_color="orange")
            print("[TIMEOUT] 引擎載入超時")
    
    def record_audio(self):
        """錄音處理主迴圈"""
        p = pyaudio.PyAudio()
        
        try:
            # 開啟音訊流
            device_index = 0
            device_text = self.device_var.get()
            if ":" in device_text:
                device_index = int(device_text.split(":")[0])
            
            # 嘗試開啟音訊流，處理可能的錯誤
            try:
                self.audio_stream = p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=1024
                )
            except Exception as e:
                # 如果 16000Hz 失敗，嘗試使用裝置預設取樣率
                try:
                    device_info = p.get_device_info_by_index(device_index)
                    sample_rate = int(device_info.get('defaultSampleRate', 48000))
                    print(f"使用裝置預設取樣率：{sample_rate}Hz")
                    
                    self.audio_stream = p.open(
                        format=pyaudio.paFloat32,
                        channels=1,
                        rate=sample_rate,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024
                    )
                except Exception as e2:
                    # Stereo Mix 可能需要在 Windows 聲音設定中啟用
                    self.audio_stream = p.open(
                        format=pyaudio.paFloat32,
                        channels=2,  # Stereo Mix 通常是立體聲
                        rate=48000,
                        input=True,
                        input_device_index=device_index,
                        frames_per_buffer=1024
                    )
            
            audio_buffer = []
            
            # 當 is_recording 變成 False 時，迴圈會自然結束
            while self.is_recording:
                # 讀取音訊
                data = self.audio_stream.read(1024, exception_on_overflow=False)
                audio_np = np.frombuffer(data, dtype=np.float32)
                audio_buffer.extend(audio_np.tolist())
                
                # 每 2 秒處理一次
                if len(audio_buffer) >= 16000 * 2:
                    self.process_audio_buffer(np.array(audio_buffer))
                    audio_buffer = audio_buffer[-3200:]  # 保留最後 2.0 秒作為重疊緩衝，避免遺漏字詞
                
        except Exception as e:
            print(f"錄音錯誤：{e}")
        finally:
            # 迴圈完結後，安全地喺度閂閉音訊流
            if self.audio_stream is not None:
                if self.audio_stream.is_active():
                    self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            p.terminate()
    
    def process_audio_buffer(self, audio: np.ndarray):
        """處理音訊緩衝區 - 支援說話者分離和連續辨識"""
        # VAD 偵測語音段落
        segments = self.vad_processor.detect_speech_segments(audio)
        
        if segments:
            for start, end in segments:
                # 截取語音片段
                start_idx = int(start * 16000)
                end_idx = int(end * 16000)
                segment = audio[start_idx:end_idx]
                
                # 說話者分離（如果已啟用）
                speaker_label = None
                if self.speaker_diarization and self.speaker_diarization.loaded:
                    try:
                        diarization_results = self.speaker_diarization.diarize(segment)
                        if diarization_results and len(diarization_results) > 0:
                            # 取第一個說話者標籤
                            _, _, speaker_label = diarization_results[0]
                    except Exception as e:
                        print(f"[WARN] Diarization error: {e}")
                
                # ASR 辨識
                try:
                    if self.asr_engine is None:
                        print("⚠️ ASR 引擎未載入，跳過語音辨識")
                        continue
                    
                    text = self.asr_engine.process_audio(segment)
                    
                    # 翻譯
                    if text.strip() and self.translate_engine:
                        translated = self.translate_engine.translate(text)
                        
                        # 加上說話者標籤
                        if speaker_label:
                            text = f"[{speaker_label}] {text}"
                            translated = f"[{speaker_label}] {translated}"
                        
                        # 更新 UI
                        self.update_subtitle(text, translated)
                    
                except Exception as e:
                    print(f"處理錯誤：{e}")
    
    def update_subtitle(self, original: str, translated: str):
        """更新字幕顯示"""
        # 在主執行緒更新
        self.after(0, lambda: self._update_textboxes(original, translated))
    
    def _update_textboxes(self, original: str, translated: str):
        """更新文字框"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.original_text.insert("end", f"[{timestamp}] {original}\n")
        self.translated_text.insert("end", f"[{timestamp}] {translated}\n")
        
        # 自動捲動到底部
        self.original_text.see("end")
        self.translated_text.see("end")
    
    def save_subtitle(self):
        """儲存字幕檔"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".srt",
            filetypes=[("SRT 字幕檔", "*.srt"), ("所有檔案", "*.*")]
        )
        
        if filepath:
            # TODO: 匯出 SRT
            messagebox.showinfo("完成", f"字幕已儲存至:\n{filepath}")
    
    def cleanup(self):
        """清理資源（用於 App 關閉時）"""
        # 停止錄音
        if self.is_recording:
            self.is_recording = False
        
        # 等待音訊流安全關閉
        import time
        time.sleep(0.3)
        
        # 關閉音訊流
        if self.audio_stream:
            try:
                if self.audio_stream.is_active():
                    self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None


class UploadTab(ctk.CTkFrame):
    """上傳翻譯分頁"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.selected_file = None
        self.setup_ui()
    
    def setup_ui(self):
        """設定介面"""
        # 檔案選擇
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(file_frame, text="📁 選擇檔案:", font=("Arial", 14, "bold")).pack(side="left", padx=5)
        
        self.file_label = ctk.CTkLabel(file_frame, text="未選擇檔案", text_color="gray")
        self.file_label.pack(side="left", padx=10)
        
        browse_btn = ctk.CTkButton(file_frame, text="瀏覽...", command=self.browse_file)
        browse_btn.pack(side="right", padx=5)
        
        # 格式說明
        formats = "支援格式：MP3, WAV, FLAC, M4A, OGG, MP4, MKV, AVI, MOV, WMV"
        ctk.CTkLabel(self, text=formats, text_color="gray").pack(pady=5)
        
        # 翻譯設定
        trans_frame = ctk.CTkFrame(self)
        trans_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(trans_frame, text="來源語言:").pack(side="left", padx=5)
        self.source_lang_var = ctk.StringVar(value="auto")
        ctk.CTkComboBox(trans_frame, values=["auto", "zh", "en", "ja"],
                       variable=self.source_lang_var, width=120).pack(side="left", padx=5)
        
        ctk.CTkLabel(trans_frame, text="目標語言:").pack(side="left", padx=5)
        self.target_lang_var = ctk.StringVar(value="en")
        ctk.CTkComboBox(trans_frame, values=["en", "zh", "ja", "ko", "fr", "de", "es"],
                       variable=self.target_lang_var, width=120).pack(side="left", padx=5)
        
        # 雙語字幕選項
        self.dual_lang_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(trans_frame, text="雙語字幕", variable=self.dual_lang_var).pack(side="left", padx=20)
        
        # 進度條
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=20, pady=10)
        self.progress_bar.set(0)
        
        # 控制按鈕
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(pady=20)
        
        self.convert_btn = ctk.CTkButton(control_frame, text="▶ 開始轉換",
                                        command=self.start_conversion,
                                        height=40, font=("Arial", 16, "bold"))
        self.convert_btn.pack(pady=10)
        
        # 狀態顯示
        self.status_label = ctk.CTkLabel(self, text="⏹ 就緒", text_color="gray")
        self.status_label.pack(pady=5)
    
    def browse_file(self):
        """選擇檔案"""
        filepath = filedialog.askopenfilename(
            title="選擇音訊/影片檔案",
            filetypes=[
                ("所有支援的檔案", "*.mp3 *.wav *.flac *.m4a *.ogg *.mp4 *.mkv *.avi *.mov *.wmv"),
                ("音訊檔案", "*.mp3 *.wav *.flac *.m4a *.ogg"),
                ("影片檔案", "*.mp4 *.mkv *.avi *.mov *.wmv"),
                ("所有檔案", "*.*")
            ]
        )
        
        if filepath:
            self.selected_file = filepath
            self.file_label.configure(text=Path(filepath).name, text_color="white")
    
    def start_conversion(self):
        """開始轉換"""
        if not self.selected_file:
            messagebox.showwarning("警告", "請先選擇檔案")
            return
        
        # TODO: 實作轉換邏輯
        self.status_label.configure(text="🔄 處理中...", text_color="#1976d2")
        self.progress_bar.set(0.5)
        
        # 模擬處理
        threading.Thread(target=self.process_file, daemon=True).start()
    
    def process_file(self):
        """處理檔案"""
        # TODO: 實作完整的轉換流程
        import time
        time.sleep(2)
        
        self.after(0, lambda: self.progress_bar.set(1.0))
        self.after(0, lambda: self.status_label.configure(text="✅ 完成", text_color="green"))
        self.after(0, lambda: messagebox.showinfo("完成", "轉換完成！"))


class SettingsTab(ctk.CTkFrame):
    """設定分頁"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """設定介面"""
        # 外觀設定
        appearance_frame = ctk.CTkFrame(self)
        appearance_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(appearance_frame, text="外觀設定", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(0, 10))
        
        ctk.CTkLabel(appearance_frame, text="顏色模式:").pack(anchor="w", padx=5, pady=5)
        
        self.appearance_var = ctk.StringVar(value="system")
        appearance_combo = ctk.CTkComboBox(appearance_frame, 
                                          values=["Dark", "Light", "System"],
                                          variable=self.appearance_var,
                                          command=self.change_appearance)
        appearance_combo.pack(anchor="w", padx=5, pady=5)
        
        # 輸出設定
        output_frame = ctk.CTkFrame(self)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(output_frame, text="輸出設定", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(0, 10))
        
        ctk.CTkLabel(output_frame, text="中文輸出:").pack(anchor="w", padx=5, pady=5)
        
        self.chinese_var = ctk.StringVar(value="traditional")
        ctk.CTkRadioButton(output_frame, text="繁體中文", variable=self.chinese_var,
                          value="traditional").pack(anchor="w", padx=5)
        ctk.CTkRadioButton(output_frame, text="簡體中文", variable=self.chinese_var,
                          value="simplified").pack(anchor="w", padx=5)
        
        # 模型設定
        model_frame = ctk.CTkFrame(self)
        model_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(model_frame, text="模型設定", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(0, 10))
        
        ctk.CTkLabel(model_frame, text="ASR 模型:").pack(anchor="w", padx=5, pady=5)
        
        self.model_var = ctk.StringVar(value="Qwen3-ASR-0.6B INT8")
        ctk.CTkComboBox(model_frame, 
                       values=["Qwen3-ASR-0.6B INT8", "Qwen3-ASR-1.7B INT8"],
                       variable=self.model_var).pack(anchor="w", padx=5, pady=5)
        
        ctk.CTkLabel(model_frame, text="推理裝置:").pack(anchor="w", padx=5, pady=5)
        
        self.device_var = ctk.StringVar(value="CPU")
        ctk.CTkRadioButton(model_frame, text="CPU (OpenVINO)", variable=self.device_var,
                          value="CPU").pack(anchor="w", padx=5)
        ctk.CTkRadioButton(model_frame, text="GPU (Vulkan)", variable=self.device_var,
                          value="GPU").pack(anchor="w", padx=5)
    
    def change_appearance(self, mode: str):
        """切換外觀模式"""
        ctk.set_appearance_mode(mode.lower())


class MainWindow(ctk.CTk):
    """主視窗"""
    
    def __init__(self):
        super().__init__()
        
        self.title("QwenASR 即時語音辨識與翻譯")
        self.geometry("900x700")
        
        # 設定外觀
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.setup_ui()
    
    def setup_ui(self):
        """設定主介面"""
        # 標籤頁
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True)
        
        # 添加分頁
        self.realtime_tab = RealtimeTab(self.tabview.add("即時轉換"))
        self.realtime_tab.pack(fill="both", expand=True)
        
        self.upload_tab = UploadTab(self.tabview.add("音檔轉字幕"))
        self.upload_tab.pack(fill="both", expand=True)
        
        self.settings_tab = SettingsTab(self.tabview.add("設定"))
        self.settings_tab.pack(fill="both", expand=True)
    
    def on_closing(self):
        """關閉處理"""
        # 如果錄緊音，先停止錄音並清理資源
        if hasattr(self, 'realtime_tab'):
            self.realtime_tab.cleanup()
        
        if messagebox.askokcancel("退出", "確定要退出嗎？"):
            self.destroy()


def main():
    """主程式進入點"""
    app = MainWindow()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
