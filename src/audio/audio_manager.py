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

    def set_vad_params(self, rms_threshold=150.0, silence_duration=1.5, max_duration=8.0):
        self.vad = SimpleVAD(rms_threshold, silence_duration, max_duration)
        logger.info(f"VAD params: RMS={rms_threshold}, silence={silence_duration}s, max={max_duration}s")

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
            wasapi_output = self.p.get_default_wasapi_device_info_by_index(role='eMultimedia')
            loopback = self.p.get_loopback_device_info_by_index(wasapi_output['index'])
            logger.info(f"Loopback device: {loopback['name']} [index={loopback['index']}]")
            logger.debug(f"Loopback details: channels={loopback['maxInputChannels']}, rate={loopback['defaultSampleRate']}")
            return loopback
        except Exception as e:
            logger.error(f"Failed to find loopback device: {e}", exc_info=True)
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
            logger.info("Mic stream opened: 16kHz, Mono")

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

        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=loopback_channels,
                rate=loopback_rate,
                input=True,
                input_device_index=loopback_index,
                frames_per_buffer=1024
            )
            logger.info(f"System loopback stream opened: {loopback_rate}Hz, {loopback_channels}ch, device={loopback_index}")

            from librosa import resample as librosa_resample
            target_rate = 16000

            while self.is_recording:
                data = self.stream.read(1024, exception_on_overflow=False)
                audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                if loopback_channels > 1:
                    audio_np = np.mean(audio_np.reshape(-1, loopback_channels), axis=1)

                if loopback_rate != target_rate and len(audio_np) > 0:
                    audio_np = librosa_resample(audio_np, orig_sr=loopback_rate, target_sr=target_rate)

                rms = np.sqrt(np.mean(audio_np ** 2)) * 1000
                logger.debug(f"System chunk: RMS={rms:.1f}, samples={len(audio_np)}, rate={loopback_rate}->{target_rate}")
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
        if self.on_audio_level and len(audio_np) > 0:
            rms = np.sqrt(np.mean(audio_np ** 2))
            level = min(1.0, rms * 10)
            self.on_audio_level(level)

    def _close_stream(self):
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

                if self.p is not None:
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

    def cleanup(self):
        logger.info("Cleaning audio resources...")
        self.is_recording = False
        self._close_stream()
        logger.info("Audio resources cleaned")