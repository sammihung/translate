"""
Controller Layer - 業務邏輯調控
連接 UI 層和 AI 層，所有模型配置由 .env / UI 動態設定
"""

import threading
import queue
import time
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from audio.audio_manager import AudioManager
from ai.ai_controller import AIController
from core.logging_config import get_logger
from config.settings import config
from domain.events import AppCallbacks

logger = get_logger(__name__)


class RecordingState:
    """使用 Event 管理錄音狀態"""
    
    def __init__(self) -> None:
        self._stop_event: threading.Event = threading.Event()
        self._is_recording: bool = False
    
    def start(self) -> None:
        self._stop_event.clear()
        self._is_recording = True
    
    def stop(self) -> None:
        self._is_recording = False
        self._stop_event.set()
    
    def is_recording(self) -> bool:
        return self._is_recording
    
    def wait_for_stop(self, timeout: Optional[float] = None) -> bool:
        return self._stop_event.wait(timeout=timeout)
    
    def is_set(self) -> bool:
        return self._stop_event.is_set()


class AppController:
    """應用程式控制器 - 配置驅動，唔硬编码 model"""
    
    def __init__(self) -> None:
        self.audio_mgr: AudioManager = AudioManager()
        self.ai_ctrl: AIController = AIController()
        
        self.recording_state: RecordingState = RecordingState()
        self.is_recording: bool = False
        self.audio_source: str = config.audio_source
        
        self.record_thread: Optional[threading.Thread] = None
        self.process_thread: Optional[threading.Thread] = None
        
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=10)
        
        self.callbacks: AppCallbacks = AppCallbacks()
        
        self.translate_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="Translator")
        
        self.target_lang: str = "zh"
        self.src_lang: str = "auto"
        self.tgt_lang: str = "zh"
        self.bilingual_mode: bool = True
        self.subtitles: List[Dict[str, Any]] = []
    
    def initialize_engines(self, progress_callback: Optional[Callable] = None) -> bool:
        """初始化引擎 - 用 config 中嘅設定"""
        try:
            success: bool = self.ai_ctrl.load_all_models(
                target_lang=self.target_lang,
                progress_callback=progress_callback
            )
            
            if success:
                logger.info("引擎初始化成功")
            else:
                logger.error("引擎初始化失敗")
            
            return success
        except Exception as e:
            logger.error(f"引擎初始化失敗：{e}", exc_info=True)
            if progress_callback:
                progress_callback(f"[ERROR] 初始化失敗：{str(e)}")
            return False
    
    def update_config(self, settings: Dict[str, Any]) -> None:
        try:
            from config.settings import config
            
            if "asr_model" in settings:
                config.asr_model = settings["asr_model"]
            if "asr_api_url" in settings:
                config.asr_api_url = settings["asr_api_url"]
            if "asr_api_key" in settings:
                config.asr_api_key = settings["asr_api_key"]
            
            if "translate_model" in settings:
                config.translate_model = settings["translate_model"]
            if "translate_api_url" in settings:
                config.translate_api_url = settings["translate_api_url"]
            if "translate_api_key" in settings:
                config.translate_api_key = settings["translate_api_key"]
            
            if "vad_duration" in settings:
                vad_duration: float = settings["vad_duration"]
                rms_threshold: float = 250.0 - (vad_duration - 0.5) * 75.0
                self.audio_mgr.set_vad_params(
                    rms_threshold=rms_threshold,
                    silence_duration=vad_duration,
                    max_duration=8.0
                )
            
            self._save_env()
            
            logger.info(f"Config updated: ASR={config.asr_model}@{config.asr_api_url}, Translate={config.translate_model}@{config.translate_api_url}")
            
            def reload() -> None:
                try:
                    self.ai_ctrl.load_all_models(target_lang=self.target_lang)
                    logger.info("引擎重新載入完成")
                except Exception as e:
                    logger.error(f"引擎重新載入失敗：{e}", exc_info=True)
            
            threading.Thread(target=reload, daemon=True).start()
            
        except Exception as e:
            logger.error(f"更新配置失敗：{e}", exc_info=True)
            raise
    
    def _save_env(self) -> None:
        try:
            from config.settings import config
            env_path = Path(".env")
            lines = []
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            
            env_map = {
                "ASR_MODEL": config.asr_model,
                "ASR_API_URL": config.asr_api_url,
                "ASR_API_KEY": config.asr_api_key or "",
                "TRANSLATE_MODEL": config.translate_model,
                "TRANSLATE_API_URL": config.translate_api_url,
                "TRANSLATE_API_KEY": config.translate_api_key or "",
            }
            
            updated_keys = set()
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key = stripped.split("=", 1)[0].strip()
                    if key in env_map:
                        new_lines.append(f"{key}={env_map[key]}\n")
                        updated_keys.add(key)
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            for key, value in env_map.items():
                if key not in updated_keys:
                    new_lines.append(f"{key}={value}\n")
            
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            
            logger.info(f".env saved with updated config")
        except Exception as e:
            logger.error(f"Failed to save .env: {e}")
    
    def set_audio_source(self, source: str, target_app: str = "") -> None:
        self.audio_source = source
        self.audio_mgr.set_audio_source(source, target_app)
        logger.info(f"Audio source set to: {source}, target_app={target_app}")
    
    def get_audio_devices(self, source: str = "mic") -> List[str]:
        try:
            self.audio_mgr.set_audio_source(source)
            return self.audio_mgr.get_audio_devices()
        except Exception as e:
            logger.error(f"獲取設備列表失敗：{e}")
            return []
    
    def is_engines_ready(self) -> bool:
        return self.ai_ctrl.engines_ready
    
    def get_current_config(self) -> Dict[str, Any]:
        return {
            "asr_model": config.asr_model,
            "asr_api_url": config.asr_api_url,
            "asr_api_key": config.asr_api_key or "",
            "translate_model": config.translate_model,
            "translate_api_url": config.translate_api_url,
            "translate_api_key": config.translate_api_key or ""
        }
    
    def set_settings(self, settings: Dict[str, Any]) -> None:
        """由 UI 儲存設定時呼叫"""
        self.update_config(settings)
    
    def start_recording(self, device_index: Optional[int] = None) -> bool:
        try:
            if self.recording_state.is_recording():
                return False
            
            if not self.ai_ctrl.engines_ready:
                if self.on_status_change:
                    self.on_status_change("⚠️ 引擎未就緒", "#f59e0b")
                return False
            
            self.recording_state.start()
            self.is_recording = True
            
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            self.process_thread = threading.Thread(
                target=self._processing_worker, daemon=True, name="AudioProcessor"
            )
            self.process_thread.start()
            
            self.record_thread = threading.Thread(
                target=self._recording_thread, args=(device_index,),
                daemon=True, name="AudioRecorder"
            )
            self.record_thread.start()
            
            self.callbacks.notify_status_change("🔴 錄音中...", "#ef4444")
            
            return True
        except Exception as e:
            logger.error(f"啟動錄音失敗：{e}", exc_info=True)
            self.recording_state.stop()
            self.is_recording = False
            return False
    
    def stop_recording(self) -> None:
        try:
            self.recording_state.stop()
            self.is_recording = False
            try:
                self.audio_mgr.stop_recording()
            except Exception:
                pass
            
            self.callbacks.notify_status_change("⏳ 正在處理最後的音訊...", "#f59e0b")
            
            def finish() -> None:
                try:
                    self.audio_queue.join()
                    self.callbacks.notify_status_change("⏹ 已停止", "#94a3b8")
                except Exception as e:
                    logger.error(f"等待隊列清空時出錯：{e}")
            
            threading.Thread(target=finish, daemon=True).start()
        except Exception as e:
            logger.error(f"停止錄音失敗：{e}", exc_info=True)
    
    def _recording_thread(self, device_index: Optional[int]) -> None:
        try:
            def on_audio_data(audio_np: np.ndarray) -> None:
                try:
                    self.audio_queue.put(audio_np, block=True, timeout=2.0)
                except queue.Full:
                    logger.warning("音訊隊列已滿")
            
            if device_index is None:
                devices = self.audio_mgr.get_audio_devices()
                device_index = self.audio_mgr.parse_device_index(
                    devices[0] if devices else "default"
                )
            
            self.audio_mgr.start_recording(device_index, callback=on_audio_data)
        except Exception as e:
            logger.error(f"錄音線程出錯：{e}", exc_info=True)
            self.recording_state.stop()
            self.is_recording = False
    
    def _processing_worker(self) -> None:
        try:
            while not self.recording_state.is_set():
                try:
                    try:
                        audio_data = self.audio_queue.get(timeout=0.5)
                    except queue.Empty:
                        continue
                    
                    try:
                        src_lang_param = getattr(self, 'src_lang', 'auto')
                        original, _, speaker = self.ai_ctrl.process_audio(
                            audio_data, src_lang=src_lang_param, skip_translation=True
                        )
                        
                        if original and original.strip():
                            speaker_id = 1 if speaker is None else (1 if "SPEAKER_00" in str(speaker) else 2)
                            
                            subtitle_item = {
                                "original": original,
                                "translated": "⏳ 翻譯中...",
                                "speaker_id": speaker_id,
                                "timestamp": np.datetime64('now')
                            }
                            self.subtitles.append(subtitle_item)
                            item_index = len(self.subtitles) - 1
                            
                            bubble_id = self.callbacks.notify_subtitle_update(original, "⏳ 翻譯中...", speaker_id)
                            
                            if bubble_id:
                                def translate_task(text, b_id, idx) -> None:
                                    try:
                                        real_translated = self.ai_ctrl.translate_text(text)
                                        if idx < len(self.subtitles):
                                            self.subtitles[idx]["translated"] = real_translated
                                        self.callbacks.notify_translation_complete(b_id, real_translated)
                                    except Exception as e:
                                        logger.error(f"背景翻譯失敗：{e}", exc_info=True)
                                
                                self.translate_pool.submit(translate_task, original, bubble_id, item_index)
                    finally:
                        try:
                            self.audio_queue.task_done()
                        except Exception:
                            pass
                        
                except Exception as e:
                    logger.error(f"背景處理錯誤：{e}", exc_info=True)
                    continue
        except Exception as e:
            logger.error(f"處理線程崩潰：{e}", exc_info=True)
    
    def process_audio_file(self, filepath: str) -> bool:
        try:
            import librosa
            
            if not self.ai_ctrl.engines_ready:
                self.callbacks.notify_status_change("⚠️ 引擎未就緒", "#f59e0b")
                return False
            
            audio_data, sr = librosa.load(filepath, sr=16000)
            
            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            original, translated, speaker = self.ai_ctrl.process_audio(audio_data)
            
            if original and original.strip():
                speaker_id = 1 if speaker is None else (1 if "SPEAKER_00" in str(speaker) else 2)
                
                self.subtitles.append({
                    "original": original,
                    "translated": translated,
                    "speaker_id": speaker_id,
                    "timestamp": np.datetime64('now')
                })
                
                self.callbacks.notify_subtitle_update(original, translated, speaker_id)
            
            self.callbacks.notify_status_change("✓ 檔案處理完成", "#10b981")
            
            return True
        except Exception as e:
            logger.error(f"檔案處理失敗：{e}", exc_info=True)
            return False
    
    def save_subtitles(self, filepath: str) -> bool:
        try:
            srt_content = self._generate_srt()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            logger.info(f"字幕已保存：{filepath}")
            return True
        except Exception as e:
            logger.error(f"保存字幕失敗：{e}")
            return False
    
    def _generate_srt(self) -> str:
        srt_lines = []
        for idx, subtitle in enumerate(self.subtitles, 1):
            start_time = f"00:00:{(idx-1):02d},000"
            end_time = f"00:00:{idx:02d},000"
            srt_lines.append(str(idx))
            srt_lines.append(f"{start_time} --> {end_time}")
            if self.bilingual_mode:
                srt_lines.append(subtitle['original'])
                srt_lines.append(subtitle['translated'])
            else:
                srt_lines.append(subtitle['translated'])
            srt_lines.append("")
        return "\n".join(srt_lines)
    
    def clear_history(self) -> None:
        self.subtitles = []
    
    def cleanup(self) -> None:
        try:
            self.stop_recording()
            self.audio_mgr.cleanup()
            self.ai_ctrl.cleanup()
            self.translate_pool.shutdown(wait=False)
        except Exception as e:
            logger.error(f"清理資源失敗：{e}", exc_info=True)