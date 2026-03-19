"""
AI Controller - AI 模型管理與推理
負責 ASR、VAD、翻譯、說話者分離的模型載入與推理
"""

from typing import Optional, Tuple, List
import threading
from datetime import datetime


class AIController:
    """AI 控制器 - 管理所有 AI 模型"""
    
    def __init__(self):
        self.asr_engine = None
        self.translate_engine = None
        self.vad_processor = None
        self.speaker_diarization = None
        self.engines_ready = False
        self.use_speaker_diarization = True
    
    def load_all_models(self, target_lang: str = "en", 
                        progress_callback: Optional[callable] = None) -> bool:
        """
        載入所有 AI 模型
        
        Args:
            target_lang: 翻譯目標語言
            progress_callback: 進度回調函數 (status_text: str)
            
        Returns:
            bool: 是否成功載入
        """
        try:
            # 載入 ASR 模型
            if progress_callback:
                progress_callback("正在初始化 ASR 引擎...")
            
            try:
                from asr_engine import QwenASREngine
                self.asr_engine = QwenASREngine(model_name="Qwen/Qwen3-ASR-0.6B", device="cpu")
                self.asr_engine.load_model()
                print("✓ ASR 引擎載入完成")
            except Exception as e:
                print(f"[WARN] ASR 模型載入失敗：{e}")
                self.asr_engine = None
            
            # 載入 VAD
            if progress_callback:
                progress_callback("正在初始化 VAD 處理器...")
            
            from vad_processor import VADProcessor
            self.vad_processor = VADProcessor()
            print("✓ VAD 處理器載入完成")
            
            # 載入翻譯引擎
            if progress_callback:
                progress_callback(f"正在初始化翻譯引擎 (目標：{target_lang})...")
            
            from asr_engine import TranslationEngine
            self.translate_engine = TranslationEngine(source_lang="zh", target_lang=target_lang)
            self.translate_engine.load_model()
            print("✓ 翻譯引擎載入完成")
            
            # 載入說話者分離（可選）
            if self.use_speaker_diarization:
                if progress_callback:
                    progress_callback("正在初始化說話者分離...")
                
                try:
                    from asr_engine import SpeakerDiarization
                    self.speaker_diarization = SpeakerDiarization()
                    self.speaker_diarization.load_pipeline()
                    print("✓ 說話者分離載入完成")
                except Exception as e:
                    print(f"[WARN] Speaker Diarization 載入失敗：{e}")
                    self.speaker_diarization = None
            
            self.engines_ready = True
            
            if progress_callback:
                if self.asr_engine and self.speaker_diarization:
                    progress_callback("[OK] 所有引擎已就緒 (ASR + VAD + 翻譯 + 說話者分離)")
                elif self.asr_engine:
                    progress_callback("[OK] 引擎已就緒 (ASR + VAD + 翻譯)")
                else:
                    progress_callback("[OK] 引擎已就緒 (VAD + 翻譯)")
            
            return True
            
        except Exception as e:
            self.engines_ready = False
            if progress_callback:
                progress_callback(f"[ERROR] 引擎初始化失敗：{str(e)}")
            print(f"[ERROR] 引擎初始化失敗：{e}")
            return False
    
    def process_audio(self, audio: np.ndarray) -> Tuple[str, str, Optional[str]]:
        """
        處理音訊數據
        
        Args:
            audio: 音訊數據 (numpy array)
            
        Returns:
            (original_text, translated_text, speaker_label)
        """
        if not self.engines_ready:
            return "", "", None
        
        if self.vad_processor is None:
            return "", "", None
        
        # VAD 偵測語音段落
        segments = self.vad_processor.detect_speech_segments(audio)
        
        results = []
        
        for start, end in segments:
            # 截取語音片段
            start_idx = int(start * 16000)
            end_idx = int(end * 16000)
            segment = audio[start_idx:end_idx]
            
            # 跳過太短的片段
            if len(segment) < 16000 * 0.5:  # 少於 0.5 秒
                continue
            
            # 說話者分離
            speaker_label = None
            if self.speaker_diarization and self.speaker_diarization.loaded:
                try:
                    diarization_results = self.speaker_diarization.diarize(segment)
                    if diarization_results and len(diarization_results) > 0:
                        _, _, speaker_label = diarization_results[0]
                except Exception as e:
                    print(f"[WARN] Diarization error: {e}")
            
            # ASR 辨識
            text = ""
            if self.asr_engine:
                try:
                    text = self.asr_engine.process_audio(segment)
                except Exception as e:
                    print(f"ASR 處理錯誤：{e}")
            
            # 翻譯
            translated = ""
            if text.strip() and self.translate_engine:
                try:
                    translated = self.translate_engine.translate(text)
                except Exception as e:
                    print(f"翻譯錯誤：{e}")
            
            # 加上說話者標籤
            if speaker_label:
                text = f"[{speaker_label}] {text}"
                translated = f"[{speaker_label}] {translated}"
            
            if text.strip():
                results.append((text, translated, speaker_label))
        
        # 返回最後一個結果（或多個結果合併）
        if results:
            return results[-1]
        return "", "", None
    
    def get_status(self) -> str:
        """獲取引擎狀態文字"""
        if not self.engines_ready:
            return "引擎未就緒"
        
        status_parts = []
        if self.asr_engine:
            status_parts.append("ASR")
        if self.vad_processor:
            status_parts.append("VAD")
        if self.translate_engine:
            status_parts.append("翻譯")
        if self.speaker_diarization:
            status_parts.append("說話者分離")
        
        return " + ".join(status_parts)
    
    def cleanup(self):
        """清理資源"""
        # 可以在這裡添加模型卸載邏輯
        pass
