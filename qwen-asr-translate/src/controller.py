"""
Controller Layer - 業務邏輯調控
負責連接 UI 層和數據層，管理應用程式的狀態和流程
"""

import threading
import queue
import time
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path
import numpy as np
import torch

from audio_manager import AudioManager
from ai_controller import AIController
from logging_config import get_logger

logger = get_logger(__name__)


class RecordingState:
    """使用 Event 管理錄音狀態，確保跨執行緒同步安全"""
    
    def __init__(self) -> None:
        self._stop_event: threading.Event = threading.Event()
        self._is_recording: bool = False
    
    def start(self) -> None:
        """開始錄音"""
        self._stop_event.clear()
        self._is_recording = True
    
    def stop(self) -> None:
        """停止錄音"""
        self._is_recording = False
        self._stop_event.set()
    
    def is_recording(self) -> bool:
        """檢查是否正在錄音"""
        return self._is_recording
    
    def wait_for_stop(self, timeout: Optional[float] = None) -> bool:
        """等待錄音停止，可設定超時"""
        return self._stop_event.wait(timeout=timeout)
    
    def is_set(self) -> bool:
        """檢查停止事件是否已設定"""
        return self._stop_event.is_set()


class AppController:
    """應用程式控制器 - 處理所有業務邏輯"""
    
    def __init__(self) -> None:
        # 核心組件
        self.audio_mgr: AudioManager = AudioManager()
        self.ai_ctrl: AIController = AIController()
        
        # 狀態 - 使用 Event 確保執行緒安全
        self.recording_state: RecordingState = RecordingState()
        self.is_recording: bool = False  # 保留向下相容
        
        self.record_thread: Optional[threading.Thread] = None
        self.process_thread: Optional[threading.Thread] = None
        
        # 生產者 - 消費者模式 - 設定 maxsize 防止 OOM
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=10)
        
        # 回調函數
        self.on_subtitle_update: Optional[Callable[[str, str, int], str]] = None
        self.on_translation_complete: Optional[Callable[[str, str], None]] = None
        self.on_status_change: Optional[Callable[[str, str], None]] = None
        self.on_device_refresh: Optional[Callable[[], None]] = None
        
        # 設置
        self.target_lang: str = "zh"
        self.use_speaker_diarization: bool = False
        self.bilingual_mode: bool = True
        
        # 智能偵測：一開機就睇吓有冇 GPU
        self.has_gpu: bool = torch.cuda.is_available()
        
        # 自動預設：有 GPU 就預設用 Full (fp16)，冇就用 Fast (q4)
        self.use_full_model: bool = self.has_gpu
        
        # 根據預設值設定目標模型名稱
        self.tgt_model_name: str = "translategemma:4b-it-fp16" if self.use_full_model else "translategemma:4b-it-q4_K_M"
        
        logger.info(f"GPU Available: {self.has_gpu}")
        logger.info(f"Default Model: {self.tgt_model_name}")
            
        # 字幕歷史
        self.subtitles: List[Dict[str, Any]] = []
        # 語言變數
        self.src_lang: str = "auto"
        self.tgt_lang: str = "zh"
    
    def initialize_engines(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """初始化 AI 引擎"""
        try:
            # 根據偵測結果決定要用邊個 ASR 模型
            asr_model: str = "Qwen/Qwen3-ASR-1.7B" if self.has_gpu else "Qwen/Qwen3-ASR-0.6B"
            device: str = "cuda" if self.has_gpu else "cpu"
            
            logger.info(f"正在初始化引擎：{asr_model} on {device}")
            
            success: bool = self.ai_ctrl.load_all_models(
                target_lang=self.target_lang,
                asr_model=asr_model,
                device=device,
                progress_callback=progress_callback
            )
            
            if success:
                logger.info("引擎初始化成功")
            else:
                logger.error("引擎初始化失敗")
            
            return success
            
        except Exception as e:
            logger.error(f"引擎初始化失敗：{e}", exc_info=True)
            return False
    
    def get_audio_devices(self) -> List[str]:
        """獲取音訊設備列表"""
        try:
            devices: List[str] = self.audio_mgr.get_audio_devices()
            logger.debug(f"獲取到 {len(devices)} 個音訊設備")
            return devices
        except Exception as e:
            logger.error(f"獲取設備列表失敗：{e}", exc_info=True)
            return []
    
    def is_engines_ready(self) -> bool:
        """檢查引擎是否就緒"""
        return self.ai_ctrl.engines_ready
    
    def set_settings(self, settings: Dict[str, Any]) -> None:
        """更新設置"""
        try:
            if "language" in settings:
                self.target_lang = settings["language"]
                logger.info(f"目標語言已更新：{self.target_lang}")
                
            if "diarization" in settings:
                self.use_speaker_diarization = settings["diarization"]
                self.ai_ctrl.use_speaker_diarization = settings["diarization"]
                logger.info(f"說話者分離：{'啟用' if self.use_speaker_diarization else '停用'}")
                
            if "bilingual" in settings:
                self.bilingual_mode = settings["bilingual"]
                logger.info(f"雙語模式：{'啟用' if self.bilingual_mode else '停用'}")
            
            # 處理 ASR 模型與設備
            target_asr: str = settings.get("model", "Qwen/Qwen3-ASR-0.6B")
            target_device: str = settings.get("device", "cpu").lower()
            
            if target_device == "cuda" and not self.has_gpu:
                target_device = "cpu"
                logger.warning("未檢測到 GPU，已自動切換回 CPU 模式")
            
            # 更新翻譯模型 (Ollama)
            if "use_full_model" in settings:
                self.use_full_model = settings["use_full_model"]
                self.tgt_model_name = "translategemma:4b-it" if self.use_full_model else "translategemma:4b-it-q4_K_M"
                
                if self.ai_ctrl.translate_engine:
                    self.ai_ctrl.translate_engine.model_name = self.tgt_model_name
                    logger.info(f"翻譯模型已更新：{self.tgt_model_name}")

            # 重新初始化 ASR
            logger.info(f"正在套用新設定：{target_asr} on {target_device}")
            
            # 注意：載入模型較慢，建議在背景執行緒進行
            def reload_asr() -> None:
                try:
                    self.ai_ctrl.load_all_models(
                        asr_model=target_asr,
                        device=target_device
                    )
                    logger.info("ASR 模型重新載入完成")
                except Exception as e:
                    logger.error(f"ASR 重新載入失敗：{e}", exc_info=True)
            
            threading.Thread(target=reload_asr, daemon=True).start()
            
        except Exception as e:
            logger.error(f"更新設置失敗：{e}", exc_info=True)
            raise
    
    def start_recording(self, device_index: Optional[int] = None) -> bool:
        """開始錄音"""
        try:
            if self.recording_state.is_recording():
                logger.warning("已經在錄音中")
                return False
            
            if not self.ai_ctrl.engines_ready:
                logger.warning("引擎尚未就緒")
                if self.on_status_change:
                    self.on_status_change("⚠️ 引擎未就緒", "#f59e0b")
                return False
            
            # 使用 Event 管理狀態
            self.recording_state.start()
            self.is_recording = True  # 保持向下相容
            
            # 清空舊隊列
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            # 啟動處理線程
            self.process_thread = threading.Thread(
                target=self._processing_worker,
                daemon=True,
                name="AudioProcessor"
            )
            self.process_thread.start()
            
            # 啟動錄音線程
            self.record_thread = threading.Thread(
                target=self._recording_thread,
                args=(device_index,),
                daemon=True,
                name="AudioRecorder"
            )
            self.record_thread.start()
            
            logger.info(f"開始錄音 (設備：{device_index})")
            
            if self.on_status_change:
                self.on_status_change("🔴 錄音中...", "#ef4444")
            
            return True
            
        except Exception as e:
            logger.error(f"啟動錄音失敗：{e}", exc_info=True)
            self.recording_state.stop()
            self.is_recording = False
            return False
    
    def stop_recording(self) -> None:
        """停止錄音 - 使用 Event 優雅停止"""
        try:
            # 使用 Event 設定停止信號
            self.recording_state.stop()
            self.is_recording = False  # 保持向下相容
            
            try:
                self.audio_mgr.stop_recording()
            except Exception as e:
                logger.error(f"停止錄音失敗：{e}", exc_info=True)
            
            if self.on_status_change:
                self.on_status_change("⏳ 正在處理最後的音訊...", "#f59e0b")
            
            def finish_processing() -> None:
                """背景等待隊列清空"""
                try:
                    # 等待所有音訊處理完成，最多等 5 秒
                    self.audio_queue.join()
                    logger.info("隊列已清空，所有音訊處理完成")
                    
                    if self.on_status_change:
                        self.on_status_change("⏹ 已停止", "#94a3b8")
                except Exception as e:
                    logger.error(f"等待隊列清空時出錯：{e}", exc_info=True)
                    if self.on_status_change:
                        self.on_status_change("✗ 停止失敗", "#ef4444")
            
            threading.Thread(target=finish_processing, daemon=True).start()
            
        except Exception as e:
            logger.error(f"停止錄音失敗：{e}", exc_info=True)
    
    def _recording_thread(self, device_index: Optional[int]) -> None:
        """錄音執行緒（生產者）- 使用 Event 管理停止"""
        try:
            def on_audio_data(audio_np: np.ndarray) -> None:
                """錄音回調 - 隊列滿時自動阻塞"""
                try:
                    # 如果隊列滿了，這裡會阻塞直到有空間
                    # 這樣可以防止 OOM，同時避免丟棄音訊
                    self.audio_queue.put(audio_np, block=True, timeout=2.0)
                except queue.Full:
                    logger.warning("音訊隊列已滿，丟棄舊音訊")
            
            if device_index is None:
                devices: List[str] = self.audio_mgr.get_audio_devices()
                device_index = self.audio_mgr.parse_device_index(
                    devices[0] if devices else "default"
                )
            
            self.audio_mgr.start_recording(device_index, callback=on_audio_data)
            
        except Exception as e:
            logger.error(f"錄音線程出錯：{e}", exc_info=True)
            self.recording_state.stop()
            self.is_recording = False
    
    def _processing_worker(self) -> None:
        """背景翻譯員（消費者）- 使用 Event 管理循環"""
        try:
            # 使用 Event 檢查停止信號，更加即時和安全
            while not self.recording_state.is_set():
                try:
                    # 從隊列獲取音訊數據 (使用 timeout 避免無限阻塞)
                    try:
                        audio_data: np.ndarray = self.audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    
                    try:
                        # 第一步：只做 ASR 辨識，跳過即時翻譯 (極速返回)
                        src_lang_param: str = getattr(self, 'src_lang', 'auto')
                        original: str
                        _: str
                        speaker: Optional[str]
                        original, _, speaker = self.ai_ctrl.process_audio(
                            audio_data,
                            src_lang=src_lang_param,
                            skip_translation=True
                        )
                        
                        if original and original.strip():
                            speaker_id: int = 1 if speaker is None else (1 if "SPEAKER_00" in str(speaker) else 2)
                            
                            # 設定佔位符
                            placeholder_text: str = "⏳ 翻譯中..."
                            
                            # 添加到歷史記錄
                            subtitle_item: Dict[str, Any] = {
                                "original": original,
                                "translated": placeholder_text,
                                "speaker_id": speaker_id,
                                "timestamp": np.datetime64('now')
                            }
                            self.subtitles.append(subtitle_item)
                            item_index: int = len(self.subtitles) - 1
                            
                            # 觸發回調，先將原文畫上 UI，並獲取氣泡 ID
                            bubble_id: Optional[str] = None
                            if self.on_subtitle_update:
                                bubble_id = self.on_subtitle_update(original, placeholder_text, speaker_id)
                            
                            # 第二步：如果成功獲取 ID，將原文掟入背景 Thread 慢慢翻譯
                            if bubble_id:
                                def translate_task(
                                    text_to_translate: str,
                                    b_id: str,
                                    idx: int
                                ) -> None:
                                    """背景翻譯任務"""
                                    try:
                                        # 呼叫 Ollama 翻譯
                                        real_translated: str = self.ai_ctrl.translate_text(text_to_translate)
                                        
                                        # 更新記憶體中嘅歷史記錄
                                        if idx < len(self.subtitles):
                                            self.subtitles[idx]["translated"] = real_translated
                                        
                                        # 第三步：通知 UI 將「翻譯中...」換成真正嘅中文字
                                        if self.on_translation_complete:
                                            self.on_translation_complete(b_id, real_translated)
                                    
                                    except Exception as e:
                                        logger.error(f"背景翻譯失敗：{e}", exc_info=True)
                                
                                # 啟動獨立線程，唔阻礙主隊列聽下一句說話
                                threading.Thread(
                                    target=translate_task,
                                    args=(original, bubble_id, item_index),
                                    daemon=True,
                                    name="Translator"
                                ).start()
                    
                    finally:
                        try:
                            self.audio_queue.task_done()
                        except Exception as done_err:
                            logger.debug(f"task_done 錯誤：{done_err}")
                            
                except Exception as e:
                    logger.error(f"背景處理錯誤：{e}", exc_info=True)
                    continue
                    
        except Exception as e:
            logger.error(f"處理線程崩潰：{e}", exc_info=True)
    
    def process_audio_file(self, filepath: str) -> bool:
        """處理音訊檔案"""
        try:
            import librosa
            
            if not self.ai_ctrl.engines_ready:
                logger.warning("引擎尚未就緒")
                if self.on_status_change:
                    self.on_status_change("⚠️ 引擎未就緒", "#f59e0b")
                return False
            
            if self.on_status_change:
                self.on_status_change(f"📁 正在處理檔案：{Path(filepath).name}", "#f59e0b")
            
            logger.info(f"開始處理檔案：{filepath}")
            
            # 載入音訊檔案
            audio_data: np.ndarray
            sr: int
            audio_data, sr = librosa.load(filepath, sr=16000)
            
            # 轉換為正確格式
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            # 處理音訊
            original: str
            translated: str
            speaker: Optional[str]
            original, translated, speaker = self.ai_ctrl.process_audio(audio_data)
            
            if original and original.strip():
                speaker_id: int = 1 if speaker is None else (1 if "SPEAKER_00" in str(speaker) else 2)
                
                # 添加到歷史記錄
                subtitle_item: Dict[str, Any] = {
                    "original": original,
                    "translated": translated,
                    "speaker_id": speaker_id,
                    "timestamp": np.datetime64('now')
                }
                self.subtitles.append(subtitle_item)
                
                # 觸發回調
                if self.on_subtitle_update:
                    self.on_subtitle_update(original, translated, speaker_id)
                
                logger.info(f"檔案處理完成：{original[:50]}...")
            
            if self.on_status_change:
                self.on_status_change("✓ 檔案處理完成", "#10b981")
            
            return True
            
        except Exception as e:
            logger.error(f"檔案處理失敗：{e}", exc_info=True)
            if self.on_status_change:
                self.on_status_change(f"✗ 處理失敗：{str(e)}", "#ef4444")
            return False
    
    def save_subtitles(self, filepath: str) -> bool:
        """保存字幕為 SRT 檔"""
        try:
            srt_content: str = self._generate_srt()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"字幕已保存：{filepath}")
            
            if self.on_status_change:
                self.on_status_change("✓ 字幕已保存", "#10b981")
            
            return True
            
        except Exception as e:
            logger.error(f"保存字幕失敗：{e}", exc_info=True)
            if self.on_status_change:
                self.on_status_change("✗ 保存失敗", "#ef4444")
            return False
    
    def _generate_srt(self) -> str:
        """生成 SRT 字幕內容"""
        srt_lines: List[str] = []
        
        for idx, subtitle in enumerate(self.subtitles, 1):
            # 時間碼（簡化版本）
            start_time: str = f"00:00:{(idx-1):02d},000"
            end_time: str = f"00:00:{idx:02d},000"
            
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
            
            data: Dict[str, Any] = {
                "subtitles": self.subtitles,
                "settings": {
                    "target_language": self.target_lang,
                    "use_speaker_diarization": self.use_speaker_diarization,
                    "bilingual_mode": self.bilingual_mode
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"JSON 已匯出：{filepath}")
            return True
            
        except Exception as e:
            logger.error(f"匯出 JSON 失敗：{e}", exc_info=True)
            return False
    
    def clear_history(self) -> None:
        """清空歷史記錄"""
        self.subtitles = []
        logger.info("歷史記錄已清空")
    
    def cleanup(self) -> None:
        """清理資源"""
        try:
            logger.info("正在清理資源...")
            self.stop_recording()
            
            try:
                self.audio_mgr.cleanup()
            except Exception as e:
                logger.error(f"AudioManager 清理失敗：{e}", exc_info=True)
                
            try:
                self.ai_ctrl.cleanup()
            except Exception as e:
                logger.error(f"AIController 清理失敗：{e}", exc_info=True)
            
            # 釋放 GPU 記憶體
            if self.has_gpu and torch.cuda.is_available():
                try:
                    torch.cuda.empty_cache()
                    logger.info("GPU 記憶體已釋放")
                except Exception as e:
                    logger.error(f"GPU 記憶體釋放失敗：{e}", exc_info=True)
            
            logger.info("資源清理完成")
            
        except Exception as e:
            logger.error(f"清理資源失敗：{e}", exc_info=True)
