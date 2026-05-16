import time
import numpy as np
from typing import Optional, List, Callable
from core.logging_config import get_logger

logger = get_logger(__name__)


class SimpleVAD:
    """
    Silero VAD + Sliding window + 0.5s overlap
    No fallback - Silero or nothing
    """

    OVERLAP_SECONDS = 0.5
    SAMPLE_RATE = 16000
    FRAME_SIZE = 512

    def __init__(self, rms_threshold=50.0, silence_duration=0.8, max_chunk_duration=4.0, speech_duration=2.0, aggressiveness=3):
        self.silence_duration = silence_duration
        self.max_chunk_duration = max_chunk_duration
        self.speech_duration = speech_duration

        self.buffer: List[float] = []
        self.overlap_buffer: List[float] = []
        self.silence_start: Optional[float] = None
        self.chunk_start_time: Optional[float] = None
        self.speech_start: Optional[float] = None

        self._model = None
        self._iterator = None
        self._loaded = False

    def _load_silero(self):
        if self._loaded:
            return
        try:
            import torch
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
                trust_repo=True
            )
            model.eval()
            self._model = model
            self._iterator = utils[3](model, threshold=0.5)
            self._loaded = True
            logger.info("Silero VAD loaded")
        except Exception as e:
            logger.error(f"Silero VAD failed to load: {e}")
            raise

    def reset(self):
        self.buffer = []
        self.overlap_buffer = []
        self.silence_start = None
        self.chunk_start_time = None
        self.speech_start = None
        if self._iterator:
            self._iterator.reset_states()

    def _is_speech(self, audio_np: np.ndarray) -> bool:
        import torch
        
        audio_int16 = (np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16)
        
        while len(audio_int16) >= self.FRAME_SIZE:
            frame = audio_int16[:self.FRAME_SIZE]
            audio_int16 = audio_int16[self.FRAME_SIZE:]
            
            audio_float = torch.from_numpy(frame.astype(np.float32) / 32767.0)
            result = self._iterator(audio_float, self.SAMPLE_RATE)
            
            if result and 'start' in result:
                return True
            if result and 'end' in result:
                return False
        
        return getattr(self._iterator, 'is_speech', False) if self._iterator else False

    def process_chunk(self, audio_np: np.ndarray, callback: Callable[[np.ndarray], None]):
        if not self._loaded:
            self._load_silero()

        current_time = time.time()

        if self.chunk_start_time is None and len(self.buffer) == 0:
            self.chunk_start_time = current_time
            if self.overlap_buffer:
                self.buffer = list(self.overlap_buffer)

        is_speech = self._is_speech(audio_np)
        self.buffer.extend(audio_np.tolist())

        should_process = False
        reason = ""
        buffer_duration = len(self.buffer) / self.SAMPLE_RATE

        if is_speech:
            if self.speech_start is None:
                self.speech_start = current_time
                logger.debug("Silero: speech START")
            self.silence_start = None

            if (current_time - self.speech_start) >= self.speech_duration:
                if buffer_duration >= 1.0:
                    should_process = True
                    reason = f"speech_duration ({self.speech_duration}s)"
                    self.speech_start = None
        else:
            if self.silence_start is None:
                self.silence_start = current_time
            elif (current_time - self.silence_start) >= self.silence_duration:
                if buffer_duration >= 0.5:
                    should_process = True
                    reason = "silence"
                    logger.debug("Silero: speech END")
                self.speech_start = None

        if self.chunk_start_time and (current_time - self.chunk_start_time) >= self.max_chunk_duration:
            if buffer_duration >= 0.5:
                should_process = True
                reason = f"timeout ({self.max_chunk_duration}s)"
            self.speech_start = None

        if should_process:
            overlap_samples = int(self.OVERLAP_SECONDS * self.SAMPLE_RATE)
            if len(self.buffer) > overlap_samples:
                self.overlap_buffer = self.buffer[-overlap_samples:]
            else:
                self.overlap_buffer = list(self.buffer)

            audio_to_send = np.array(self.buffer)
            logger.info(f"VAD send: {len(audio_to_send)} samples ({buffer_duration:.1f}s), trigger={reason}")
            callback(audio_to_send)

            self.buffer = []
            self.chunk_start_time = current_time
            self.silence_start = None