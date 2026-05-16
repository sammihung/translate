import time
import numpy as np
from typing import Optional, List, Callable

try:
    import webrtcvad
    HAS_WEBRTC = True
except ImportError:
    HAS_WEBRTC = False


class SimpleVAD:

    def __init__(self, rms_threshold=150.0, silence_duration=1.5, max_chunk_duration=8.0, aggressiveness=3):
        self.rms_threshold = rms_threshold
        self.silence_duration = silence_duration
        self.max_chunk_duration = max_chunk_duration
        self.aggressiveness = aggressiveness

        self.buffer: List[float] = []
        self.silence_start: Optional[float] = None
        self.chunk_start_time: Optional[float] = None

        self._use_webrtc = HAS_WEBRTC
        if HAS_WEBRTC:
            self._vad = webrtcvad.Vad(aggressiveness)
            self._frame_duration_ms = 30
            self._frame_size = int(16000 * (self._frame_duration_ms / 1000.0))
            self._frame_bytes = self._frame_size * 2
            self._byte_buffer = bytearray()

    def reset(self):
        self.buffer = []
        self.silence_start = None
        self.chunk_start_time = None
        if self._use_webrtc:
            self._byte_buffer = bytearray()

    def _is_speech_webrtc(self, audio_np: np.ndarray) -> bool:
        audio_int16 = (np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16)
        self._byte_buffer.extend(audio_int16.tobytes())

        speech_frames = 0
        total_frames = 0

        while len(self._byte_buffer) >= self._frame_bytes:
            frame_bytes = bytes(self._byte_buffer[:self._frame_bytes])
            self._byte_buffer = self._byte_buffer[self._frame_bytes:]
            try:
                if self._vad.is_speech(frame_bytes, 16000):
                    speech_frames += 1
            except Exception:
                pass
            total_frames += 1

        if total_frames == 0:
            return False
        return (speech_frames / total_frames) > 0.3

    def _is_speech_rms(self, audio_np: np.ndarray) -> bool:
        rms = np.sqrt(np.mean(audio_np ** 2)) * 1000
        return rms >= self.rms_threshold

    def process_chunk(self, audio_np: np.ndarray, callback: Callable[[np.ndarray], None]):
        current_time = time.time()

        if self.chunk_start_time is None and len(self.buffer) == 0:
            self.chunk_start_time = current_time

        if self._use_webrtc:
            is_speech = self._is_speech_webrtc(audio_np)
        else:
            is_speech = self._is_speech_rms(audio_np)

        self.buffer.extend(audio_np.tolist())

        should_process = False

        if self.chunk_start_time and (current_time - self.chunk_start_time) >= self.max_chunk_duration:
            if len(self.buffer) >= 16000 * 2:
                should_process = True
                self.silence_start = None
        elif not is_speech:
            if self.silence_start is None:
                self.silence_start = current_time
            elif (current_time - self.silence_start) >= self.silence_duration:
                if len(self.buffer) >= 16000 * 1:
                    should_process = True
                self.silence_start = None
        else:
            self.silence_start = None

        if should_process:
            callback(np.array(self.buffer))
            self.buffer = []
            self.chunk_start_time = current_time
            if self._use_webrtc:
                self._byte_buffer = bytearray()

        if len(self.buffer) >= 16000 * 10:
            callback(np.array(self.buffer))
            self.buffer = []
            self.chunk_start_time = current_time
            if self._use_webrtc:
                self._byte_buffer = bytearray()

        if self.chunk_start_time and (current_time - self.chunk_start_time) >= 3.0:
            if len(self.buffer) >= 16000 * 1:
                callback(np.array(self.buffer))
                self.buffer = []
                self.chunk_start_time = current_time
                self.silence_start = None
                if self._use_webrtc:
                    self._byte_buffer = bytearray()
