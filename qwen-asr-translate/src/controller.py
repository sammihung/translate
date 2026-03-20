"""
Controller Layer - 業務邏輯調控
負責連接 UI 層和數據層，管理應用程式的狀態和流程
"""

import threading
import queue
from typing import Optional, Callable
from pathlib import Path
import numpy as np

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
        self.on_status_change: Optional[Callable] = None
        self.on_device_refresh: Optional[Callable] = None
        
        # 設置
        self.target_lang = "en"
        self.use_speaker_diarization = True
        self.bilingual_mode = True
        
        # 字幕歷史
        self.subtitles = []
    
    def initialize_engines(self, progress_callback: Optional[Callable] = None) -> bool:
        """初始化 AI 引擎"""
        try:
            return self.ai_ctrl.load_all_models(
                target_lang=self.target_lang,
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
                if queue_size > 3:
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
