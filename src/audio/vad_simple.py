import time
import numpy as np
from typing import Optional, List, Callable


class SimpleVAD:

    def __init__(self, rms_threshold=150.0, silence_duration=1.5, max_chunk_duration=8.0):
        self.rms_threshold = rms_threshold
        self.silence_duration = silence_duration
        self.max_chunk_duration = max_chunk_duration

        self.buffer: List[float] = []
        self.silence_start: Optional[float] = None
        self.chunk_start_time: Optional[float] = None

    def reset(self):
        self.buffer = []
        self.silence_start = None
        self.chunk_start_time = None

    def process_chunk(self, audio_np: np.ndarray, callback: Callable[[np.ndarray], None]):
        rms = np.sqrt(np.mean(audio_np ** 2)) * 1000
        current_time = time.time()

        self.buffer.extend(audio_np.tolist())

        should_process = False

        if self.chunk_start_time and (current_time - self.chunk_start_time) >= self.max_chunk_duration:
            if len(self.buffer) >= 16000 * 2:
                should_process = True
                self.silence_start = None

        elif rms < self.rms_threshold:
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

        if len(self.buffer) >= 16000 * 10:
            callback(np.array(self.buffer))
            self.buffer = []
            self.chunk_start_time = current_time

        if self.chunk_start_time and (current_time - self.chunk_start_time) >= 3.0:
            if len(self.buffer) >= 16000 * 1:
                callback(np.array(self.buffer))
                self.buffer = []
                self.chunk_start_time = current_time
                self.silence_start = None