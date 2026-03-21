"""
AI Controller - AI 模型管理與推理
負責 ASR、VAD、翻譯、說話者分離的模型載入與推理
"""

from typing import Optional, Tuple, List, Callable
import threading
import numpy as np
from qwen_asr_app.core.logging_config import get_logger

logger = get_logger(__name__)


class AIController:
    """AI 控制器 - 管理所有 AI 模型"""
    
    def __init__(self) -> None:
        self.asr_engine = None
        self.translate_engine = None
        self.vad_processor = None
        self.speaker_diarization = None
        self.engines_ready: bool = False
        self.use_speaker_diarization: bool = True
    
    def load_all_models(
        self,
        target_lang: str = "zh",
        asr_model: str = "Qwen/Qwen3-ASR-0.6B",
        device: str = "cpu",
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        載入所有 AI 模型
        
        Args:
            target_lang: 目標語言
            asr_model: ASR 模型名稱
            device: 計算設備 (cpu/cuda)
            progress_callback: 進度回調函數
            
        Returns:
            是否成功載入
        """
        try:
            # 載入 ASR 模型
            if progress_callback:
                progress_callback(f"正在載入 {asr_model} ({device})...")
            
            logger.info(f"正在載入 ASR 模型：{asr_model}")
            
            try:
                from qwen_asr_app.ai.asr_engine import QwenASREngine
                # 🔧 FIX: 使用臨時變數，載入成功後才替換（避免 Race Condition）
                new_asr = QwenASREngine(model_name=asr_model, device=device)
                new_asr.load_model()
                self.asr_engine = new_asr  # 載入成功後才替換舊引擎
                logger.info("ASR 模型載入完成")
            except Exception as e:
                logger.error(f"ASR 模型載入失敗：{e}", exc_info=True)
                
            # 載入 VAD
            if progress_callback:
                progress_callback("正在初始化 VAD 處理器...")
            
            logger.info("正在載入 VAD 處理器")
            
            from qwen_asr_app.audio.vad_processor import VADProcessor
            self.vad_processor = VADProcessor()
            logger.info("✓ VAD 處理器載入完成")
            
            # 載入翻譯引擎
            if progress_callback:
                progress_callback(f"正在初始化翻譯引擎 (目標：{target_lang})...")
            
            logger.info(f"正在載入翻譯引擎，目標語言：{target_lang}")
            
            from qwen_asr_app.ai.asr_engine import TranslationEngine
            self.translate_engine = TranslationEngine(source_lang="zh", target_lang=target_lang)
            self.translate_engine.load_model()
            logger.info("✓ 翻譯引擎載入完成")
            
            # 載入說話者分離（可選）
            if self.use_speaker_diarization:
                if progress_callback:
                    progress_callback("正在初始化說話者分離...")
                
                logger.info("正在載入說話者分離模型")
                
                try:
                    from qwen_asr_app.ai.asr_engine import SpeakerDiarization
                    self.speaker_diarization = SpeakerDiarization()
                    self.speaker_diarization.load_pipeline()
                    logger.info("✓ 說話者分離載入完成")
                except Exception as e:
                    logger.warning(f"Speaker Diarization 載入失敗：{e}")
                    self.speaker_diarization = None
            
            self.engines_ready = True
            
            if progress_callback:
                if self.asr_engine and self.speaker_diarization:
                    progress_callback("[OK] 所有引擎已就緒 (ASR + VAD + 翻譯 + 說話者分離)")
                elif self.asr_engine:
                    progress_callback("[OK] 引擎已就緒 (ASR + VAD + 翻譯)")
                else:
                    progress_callback("[OK] 引擎已就緒 (VAD + 翻譯)")
            
            logger.info("所有引擎初始化完成")
            return True
            
        except Exception as e:
            self.engines_ready = False
            logger.error(f"引擎初始化失敗：{e}", exc_info=True)
            
            if progress_callback:
                progress_callback(f"[ERROR] 引擎初始化失敗：{str(e)}")
            
            return False
    
    def process_audio(
        self,
        audio: np.ndarray,
        src_lang: str = "auto",
        skip_translation: bool = False
    ) -> Tuple[str, str, Optional[str]]:
        """
        處理音訊數據
        
        Args:
            audio: 音訊數據 (numpy array)
            src_lang: 原始語言
            skip_translation: 是否跳過翻譯
            
        Returns:
            (original_text, translated_text, speaker_label)
        """
        try:
            if not self.engines_ready:
                logger.warning("引擎尚未就緒")
                return "", "", None
            
            if self.vad_processor is None:
                logger.error("VAD 處理器未載入")
                return "", "", None
            
            # VAD 偵測語音段落
            segments: List[Tuple[float, float]] = self.vad_processor.detect_speech_segments(audio)
            logger.debug(f"VAD 偵測到 {len(segments)} 個語音段落")
            
            results: List[Tuple[str, str, Optional[str]]] = []
            
            for start, end in segments:
                try:
                    # 截取語音片段
                    start_idx: int = int(start * 16000)
                    end_idx: int = int(end * 16000)
                    segment: np.ndarray = audio[start_idx:end_idx]
                    
                    # 跳過太短的片段
                    if len(segment) < 16000 * 0.5:  # 少於 0.5 秒
                        logger.debug(f"跳過過短片段：{len(segment)/16000:.2f}s")
                        continue
                    
                    # 說話者分離
                    speaker_label: Optional[str] = None
                    if self.speaker_diarization and self.speaker_diarization.loaded:
                        try:
                            diarization_results = self.speaker_diarization.diarize(segment)
                            if diarization_results and len(diarization_results) > 0:
                                _, _, speaker_label = diarization_results[0]
                                logger.debug(f"說話者識別：{speaker_label}")
                        except Exception as e:
                            logger.warning(f"Diarization error: {e}")
                    
                    # ASR 辨識
                    text: str = ""
                    if self.asr_engine:
                        try:
                            # 如果係 auto 就傳 None，否則傳對應語言代碼
                            lang_param: Optional[str] = None if src_lang == "auto" else src_lang
                            text = self.asr_engine.process_audio(segment, language=lang_param)
                            if text:
                                logger.debug(f"ASR 辨識結果：{text[:100]}...")
                        except Exception as e:
                            logger.error(f"ASR 處理錯誤：{e}", exc_info=True)
                    
                    # 翻譯
                    translated: str = ""
                    if not skip_translation and text.strip() and self.translate_engine:
                        try:
                            translated = self.translate_engine.translate(text)
                            logger.debug(f"翻譯結果：{translated[:100]}...")
                        except Exception as e:
                            logger.error(f"翻譯錯誤：{e}", exc_info=True)
                    
                    # 加上說話者標籤
                    if speaker_label:
                        text = f"[{speaker_label}] {text}"
                        translated = f"[{speaker_label}] {translated}"
                    
                    if text.strip():
                        results.append((text, translated, speaker_label))
                
                except Exception as e:
                    logger.error(f"處理語音段落失敗：{e}", exc_info=True)
                    continue
            
            # 返回最後一個結果（或多個結果合併）
            if results:
                logger.debug(f"返回 {len(results)} 個結果")
                return results[-1]
            
            logger.debug("未辨識到有效語音")
            return "", "", None
            
        except Exception as e:
            logger.error(f"process_audio 失敗：{e}", exc_info=True)
            return "", "", None
    
    def get_status(self) -> str:
        """獲取引擎狀態文字"""
        if not self.engines_ready:
            return "引擎未就緒"
        
        status_parts: List[str] = []
        if self.asr_engine:
            status_parts.append("ASR")
        if self.vad_processor:
            status_parts.append("VAD")
        if self.translate_engine:
            status_parts.append("翻譯")
        if self.speaker_diarization:
            status_parts.append("說話者分離")
        
        return " + ".join(status_parts)
    
    def cleanup(self) -> None:
        """清理資源"""
        try:
            logger.info("正在清理 AI 控制器資源...")
            
            # 卸載模型以釋放記憶體
            if self.asr_engine and hasattr(self.asr_engine, 'unload_model'):
                try:
                    self.asr_engine.unload_model()
                    logger.info("ASR 模型已卸載")
                except Exception as e:
                    logger.error(f"ASR 模型卸載失敗：{e}")
            
            if self.translate_engine and hasattr(self.translate_engine, 'unload_model'):
                try:
                    self.translate_engine.unload_model()
                    logger.info("翻譯模型已卸載")
                except Exception as e:
                    logger.error(f"翻譯模型卸載失敗：{e}")
            
            self.engines_ready = False
            logger.info("AI 控制器資源已清理")
            
        except Exception as e:
            logger.error(f"cleanup 失敗：{e}", exc_info=True)
    
    def translate_text(self, text: str) -> str:
        """
        獨立翻譯文字方法 (交俾背景 Thread 呼叫)
        
        Args:
            text: 需要翻譯的文字
            
        Returns:
            翻譯結果
        """
        if self.translate_engine:
            try:
                result: str = self.translate_engine.translate(text)
                logger.debug(f"背景翻譯完成：{text[:50]}... -> {result[:50]}...")
                return result
            except Exception as e:
                logger.error(f"獨立翻譯錯誤：{e}", exc_info=True)
        
        return text
