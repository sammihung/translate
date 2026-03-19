"""
Qwen3-ASR 推理引擎 - 使用官方 qwen-asr 套件
基於 Transformers 後端，支持流式推理
"""

import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
import torch


class SpeakerDiarization:
    """說話者分離模組 - 使用 PyAnnote"""
    
    def __init__(self):
        """初始化說話者分離"""
        self.pipeline = None
        self.loaded = False
        self.min_speakers = 1
        self.max_speakers = 4
        
    def load_pipeline(self):
        """載入 PyAnnote 說話者分離模型"""
        if self.loaded:
            return
        
        print("Loading Speaker Diarization pipeline...")
        
        try:
            from pyannote.audio import Pipeline
            
            # 使用預訓練模型（需要 HuggingFace token）
            # 注意：需要接受 pyannote 的條款並獲取 token
            # 獲取 token: https://hf.co/settings/tokens
            try:
                from huggingface_hub import login
                import os
                token = os.getenv("HF_TOKEN")
                if token:
                    login(token=token)
            except:
                pass
            
            # 載入模型
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=True
            )
            
            if self.pipeline:
                self.loaded = True
                print("[OK] Speaker Diarization loaded")
            else:
                print("[WARN] Speaker Diarization load failed - running without speaker separation")
                
        except Exception as e:
            print(f"[WARN] Speaker Diarization load failed: {e}")
            print("Will run without speaker separation")
            self.pipeline = None
    
    def diarize(self, audio: np.ndarray, sample_rate: int = 16000) -> List[Tuple[float, float, str]]:
        """
        執行說話者分離
        
        Args:
            audio: 音訊數據 (float32, mono)
            sample_rate: 取樣率
            
        Returns:
            說話者段落列表 [(start, end, speaker_id), ...]
        """
        if not self.loaded or self.pipeline is None:
            return []
        
        try:
            import torch
            from torch import FloatTensor
            from pyannote.audio import Audio
            
            # 轉換為 torch tensor
            audio_tensor = FloatTensor(audio.astype(np.float32))
            
            # 執行說話者分離
            diarization = self.pipeline(
                {"waveform": audio_tensor.unsqueeze(0), "sample_rate": sample_rate},
                min_speakers=self.min_speakers,
                max_speakers=self.max_speakers
            )
            
            # 提取結果
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                start = turn.start
                end = turn.end
                # 格式化說話者標籤為更易讀的形式
                speaker_name = f"Role {speaker.replace('SPEAKER_', '')}"
                segments.append((start, end, speaker_name))
            
            return segments
            
        except Exception as e:
            print(f"[WARN] Diarization failed: {e}")
            return []
    
    def set_num_speakers(self, min_speakers: int = 1, max_speakers: int = 4):
        """設定說話者數量範圍"""
        self.min_speakers = min_speakers
        self.max_speakers = max_speakers


class QwenASREngine:
    def __init__(self, model_name: str = "Qwen/Qwen3-ASR-0.6B", device: str = "cpu"):
        """
        初始化 ASR 引擎
        
        Args:
            model_name: HuggingFace 模型名稱
            device: 推理裝置 ("cpu" 或 "cuda")
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.loaded = False
        
    def load_model(self):
        """載入 ASR 模型"""
        if self.loaded:
            return
            
        print(f"Loading ASR model: {self.model_name}...")
        
        try:
            from qwen_asr import Qwen3ASRModel
            
            # 確定 dtype
            if self.device == "cuda":
                dtype = torch.float16
            else:
                dtype = torch.float32
            
            # 載入模型
            self.model = Qwen3ASRModel.from_pretrained(
                self.model_name,
                dtype=dtype,
                device_map=self.device,
                max_new_tokens=256,
            )
            
            self.loaded = True
            print(f"[OK] ASR model loaded ({self.device})")
            
        except Exception as e:
            print(f"[WARN] ASR model load failed: {e}")
            self.model = None
            self.loaded = False
    
    def process_audio(self, audio: np.ndarray, sample_rate: int = 16000, language: str = None) -> str:
        """
        處理音訊並返回轉錄文字
        
        Args:
            audio: 音訊數據 (float32, mono)
            sample_rate: 取樣率 (預設 16kHz)
            language: 語言設定 (None = 自動偵測, "Chinese", "English" 等)
            
        Returns:
            轉錄文字
        """
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            return ""
        
        try:
            # 確保 audio 是 float32
            audio = audio.astype(np.float32)
            
            # 重取樣到 16kHz (如果需要)
            if sample_rate != 16000:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=16000)
            
            # 執行轉錄
            results = self.model.transcribe(
                audio=(audio, 16000),
                language=language,
            )
            
            # 提取文字
            if results and len(results) > 0:
                text = results[0].text
                return text.strip()
            else:
                return ""
                
        except Exception as e:
            print(f"ASR 辨識錯誤：{e}")
            return ""
    
    def process_audio_with_timestamps(self, audio: np.ndarray, sample_rate: int = 16000, language: str = None):
        """
        處理音訊並返回帶時間戳的結果
        
        Args:
            audio: 音訊數據
            sample_rate: 取樣率
            language: 語言設定
            
        Returns:
            dict: {text: str, language: str, timestamps: List}
        """
        if self.model is None:
            self.load_model()
        
        if self.model is None:
            return {"text": "", "language": "", "timestamps": []}
        
        try:
            from qwen_asr import Qwen3ForcedAligner
            
            # 確保 audio 是 float32
            audio = audio.astype(np.float32)
            
            # 重取樣到 16kHz
            if sample_rate != 16000:
                from librosa import resample
                audio = resample(audio, orig_sr=sample_rate, target_sr=16000)
            
            # 先進行 ASR 辨識
            asr_results = self.model.transcribe(
                audio=(audio, 16000),
                language=language,
                return_time_stamps=True,
            )
            
            if asr_results and len(asr_results) > 0:
                result = asr_results[0]
                return {
                    "text": result.text.strip(),
                    "language": getattr(result, 'language', ''),
                    "timestamps": getattr(result, 'time_stamps', [])
                }
            
            return {"text": "", "language": "", "timestamps": []}
            
        except Exception as e:
            print(f"ASR 時間戳辨識錯誤：{e}")
            return {"text": "", "language": "", "timestamps": []}
    
    def set_language(self, language: str = "auto"):
        """
        設定辨識語言（此方法僅用於介面相容性）
        
        Args:
            language: 語言代碼 ("zh", "en", "ja", "auto" 等)
        """
        # qwen-asr 在 transcribe 時指定語言
        pass


class TranslationEngine:
    """翻譯引擎 - 使用 Qwen 多語言模型"""
    
    def __init__(self, source_lang: str = "zh", target_lang: str = "en"):
        """
        初始化翻譯引擎
        
        Args:
            source_lang: 來源語言 (ignored for multilingual model)
            target_lang: 目標語言
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.model = None
        self.tokenizer = None
        self.loaded = False
        
        # 使用多語言翻譯模型 - NLLB 支持 200+ 語言
        # 或使用 Helsinki-NLP 的 zh-en 模型
        if target_lang == "en":
            self.model_name = "Helsinki-NLP/opus-mt-zh-en"
        elif target_lang == "zh":
            self.model_name = "Helsinki-NLP/opus-mt-en-zh"
        else:
            # 對於其他語言，使用 NLLB 模型
            self.model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}" if source_lang != "auto" else None
    
    def load_model(self):
        """載入翻譯模型"""
        if self.loaded:
            return
            
        if not self.model_name:
            print(f"Translation model not set (source={self.source_lang}, target={self.target_lang})")
            return
            
        try:
            from transformers import MarianMTModel, MarianTokenizer
            
            print(f"Loading translation model: {self.model_name}...")
            self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
            self.model = MarianMTModel.from_pretrained(self.model_name)
            self.loaded = True
            print(f"[OK] Translation model loaded")
            
        except Exception as e:
            print(f"[WARN] Translation model load failed: {e}")
            # 嘗試回退到 zh-en 模型
            if self.target_lang == "en" and self.model_name != "Helsinki-NLP/opus-mt-zh-en":
                print("Trying fallback to zh-en model...")
                try:
                    self.model_name = "Helsinki-NLP/opus-mt-zh-en"
                    from transformers import MarianMTModel, MarianTokenizer
                    self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
                    self.model = MarianMTModel.from_pretrained(self.model_name)
                    self.loaded = True
                    print(f"[OK] Translation model loaded (fallback)")
                except:
                    pass
            self.model = None
    
    def translate(self, text: str) -> str:
        """
        翻譯文字
        
        Args:
            text: 要翻譯的文字
            
        Returns:
            翻譯後的文字
        """
        if not text.strip():
            return ""
        
        if self.model is None or self.tokenizer is None:
            self.load_model()
        
        if self.model is None or self.tokenizer is None:
            return text  # 返回原文
        
        try:
            import torch
            
            # Tokenize
            inputs = self.tokenizer(text, return_tensors="pt", padding=True)
            
            # 翻譯
            with torch.no_grad():
                translated = self.model.generate(**inputs)
            
            # 解碼
            result = self.tokenizer.decode(translated[0], skip_special_tokens=True)
            
            return result
            
        except Exception as e:
            print(f"翻譯錯誤：{e}")
            return text  # 返回原文


class SubtitleGenerator:
    """雙語字幕生成器"""
    
    def __init__(self):
        self.segments: List[dict] = []
    
    def add_segment(self, start: float, end: float, original: str, translated: str, speaker: Optional[str] = None):
        """
        添加字幕段落
        
        Args:
            start: 開始時間（秒）
            end: 結束時間（秒）
            original: 原文
            translated: 譯文
            speaker: 說話者（可選）
        """
        self.segments.append({
            'start': start,
            'end': end,
            'original': original,
            'translated': translated,
            'speaker': speaker
        })
    
    def format_time(self, seconds: float) -> str:
        """將秒數轉換為 SRT 時間格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def export_srt(self, filepath: str, dual_language: bool = True):
        """
        匯出 SRT 字幕檔
        
        Args:
            filepath: 輸出檔案路徑
            dual_language: 是否輸出雙語
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            for i, seg in enumerate(self.segments, 1):
                # 序號
                f.write(f"{i}\n")
                
                # 時間軸
                f.write(f"{self.format_time(seg['start'])} --> {self.format_time(seg['end'])}\n")
                
                # 文字
                if seg.get('speaker'):
                    f.write(f"{seg['speaker']}: ")
                
                if dual_language:
                    f.write(f"{seg['original']}\n")
                    f.write(f"{seg['translated']}\n")
                else:
                    f.write(f"{seg['translated']}\n")
                
                f.write("\n")
        
        print(f"✅ 字幕已匯出：{filepath}")
