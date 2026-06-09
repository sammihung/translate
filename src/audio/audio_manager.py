import pyaudio
import numpy as np
import time
from typing import List, Optional, Callable
import threading
from core.logging_config import get_logger
from audio.vad_simple import SimpleVAD

logger = get_logger(__name__)


class AudioManager:

    def __init__(self):
        self.p: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording: bool = False
        self._stream_lock = threading.Lock()
        self._has_pyaudiowpatch: bool = False

        self.audio_source: str = "mic"
        self.target_app: str = ""

        self.vad = SimpleVAD()
        self.on_audio_level: Optional[Callable[[float], None]] = None
        self._last_level_time: float = 0
        self._level_interval: float = 0.05

    def set_vad_params(self, silence_duration=0.8, speech_duration=2.0, max_duration=4.0):
        self.vad = SimpleVAD(silence_duration=silence_duration, speech_duration=speech_duration, max_chunk_duration=max_duration)
        logger.info(f"VAD params: silence={silence_duration}s, speech={speech_duration}s, max={max_duration}s")

    def set_audio_source(self, source, target_app=""):
        self.audio_source = source
        self.target_app = target_app
        logger.info(f"Audio source set to: {source}, target_app={target_app}")

    def _init_pyaudio(self):
        if self.p is not None:
            return
        try:
            import pyaudiowpatch
            self.p = pyaudiowpatch.PyAudio()
            self._has_pyaudiowpatch = True
            logger.info("Using pyaudiowpatch (WASAPI loopback supported)")
        except ImportError:
            self.p = pyaudio.PyAudio()
            self._has_pyaudiowpatch = False
            logger.info("Using pyaudio (mic only, no system audio)")

    def _find_loopback_device(self) -> Optional[dict]:
        if not self._has_pyaudiowpatch:
            logger.error("pyaudiowpatch not available - cannot capture system audio")
            return None

        try:
            loopback = self.p.get_default_wasapi_loopback()
            logger.info(f"Loopback device: {loopback['name']} [index={loopback['index']}]")
            logger.debug(f"Loopback details: channels={loopback['maxInputChannels']}, rate={loopback['defaultSampleRate']}")
            return loopback
        except Exception as e:
            logger.error(f"Failed to find loopback device: {e}", exc_info=True)
            try:
                for dev in self.p.get_loopback_device_info_generator():
                    logger.info(f"Found loopback device: {dev['name']} [index={dev['index']}]")
                    return dev
            except Exception as e2:
                logger.error(f"Fallback loopback search also failed: {e2}")
            return None

    def get_audio_devices(self) -> List[str]:
        if self.audio_source == "mic":
            return self._get_mic_devices()
        elif self.audio_source == "system":
            return self._get_system_devices()
        elif self.audio_source == "per-app":
            return self._get_app_devices()
        return []

    def _get_mic_devices(self) -> List[str]:
        device_list: List[str] = []
        try:
            self._init_pyaudio()
            for i in range(self.p.get_device_count()):
                try:
                    info = self.p.get_device_info_by_index(i)
                    name = info.get('name', '')
                    if info.get('maxInputChannels', 0) > 0 and name:
                        device_list.append(f"{name} [{i}]")
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Get mic devices failed: {e}")
        return device_list

    def _get_system_devices(self) -> List[str]:
        return ["系統音訊 (System Audio) [loopback]"]

    def _get_app_devices(self) -> List[str]:
        apps = self._enumerate_audio_sessions()
        if not apps:
            return ["無可用應用程式"]
        return [f"{name} [{pid}]" for name, pid in apps]

    def _enumerate_audio_sessions(self):
        try:
            from pycaw.pycaw import AudioUtilities

            sessions = AudioUtilities.GetAllSessions()
            apps = []
            for session in sessions:
                if session.Process:
                    name = session.Process.name()
                    pid = session.ProcessId
                    if name and name not in ["audiodg.exe", "svchost.exe", "System"]:
                        apps.append((name, pid))

            seen = set()
            unique_apps = []
            for name, pid in apps:
                if name not in seen:
                    seen.add(name)
                    unique_apps.append((name, pid))

            return unique_apps
        except Exception as e:
            logger.error(f"Enumerate audio sessions failed: {e}")
            return []

    def parse_device_index(self, device_name: str) -> Optional[int]:
        try:
            match = __import__('re').search(r'\[(\d+)\]', device_name)
            if match:
                return int(match.group(1))
            return None
        except Exception:
            return None

    def start_recording(self, device_index, callback):
        if self.audio_source == "mic":
            self._start_mic_recording(device_index, callback)
        elif self.audio_source == "system":
            self._start_system_recording(callback)
        elif self.audio_source == "per-app":
            self._start_app_recording(callback)

    def _start_mic_recording(self, device_index, callback):
        self._init_pyaudio()
        self.is_recording = True
        self.vad.reset()

        try:
            self.stream = self.p.open(
                format=pyaudio.paFloat32, channels=1, rate=16000,
                input=True, input_device_index=device_index,
                frames_per_buffer=1024
            )
            dev_info = self.p.get_device_info_by_index(device_index) if device_index is not None else self.p.get_default_input_device_info()
            logger.info(f"Mic stream opened: 16kHz, Mono, device=[{device_index}] {dev_info.get('name', 'unknown')}, maxInputChannels={dev_info.get('maxInputChannels', '?')}")

            while self.is_recording:
                data = self.stream.read(1024, exception_on_overflow=False)
                audio_np = np.frombuffer(data, dtype=np.float32)
                rms = np.sqrt(np.mean(audio_np ** 2)) * 1000
                logger.debug(f"Mic chunk: RMS={rms:.1f}, samples={len(audio_np)}")
                self._update_level(audio_np)
                self.vad.process_chunk(audio_np, callback)

        except Exception as e:
            logger.error(f"Mic recording failed: {e}", exc_info=True)
        finally:
            self._close_stream()

    def _start_system_recording(self, callback):
        self._init_pyaudio()
        self.is_recording = True
        self.vad.reset()

        loopback = self._find_loopback_device()
        if not loopback:
            logger.error("Cannot start system recording - no loopback device found")
            self.is_recording = False
            return

        loopback_rate = int(loopback['defaultSampleRate'])
        loopback_channels = int(loopback['maxInputChannels'])
        loopback_index = loopback['index']

        open_attempts = [
            {"rate": loopback_rate, "channels": loopback_channels, "frames": 4096},
            {"rate": loopback_rate, "channels": loopback_channels, "frames": 2048},
            {"rate": loopback_rate, "channels": 1, "frames": 4096},
            {"rate": 48000, "channels": 2, "frames": 4096},
            {"rate": 44100, "channels": 2, "frames": 4096},
        ]

        def _open_loopback_stream(rate, channels, frames):
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=loopback_index,
                frames_per_buffer=frames,
                start=False,
            )
            self.stream.start_stream()
            logger.info(
                f"System loopback stream opened+started: {rate}Hz, {channels}ch, "
                f"frames={frames}, device={loopback_index}, "
                f"is_active={self.stream.is_active()}"
            )

        def _close_only():
            try:
                if self.stream is not None:
                    self.stream.close()
            except Exception:
                pass
            self.stream = None

        try:
            last_err: Optional[Exception] = None
            stream_opened = False
            for attempt in open_attempts:
                try:
                    _open_loopback_stream(attempt["rate"], attempt["channels"], attempt["frames"])
                    loopback_rate = attempt["rate"]
                    loopback_channels = attempt["channels"]
                    stream_opened = True
                    break
                except Exception as e:
                    last_err = e
                    logger.warning(
                        f"Loopback open attempt failed "
                        f"({attempt['rate']}Hz/{attempt['channels']}ch/{attempt['frames']}f): {e}"
                    )
                    _close_only()

            if not stream_opened:
                raise last_err if last_err else RuntimeError("Failed to open loopback stream")

            from librosa import resample as librosa_resample
            target_rate = 16000

            consecutive_failures = 0
            warmup_chunks_left = 3
            while self.is_recording:
                try:
                    data = self.stream.read(loopback_rate // 100, exception_on_overflow=False)
                    if consecutive_failures:
                        logger.info(f"Loopback stream recovered after {consecutive_failures} failures")
                    consecutive_failures = 0
                except OSError as e:
                    errno = getattr(e, 'errno', None)
                    if errno in (-9999, -9988, -9983) and self.is_recording:
                        consecutive_failures += 1
                        logger.warning(
                            f"WASAPI loopback read error (errno={errno}), "
                            f"failure {consecutive_failures}/10, will reopen stream..."
                        )
                        _close_only()
                        if consecutive_failures > 10:
                            logger.error("Loopback failed too many times, giving up")
                            raise
                        time.sleep(0.3)
                        opened = False
                        for attempt in open_attempts:
                            try:
                                _open_loopback_stream(attempt["rate"], attempt["channels"], attempt["frames"])
                                loopback_rate = attempt["rate"]
                                loopback_channels = attempt["channels"]
                                opened = True
                                break
                            except Exception as e2:
                                logger.warning(f"Reopen attempt failed: {e2}")
                                _close_only()
                        if not opened:
                            logger.error("Could not reopen loopback stream, giving up")
                            raise
                        warmup_chunks_left = 3
                        continue
                    raise

                if warmup_chunks_left > 0:
                    warmup_chunks_left -= 1
                    continue

                audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                if loopback_channels > 1:
                    audio_np = np.mean(audio_np.reshape(-1, loopback_channels), axis=1)

                if loopback_rate != target_rate and len(audio_np) > 0:
                    audio_np = librosa_resample(audio_np, orig_sr=loopback_rate, target_sr=target_rate)

                self._update_level(audio_np)
                self.vad.process_chunk(audio_np, callback)

        except Exception as e:
            logger.error(f"System recording failed: {e}", exc_info=True)
        finally:
            self._close_stream()

    def _start_app_recording(self, callback):
        if not self.target_app:
            logger.error("No target app specified for per-app recording")
            return

        logger.info(f"Starting per-app recording for: {self.target_app} (using system loopback)")
        self._start_system_recording(callback)

    def _update_level(self, audio_np):
        if len(audio_np) > 0:
            import time as time_module
            now = time_module.time()
            if now - self._last_level_time < self._level_interval:
                return
            self._last_level_time = now
            
            rms = float(np.sqrt(np.mean(audio_np ** 2)))
            peak = float(np.max(np.abs(audio_np)))
            db = float(20 * np.log10(rms + 1e-10))
            level = float(min(1.0, max(0.0, (db + 80) / 80)))
            logger.debug(f"[AUDIO_LEVEL] RMS={rms:.6f}, peak={peak:.6f}, dB={db:.1f}, level={level:.3f}")
            if self.on_audio_level:
                self.on_audio_level(level)

    def _close_stream(self, terminate_pyaudio=False):
        try:
            with self._stream_lock:
                if self.stream is not None:
                    try:
                        if self.stream.is_active():
                            self.stream.stop_stream()
                        self.stream.close()
                    except Exception:
                        pass
                    finally:
                        self.stream = None

                if terminate_pyaudio and self.p is not None:
                    try:
                        self.p.terminate()
                    except Exception:
                        pass
                    finally:
                        self.p = None
                        self._has_pyaudiowpatch = False
        except Exception as e:
            logger.error(f"Close stream failed: {e}", exc_info=True)

    def stop_recording(self):
        logger.info("Stopping recording...")
        self.is_recording = False
        time.sleep(0.3)
        self._close_stream(terminate_pyaudio=False)

    def cleanup(self):
        logger.info("Cleaning audio resources...")
        self.is_recording = False
        self._close_stream(terminate_pyaudio=True)
        logger.info("Audio resources cleaned")