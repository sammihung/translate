"""
Controller Layer - 業務邏輯調控
負責連接 UI 層和數據層，管理應用程式的狀態和流程
"""

import threading
import queue
import time
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import torch

from qwen_asr_app.audio.audio_manager import AudioManager
from qwen_asr_app.ai.ai_controller import AIController
from qwen_asr_app.ai.worker_client import WorkerManager
from qwen_asr_app.core.logging_config import get_logger
from qwen_asr_app.core.model_registry import (
    PerformanceMode,
    PerformanceTier,
    get_performance_tier,
    get_all_tiers,
    get_tier_by_display_name,
    AVAILABLE_MODELS
)

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
        
        # 效能模式設定 (預設：平衡版)
        self.performance_mode: PerformanceMode = PerformanceMode.BALANCED
        self.current_tier: Optional[PerformanceTier] = None
        
        # 🚨 第一步：先定義硬體資訊 (必須放在 _auto_detect 之前) 🚨
        import torch
        try:
            # 🔧 FIX: 安全地 detect GPU，避免 hang
            self.has_gpu: bool = torch.cuda.is_available()
            if self.has_gpu:
                # 測試 CUDA 是否真係 work (避免得個名)
                try:
                    _ = torch.zeros(1).cuda()
                    self.gpu_vram_gb: float = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                    logger.info(f"檢測到 GPU VRAM: {self.gpu_vram_gb:.2f} GB")
                except Exception as e:
                    logger.warning(f"CUDA available 但無法使用，可能係無 GPU 硬件: {e}")
                    self.has_gpu = False
                    self.gpu_vram_gb = 0.0
            else:
                self.gpu_vram_gb = 0.0
        except Exception as e:
            logger.warning(f"GPU 檢測失敗，使用 CPU: {e}")
            self.has_gpu = False
            self.gpu_vram_gb = 0.0
        
        logger.info(f"GPU Available: {self.has_gpu}")
        
        # 🚨 第二步：有了 GPU 資訊後，再執行自動偵測 🚨
        self._auto_detect_performance_mode()
        logger.info(f"初始效能模式：{self.performance_mode.value}")
        
        # 回調函數
        self.on_subtitle_update: Optional[Callable[[str, str, int], str]] = None
        self.on_translation_complete: Optional[Callable[[str, str], None]] = None
        self.on_status_change: Optional[Callable[[str, str], None]] = None
        self.on_device_refresh: Optional[Callable[[], None]] = None
        
        # 🔧 優化 2: Thread Pool - 限制翻譯併發數量
        self.translate_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="Translator")
        
        # 設置
        self.target_lang: str = "zh"
        self.use_speaker_diarization: bool = False
        self.bilingual_mode: bool = True
        self.use_full_model: bool = False
            
        # 字幕歷史
        self.subtitles: List[Dict[str, Any]] = []
        # 語言變數
        self.src_lang: str = "auto"
        self.tgt_lang: str = "zh"
           
    def _auto_detect_performance_mode(self) -> None:
        """根據硬體自動偵測並設定效能模式"""
        try:
            # 檢測系統 RAM
            import psutil
            total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)
        except ImportError:
            total_ram_gb = 16.0  # 預設值
            logger.warning("無法檢測系統 RAM，使用預設值 16GB")
        
        # 1. 自動配對邏輯：同時決定 PerformanceMode 同 tier_key (字串)
        if self.has_gpu and self.gpu_vram_gb >= 12.0:
            self.performance_mode = PerformanceMode.FULL
            tier_key = "full"
            logger.info("自動設定：🩸 滿血版 (高階 GPU)")
        elif self.has_gpu and self.gpu_vram_gb >= 4.0:
            self.performance_mode = PerformanceMode.BALANCED
            tier_key = "balanced"
            logger.info("自動設定：⚖️ 平衡版 (入門 GPU)")
        elif total_ram_gb >= 16.0:
            self.performance_mode = PerformanceMode.BALANCED
            tier_key = "balanced"
            logger.info("自動設定：⚖️ 平衡版 (大 RAM)")
        else:
            self.performance_mode = PerformanceMode.FAST
            tier_key = "fast"
            logger.info("自動設定：⚡ 極速版 (低階硬體)")

        # 2. 載入對應的 ASR 配置
        # (確保 get_performance_tier 已經正確導入並定義)
        self.current_tier = get_performance_tier(self.performance_mode)
        logger.info(f"已載入 ASR 配置：{self.current_tier.display_name}")
            
        # 3. 根據 tier_key 設定對應的 Ollama 翻譯模型
        ollama_tiers = {
            "fast": "translategemma:4b-it-q4_K_M",    # 極速版 (4-bit)
            "balanced": "translategemma:4b-it-q8_0",  # 平衡版 (8-bit)
            "full": "translategemma:4b-it-fp16"       # 滿血版 (16-bit)
        }
        
        self.tgt_model_name = ollama_tiers.get(tier_key, "translategemma:4b-it-q4_K_M")
        logger.info(f"準備使用 Ollama 模型：{self.tgt_model_name}")
        
        # 4. 更新到 AI Controller 的翻譯引擎中
        if hasattr(self, 'ai_ctrl') and hasattr(self.ai_ctrl, 'translate_engine') and self.ai_ctrl.translate_engine:
            self.ai_ctrl.translate_engine.model_name = self.tgt_model_name
            self.ai_ctrl.translate_engine.loaded = False # 標記為未載入，強制重新預熱
                
    def set_performance_mode(self, mode: PerformanceMode) -> None:
        """
        手動設定效能模式
        
        Args:
            mode: 效能模式 (FAST/BALANCED/FULL)
        """
        if self.performance_mode == mode:
            logger.debug(f"效能模式已經是 {mode.value}")
            return
        
        self.performance_mode = mode
        self.current_tier = get_performance_tier(mode)
        
        logger.info(f"效能模式已切換：{self.current_tier.display_name}")
        logger.info(f"  ASR: {self.current_tier.asr.name} ({self.current_tier.asr.precision})")
        logger.info(f"  翻譯：{self.current_tier.translation.name} ({self.current_tier.translation.precision})")
        
        # 如果需要，可以觸發模型重新載入
        # self._reload_models_with_new_config()
    
    def get_performance_modes(self) -> list[str]:
        """獲取所有效能模式的顯示名稱 (用於 UI)"""
        return get_all_tiers()[0].__class__  # 返回所有 tier 的顯示名稱
    
    def get_current_model_config(self) -> tuple[str, str]:
        """
        獲取當前效能模式對應的模型配置
        
        Returns:
            (asr_repo, translation_model_tag)
        """
        if self.current_tier is None:
            # 如果未設定，使用預設
            self.current_tier = get_performance_tier(self.performance_mode)
        
        return (
            self.current_tier.asr.repo,
            self.current_tier.translation.model_tag
        )
    
    def initialize_engines(self, progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """初始化 AI 引擎 - 使用效能模式配置"""
        try:
            # 獲取當前效能模式的模型配置
            asr_repo, translation_tag = self.get_current_model_config()
            
            # 🔧 FIX: 優先使用戶既設定，如果冇先至用 default logic
            from qwen_asr_app.config import config
            user_device = config.asr_device.lower() if config.asr_device else None
            
            # 如果 user 已經設定咗 device (喺 .env 或 settings 度)
            if user_device and user_device in ["cpu", "cuda"]:
                device = user_device
                # 確保 user 選擇既 device 真係可用
                if device == "cuda" and not self.has_gpu:
                    logger.warning("User 選擇咗 CUDA 但檢測唔到 GPU，改用 CPU")
                    device = "cpu"
                logger.info(f"使用戶既設定: {device}")
            else:
                # 根據效能模式同 hardware 決定設備 (default logic)
                if self.performance_mode == PerformanceMode.FULL and self.has_gpu:
                    device = "cuda"
                elif self.performance_mode == PerformanceMode.BALANCED and self.has_gpu:
                    device = "cuda"
                else:
                    device = "cpu"
            
            logger.info(f"正在初始化引擎 (效能模式：{self.performance_mode.value})")
            logger.info(f"  ASR: {asr_repo} ({device})")
            logger.info(f"  翻譯：{translation_tag}")
            
            if progress_callback:
                progress_callback(f"載入 {self.current_tier.display_name} 配置...")
            
            success: bool = self.ai_ctrl.load_all_models(
                target_lang=self.target_lang,
                asr_model=asr_repo,
                device=device,
                progress_callback=progress_callback
            )
            
            if success:
                logger.info("引擎初始化成功")
                if progress_callback:
                    progress_callback(f"[OK] {self.current_tier.display_name} 已就緒")
            else:
                logger.error("引擎初始化失敗")
            
            return success
            
        except Exception as e:
            logger.error(f"引擎初始化失敗：{e}", exc_info=True)
            if progress_callback:
                progress_callback(f"[ERROR] 初始化失敗：{str(e)}")
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
        """更新設置 - 支持三階段模型切換 + VAD 參數"""
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
            
            # 🔧 更新翻譯模型 (Ollama) - 支持三階段
            if "translate_model" in settings:
                self.tgt_model_name = settings["translate_model"]
                
                if self.ai_ctrl.translate_engine:
                    self.ai_ctrl.translate_engine.model_name = self.tgt_model_name
                    self.ai_ctrl.translate_engine.loaded = False  # 強制重新載入
                    logger.info(f"翻譯模型已更新為：{self.tgt_model_name}")
            
            # 🔧 優化 3: 更新 VAD 參數
            if "vad_duration" in settings:
                vad_duration: float = settings["vad_duration"]
                # 計算 RMS 閾值 (簡單線性映射：1.0s=200, 3.0s=100)
                rms_threshold: float = 250.0 - (vad_duration - 0.5) * 75.0
                self.audio_mgr.set_vad_params(
                    rms_threshold=rms_threshold,
                    silence_duration=vad_duration,
                    max_duration=8.0
                )
                logger.info(f"VAD 參數已更新：RMS={rms_threshold:.1f}, 靜音={vad_duration}s")
            
            # 重新初始化 ASR
            logger.info(f"正在套用新設定：{target_asr} on {target_device}")
            
            # 載入模型較慢，在背景執行緒進行
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
            logger.info("🎯 [_processing_worker] 已啟動，等待音訊數據...")
            # 使用 Event 檢查停止信號，更加即時和安全
            while not self.recording_state.is_set():
                try:
                    # 從隊列獲取音訊數據 (使用 timeout 避免無限阻塞)
                    try:
                        audio_data: np.ndarray = self.audio_queue.get(timeout=0.5)
                        logger.info(f"🎯 [QUEUE] 收到音訊數據：shape={audio_data.shape}, duration={len(audio_data)/16000:.2f}s")
                    except queue.Empty:
                        continue
                    
                    try:
                        # 第一步：只做 ASR 辨識，跳過即時翻譯 (極速返回)
                        src_lang_param: str = getattr(self, 'src_lang', 'auto')
                        original: str
                        _: str
                        speaker: Optional[str]
                        logger.info(f"🎤 [ASR_START] 開始處理音訊...")
                        original, _, speaker = self.ai_ctrl.process_audio(
                            audio_data,
                            src_lang=src_lang_param,
                            skip_translation=True
                        )
                        logger.info(f"🎤 [ASR_RESULT] 原文：'{original[:100] if original else 'EMPTY'}', speaker={speaker}")
                        
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
                            logger.info(f"📢 [UI_CALLBACK] 準備更新 UI，原文：'{original[:50]}...'")
                            bubble_id: Optional[str] = None
                            if self.on_subtitle_update:
                                bubble_id = self.on_subtitle_update(original, placeholder_text, speaker_id)
                                logger.info(f"✅ [UI_CALLBACK] 完成，bubble_id={bubble_id}")
                            else:
                                logger.error("❌ [ERROR] on_subtitle_update 回調為 None!")
                            
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
                                
                                # 🔧 優化 2: 使用 Thread Pool 代替無限創建 Thread
                                self.translate_pool.submit(
                                    translate_task,
                                    original,
                                    bubble_id,
                                    item_index
                                )
                    
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
            
            # 🔧 優化 2: 安全關閉 ThreadPool
            if hasattr(self, 'translate_pool'):
                try:
                    self.translate_pool.shutdown(wait=False)
                    logger.info("Thread Pool 已關閉")
                except Exception as e:
                    logger.error(f"Thread Pool 關閉失敗：{e}", exc_info=True)
            
            # 🔧 優化 B: 清理 Batching 資源
            if hasattr(self, 'batch_timer') and self.batch_timer:
                try:
                    self.batch_timer.cancel()
                    logger.info("Batch 計時器已取消")
                except Exception as e:
                    logger.error(f"Batch 計時器清理失敗：{e}", exc_info=True)
            
            if hasattr(self, 'translation_buffer'):
                # 如果有未翻譯嘅句子，嘗試快速翻譯
                if self.translation_buffer:
                    logger.info(f"清理前翻譯緩衝區 ({len(self.translation_buffer)} 句)...")
                    # 可以選擇快速翻譯或者直接丟棄
            
            # 🧹 深度記憶體回收機制
            if self.has_gpu and torch.cuda.is_available():
                try:
                    import gc
                    gc.collect()  # 強制 Python GC 回收引用
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()  # 清理跨進程記憶體
                    logger.info("GPU 記憶體已深度釋放 (gc.collect + empty_cache + ipc_collect)")
                except Exception as e:
                    logger.error(f"GPU 記憶體釋放失敗：{e}", exc_info=True)
            
            logger.info("資源清理完成")
            
        except Exception as e:
            logger.error(f"清理資源失敗：{e}", exc_info=True)
