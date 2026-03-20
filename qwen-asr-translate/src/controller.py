"""
Controller Layer - 業務邏輯調控
負責連接 UI 層和數據層，管理應用程式的狀態和流程
"""

import threading
import queue
from typing import Optional, Callable
from pathlib import Path
import numpy as np
import torch

from audio_manager import AudioManager
from ai_controller import AIController


class AppController:
    """應用程式控制器 - 處理所有業務邏輯"""
    
    def __init__(self):
        # 核心組件
        self.audio_mgr = AudioManager()
        self.ai_ctrl = AIController()
        
        # 狀態
        self.is_recording = False
        self.record_thread: Optional[threading.Thread] = None
        self.process_thread: Optional[threading.Thread] = None
        
        # 生產者-消費者模式
        self.audio_queue = queue.Queue()
        
        # 回調函數
        self.on_subtitle_update: Optional[Callable] = None
        self.on_translation_complete: Optional[Callable] = None
        self.on_status_change: Optional[Callable] = None
        self.on_device_refresh: Optional[Callable] = None
        
        # 設置
        self.target_lang = "zh"
        self.use_speaker_diarization = False
        self.bilingual_mode = True
        
        # 1. 智能偵測：一開機就睇吓有冇 GPU
        self.has_gpu = torch.cuda.is_available()
        
        # 2. 自動預設：有 GPU 就預設用 Full (fp16)，冇就用 Fast (q4)
        self.use_full_model = self.has_gpu 
        
        # 3. 根據預設值設定目標模型名稱
        self.tgt_model_name = "translategemma:4b-it-fp16" if self.use_full_model else "translategemma:4b-it-q4_K_M"
        
        print(f"🔍 [Auto-Detect] GPU Available: {self.has_gpu}")
        print(f"🚀 [Auto-Set] Default Model: {self.tgt_model_name}")
            
        
        # 字幕歷史
        self.subtitles = []
        # 新增語言變數
        self.src_lang = "auto"
        self.tgt_lang = "zh"
    
    # src/controller.py

    def initialize_engines(self, progress_callback: Optional[Callable] = None) -> bool:
        """初始化 AI 引擎"""
        # 💡 根據偵測結果決定要用邊個 ASR 模型
        # 如果有 GPU 就用 1.7B，冇就用 0.6B (或者你鍾意全線 1.7B 都得)
        asr_model = "Qwen/Qwen3-ASR-1.7B" if self.has_gpu else "Qwen/Qwen3-ASR-0.6B"
        device = "cuda" if self.has_gpu else "cpu"
        
        try:
            return self.ai_ctrl.load_all_models(
                target_lang=self.target_lang,
                asr_model=asr_model, # 傳入模型名
                device=device,       # 傳入設備
                progress_callback=progress_callback
            )
        except Exception as e:
            print(f"[ERROR] 引擎初始化失敗：{e}")
            return False
    
    def get_audio_devices(self) -> list:
        """獲取音訊設備列表"""
        try:
            return self.audio_mgr.get_audio_devices()
        except Exception as e:
            print(f"[ERROR] 獲取設備列表失敗：{e}")
            return []
    
    def is_engines_ready(self) -> bool:
        """檢查引擎是否就緒"""
        return self.ai_ctrl.engines_ready
    
    def set_settings(self, settings: dict):
        """更新設置"""
        if "language" in settings:
            self.target_lang = settings["language"]
        if "diarization" in settings:
            self.use_speaker_diarization = settings["diarization"]
            self.ai_ctrl.use_speaker_diarization = settings["diarization"]
        if "bilingual" in settings:
            self.bilingual_mode = settings["bilingual"]
            
        # 1. 處理 ASR 模型與設備
        target_asr = settings.get("model", "Qwen/Qwen3-ASR-0.6B")
        target_device = settings.get("device", "cpu").lower() # 轉細階配合 torch
        if target_device == "cuda" and not self.has_gpu:
            target_device = "cpu" # 防止冇卡強行開 CUDA
            
        # 2. 如果模型或設備變咗，就需要重新載入
        # 注意：載入 1.7B 較慢，建議用 Thread 行，呢度先示範核心邏輯
        print(f"🔄 正在套用新設定: {target_asr} on {target_device}")
        
        # 更新翻譯模型 (Ollama)
        if "use_full_model" in settings:
            self.use_full_model = settings["use_full_model"]
            self.tgt_model_name = "translategemma:4b-it" if self.use_full_model else "translategemma:4b-it-q4_K_M"
            if self.ai_ctrl.translate_engine:
                self.ai_ctrl.translate_engine.model_name = self.tgt_model_name

        # 重新初始化 ASR (建議透過回調通知 UI 顯示進度)
        self.ai_ctrl.load_all_models(
            asr_model=target_asr,
            device=target_device
        )
                
    def start_recording(self, device_index: Optional[int] = None) -> bool:
        """開始錄音"""
        if self.is_recording:
            return False
        
        if not self.ai_ctrl.engines_ready:
            if self.on_status_change:
                self.on_status_change("⚠️ 引擎未就緒", "#f59e0b")
            return False
        
        try:
            self.is_recording = True
            
            # 清空舊隊列
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            # 啟動處理線程
            self.process_thread = threading.Thread(target=self._processing_worker, daemon=True)
            self.process_thread.start()
            
            # 啟動錄音線程
            self.record_thread = threading.Thread(
                target=self._recording_thread,
                args=(device_index,),
                daemon=True
            )
            self.record_thread.start()
            
            if self.on_status_change:
                self.on_status_change("🔴 錄音中...", "#ef4444")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 啟動錄音失敗：{e}")
            self.is_recording = False
            return False
    
    def stop_recording(self):
        """停止錄音"""
        self.is_recording = False
        
        try:
            self.audio_mgr.stop_recording()
        except Exception as e:
            print(f"[ERROR] 停止錄音失敗：{e}")
        
        if self.on_status_change:
            self.on_status_change("⏳ 正在處理最後的音訊...", "#f59e0b")
        
        def finish_processing():
            """背景等待隊列清空"""
            try:
                self.audio_queue.join()
                print("✓ 隊列已清空，所有音訊處理完成")
                
                if self.on_status_change:
                    self.on_status_change("⏹ 已停止", "#94a3b8")
            except Exception as e:
                print(f"[ERROR] 等待隊列清空時出錯：{e}")
                if self.on_status_change:
                    self.on_status_change("✗ 停止失敗", "#ef4444")
        
        threading.Thread(target=finish_processing, daemon=True).start()
    
    def _recording_thread(self, device_index: Optional[int]):
        """錄音執行緒（生產者）"""
        def on_audio_data(audio_np):
            """錄音回調"""
            self.audio_queue.put(audio_np)
        
        try:
            if device_index is None:
                device_index = self.audio_mgr.parse_device_index(
                    self.audio_mgr.get_audio_devices()[0] if self.audio_mgr.get_audio_devices() else "default"
                )
            
            self.audio_mgr.start_recording(device_index, callback=on_audio_data)
        except Exception as e:
            print(f"[ERROR] 錄音線程出錯：{e}")
            self.is_recording = False
    
    def _processing_worker(self):
        """背景翻譯員（消費者）"""
        while self.is_recording:
            try:
                queue_size = self.audio_queue.qsize()
                if queue_size > 10:
                    print(f"⚠️ 警告：系統處理速度過慢，丟棄舊音訊 (Queue Size: {queue_size})")
                    while not self.audio_queue.empty():
                        try:
                            self.audio_queue.get_nowait()
                            self.audio_queue.task_done()
                        except queue.Empty:
                            break
                    continue
                
                try:
                    audio_data = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                try:
                    # 第一步：只做 ASR 辨識，跳過即時翻譯 (極速返回)
                    src_lang_param = getattr(self, 'src_lang', 'auto')
                    original, _, speaker = self.ai_ctrl.process_audio(audio_data, src_lang=src_lang_param, skip_translation=True)
                    
                    if original and original.strip():
                        speaker_id = 1 if speaker is None else (1 if "SPEAKER_00" in str(speaker) else 2)
                        
                        # 設定佔位符
                        placeholder_text = "⏳ 翻譯中..."
                        
                        # 添加到歷史記錄
                        subtitle_item = {
                            "original": original,
                            "translated": placeholder_text,
                            "speaker_id": speaker_id,
                            "timestamp": np.datetime64('now')
                        }
                        self.subtitles.append(subtitle_item)
                        item_index = len(self.subtitles) - 1
                        
                        # 觸發回調，先將原文畫上 UI，並獲取氣泡 ID
                        bubble_id = None
                        if self.on_subtitle_update:
                            bubble_id = self.on_subtitle_update(original, placeholder_text, speaker_id)
                        
                        # 第二步：如果成功獲取 ID，將原文掟入背景 Thread 慢慢翻譯
                        if bubble_id:
                            def translate_task(text_to_translate, b_id, idx):
                                # 呼叫 Ollama 翻譯
                                real_translated = self.ai_ctrl.translate_text(text_to_translate)
                                # 更新記憶體中嘅歷史記錄
                                if idx < len(self.subtitles):
                                    self.subtitles[idx]["translated"] = real_translated
                                # 第三步：通知 UI 將「翻譯中...」換成真正嘅中文字
                                if self.on_translation_complete:
                                    self.on_translation_complete(b_id, real_translated)
                                    
                            # 啟動獨立線程，唔阻礙主隊列聽下一句說話
                            threading.Thread(target=translate_task, args=(original, bubble_id, item_index), daemon=True).start()
                finally:
                    try:
                        self.audio_queue.task_done()
                    except Exception as done_err:
                        print(f"[DEBUG] task_done 錯誤：{done_err}")
                        
            except Exception as e:
                print(f"[ERROR] 背景處理錯誤：{e}")
    
    def process_audio_file(self, filepath: str) -> bool:
        """處理音訊檔案"""
        if not self.ai_ctrl.engines_ready:
            if self.on_status_change:
                self.on_status_change("⚠️ 引擎未就緒", "#f59e0b")
            return False
        
        try:
            import librosa
            
            if self.on_status_change:
                self.on_status_change(f"📁 正在處理檔案：{Path(filepath).name}", "#f59e0b")
            
            # 載入音訊檔案
            audio_data, sr = librosa.load(filepath, sr=16000)
            
            # 轉換為正確格式
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            # 處理音訊
            original, translated, speaker = self.ai_ctrl.process_audio(audio_data)
            
            if original and original.strip():
                speaker_id = 1 if speaker is None else (1 if "SPEAKER_00" in str(speaker) else 2)
                
                # 添加到歷史記錄
                subtitle_item = {
                    "original": original,
                    "translated": translated,
                    "speaker_id": speaker_id,
                    "timestamp": np.datetime64('now')
                }
                self.subtitles.append(subtitle_item)
                
                # 觸發回調
                if self.on_subtitle_update:
                    self.on_subtitle_update(original, translated, speaker_id)
            
            if self.on_status_change:
                self.on_status_change("✓ 檔案處理完成", "#10b981")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 檔案處理失敗：{e}")
            if self.on_status_change:
                self.on_status_change(f"✗ 處理失敗：{str(e)}", "#ef4444")
            return False
    
    def save_subtitles(self, filepath: str) -> bool:
        """保存字幕為 SRT 檔"""
        try:
            srt_content = self._generate_srt()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            if self.on_status_change:
                self.on_status_change(f"✓ 字幕已保存", "#10b981")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 保存字幕失敗：{e}")
            if self.on_status_change:
                self.on_status_change(f"✗ 保存失敗", "#ef4444")
            return False
    
    def _generate_srt(self) -> str:
        """生成 SRT 字幕內容"""
        srt_lines = []
        
        for idx, subtitle in enumerate(self.subtitles, 1):
            # 時間碼（簡化版本）
            start_time = f"00:00:{(idx-1):02d},000"
            end_time = f"00:00:{idx:02d},000"
            
            srt_lines.append(str(idx))
            srt_lines.append(f"{start_time} --> {end_time}")
            
            if self.bilingual_mode:
                srt_lines.append(f"{subtitle['original']}")
                srt_lines.append(f"{subtitle['translated']}")
            else:
                srt_lines.append(f"{subtitle['translated']}")
            
            srt_lines.append("")
        
        return "\n".join(srt_lines)
    
    def export_json(self, filepath: str) -> bool:
        """匯出為 JSON 檔"""
        try:
            import json
            
            data = {
                "subtitles": self.subtitles,
                "settings": {
                    "target_language": self.target_lang,
                    "use_speaker_diarization": self.use_speaker_diarization,
                    "bilingual_mode": self.bilingual_mode
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 匯出 JSON 失敗：{e}")
            return False
    
    def clear_history(self):
        """清空歷史記錄"""
        self.subtitles = []
    
    def cleanup(self):
        """清理資源"""
        self.stop_recording()
        try:
            self.audio_mgr.cleanup()
        except:
            pass
        try:
            self.ai_ctrl.cleanup()
        except:
            pass
