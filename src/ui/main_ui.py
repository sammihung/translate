import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Callable
from functools import wraps
from core.logging_config import get_logger
from config.settings import config
from ui.theme import COLORS, FONT_PRESETS, DEFAULT_FONT_PRESET_INDEX, AUDIO_SOURCE_MAP
from ui.sidebar import Sidebar
from ui.realtime_view import RealtimeView
from ui.batch_view import BatchView
from ui.settings_view import SettingsView
from ui.chat_bubble import ChatBubbleManager
from ui.floating_overlay import FloatingOverlay

logger = get_logger(__name__)


def run_in_main_thread(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        self.after(0, lambda: func(self, *args, **kwargs))
    return wrapper


class MainUI(ctk.CTkFrame):

    def __init__(self, master, controller=None, **kwargs):
        super().__init__(master, **kwargs)

        if controller:
            self.controller = controller
        elif hasattr(master, 'controller'):
            self.controller = master.controller
        else:
            self.controller = master

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.configure(fg_color=COLORS["bg_dark"])

        self.font_sizes = {
            "original": FONT_PRESETS[DEFAULT_FONT_PRESET_INDEX]["original"],
            "translated": FONT_PRESETS[DEFAULT_FONT_PRESET_INDEX]["translated"]
        }

        self.device_var = ctk.StringVar(value="請先重新整理裝置...")
        self.src_lang_var = ctk.StringVar(value="auto")
        self.tgt_lang_var = ctk.StringVar(value="zh")
        self.asr_model_var = ctk.StringVar(value=config.asr_model)
        self.asr_url_var = ctk.StringVar(value=config.asr_api_url)
        self.asr_key_var = ctk.StringVar(value=config.asr_api_key or "")
        self.translate_model_var = ctk.StringVar(value=config.translate_model)
        self.translate_url_var = ctk.StringVar(value=config.translate_api_url)
        self.translate_key_var = ctk.StringVar(value=config.translate_api_key or "")
        self.vad_duration_var = ctk.DoubleVar(value=1.5)
        self.audio_source_var = ctk.StringVar(value="mic")

        self.on_record_toggle: Optional[Callable] = None
        self.on_upload_file: Optional[Callable] = None
        self.on_save_subtitle: Optional[Callable] = None

        self.floating_mode = False

        self._build_layout()
        self.switch_view("realtime")

    def _build_layout(self):
        self.sidebar = Sidebar(
            self,
            on_nav_click=self.switch_view,
            on_floating_toggle=self.toggle_floating_mode,
            on_font_cycle=self.cycle_font_size
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.realtime_view = RealtimeView(
            self.main_container,
            device_var=self.device_var,
            src_lang_var=self.src_lang_var,
            tgt_lang_var=self.tgt_lang_var,
            audio_source_var=self.audio_source_var
        )
        self.realtime_view.on_refresh_devices = self._on_refresh_devices
        self.realtime_view.on_source_change = self._on_source_change
        self.realtime_view.on_record_click = self._on_record_click
        self.realtime_view.on_export_click = self._on_export_click

        self.batch_view = BatchView(self.main_container)
        self.batch_view.on_batch_start = self._on_batch_start

        self.settings_view = SettingsView(
            self.main_container,
            asr_model_var=self.asr_model_var,
            asr_url_var=self.asr_url_var,
            asr_key_var=self.asr_key_var,
            translate_model_var=self.translate_model_var,
            translate_url_var=self.translate_url_var,
            translate_key_var=self.translate_key_var,
            vad_duration_var=self.vad_duration_var
        )
        self.settings_view.on_save_settings = self._on_save_settings
        self.settings_view.on_fetch_models = self._on_fetch_models
        self.settings_view.show_info = self.show_info
        self.settings_view.show_error = self.show_error

        self.views = {
            "realtime": self.realtime_view,
            "batch": self.batch_view,
            "settings": self.settings_view
        }

        self.bubble_mgr = ChatBubbleManager(
            self.realtime_view.chat_scroll, self.font_sizes
        )
        self.floating_overlay = FloatingOverlay(self, self.font_sizes)

    def switch_view(self, view_id):
        for view in self.views.values():
            view.grid_forget()
        self.views[view_id].grid(row=0, column=0, sticky="nsew")
        self.sidebar.set_active_nav(view_id)

    # ==========================================
    # Public API
    # ==========================================

    def set_device_list(self, devices, default_index=0):
        self.realtime_view.set_device_list(devices, default_index)

    @run_in_main_thread
    def set_status(self, text, color=None):
        self.sidebar.set_status(text, color)

    @run_in_main_thread
    def enable_record_button(self, enabled):
        self.realtime_view.enable_record_button(enabled)

    def get_selected_device(self):
        return self.realtime_view.device_combo.get()

    def get_selected_languages(self):
        return self.src_lang_var.get(), self.tgt_lang_var.get()

    @run_in_main_thread
    def update_record_state(self, is_recording):
        self.realtime_view.update_record_state(is_recording)

    def add_chat_bubble(self, speaker_name, original, translated, speaker_id=1):
        import uuid
        bubble_id = str(uuid.uuid4())

        def _update():
            real_bubble_id = self.bubble_mgr.add_bubble(speaker_name, original, translated, speaker_id)
            if self.floating_mode:
                self.floating_overlay.add_bubble(
                    bubble_id, speaker_name, original, translated, speaker_id,
                    self.bubble_mgr.cleaned_bubble_ids
                )

        self.after(0, _update)
        return bubble_id

    def update_chat_bubble(self, bubble_id, new_translated):
        def _update():
            self.bubble_mgr.update_bubble(bubble_id, new_translated)
            if self.floating_mode:
                self.floating_overlay.update_bubble(
                    bubble_id, new_translated,
                    self.bubble_mgr.cleaned_bubble_ids
                )

        self.after(0, _update)

    def ask_open_audio_file(self):
        fp = filedialog.askopenfilename(
            title="選擇音訊/影片檔案",
            filetypes=[("媒體檔案", "*.mp3 *.wav *.mp4 *.m4a *.aac *.flac"), ("所有檔案", "*.*")]
        )
        return fp if fp else None

    def ask_save_file(self, default_name="subtitle"):
        fp = filedialog.asksaveasfilename(
            title="儲存字幕檔案", initialfile=f"{default_name}.srt",
            defaultextension=".srt",
            filetypes=[("SRT 字幕", "*.srt"), ("所有檔案", "*.*")]
        )
        return fp if fp else None

    def show_info(self, title, msg):
        messagebox.showinfo(title, msg)

    def show_error(self, title, msg):
        messagebox.showerror(title, msg)

    # ==========================================
    # Floating Overlay
    # ==========================================

    def toggle_floating_mode(self):
        if self.floating_mode:
            self._close_floating()
        else:
            self._open_floating()

    def _open_floating(self):
        success = self.floating_overlay.open(self.bubble_mgr.cleaned_bubble_ids)
        if success:
            self.floating_mode = True
            self.sidebar.set_floating_button_state(True)

    def _close_floating(self):
        main_window = self.master if hasattr(self, 'master') else None
        success = self.floating_overlay.close(main_window)
        if success:
            self.floating_mode = False
            self.sidebar.set_floating_button_state(False)
            self.bubble_mgr.clear_cleaned_ids()

    # ==========================================
    # Font Size
    # ==========================================

    def cycle_font_size(self):
        current_idx = DEFAULT_FONT_PRESET_INDEX
        for idx, preset in enumerate(FONT_PRESETS):
            if preset["original"] == self.font_sizes["original"] and preset["translated"] == self.font_sizes["translated"]:
                current_idx = idx
                break

        next_idx = (current_idx + 1) % len(FONT_PRESETS)
        next_preset = FONT_PRESETS[next_idx]
        self.font_sizes["original"] = next_preset["original"]
        self.font_sizes["translated"] = next_preset["translated"]

        self.sidebar.set_font_label(next_preset["label"])
        self.bubble_mgr.refresh_fonts()
        self.floating_overlay.refresh_fonts()

    # ==========================================
    # Button Handlers
    # ==========================================

    def _on_refresh_devices(self):
        import threading
        self.realtime_view.set_device_loading()

        def refresh_thread():
            if self.controller and hasattr(self.controller, 'get_audio_devices'):
                source = AUDIO_SOURCE_MAP.get(self.audio_source_var.get(), "mic")
                devices = self.controller.get_audio_devices(source)
                self.after(0, lambda: self.set_device_list(devices))

        threading.Thread(target=refresh_thread, daemon=True).start()

    def _on_source_change(self, choice):
        if "系統" in choice:
            source = "system"
        elif "App" in choice or "app" in choice:
            source = "per-app"
        else:
            source = "mic"

        if self.controller and hasattr(self.controller, 'set_audio_source'):
            self.controller.set_audio_source(source)
        self._on_refresh_devices()

    def _on_record_click(self):
        if self.on_record_toggle and callable(self.on_record_toggle):
            self.on_record_toggle()

    def _on_export_click(self):
        if self.on_save_subtitle and callable(self.on_save_subtitle):
            self.on_save_subtitle()

    def _on_batch_start(self):
        if self.on_upload_file and callable(self.on_upload_file):
            self.on_upload_file()

    def _on_save_settings(self):
        settings = {
            "asr_model": self.asr_model_var.get(),
            "asr_api_url": self.asr_url_var.get(),
            "asr_api_key": self.asr_key_var.get(),
            "translate_model": self.translate_model_var.get(),
            "translate_api_url": self.translate_url_var.get(),
            "translate_api_key": self.translate_key_var.get(),
            "vad_duration": self.vad_duration_var.get()
        }
        if self.controller and hasattr(self.controller, 'set_settings'):
            self.controller.set_settings(settings)
            self.show_info("OK", "Settings saved, reconnecting API...")
        else:
            self.show_error("Error", "Cannot connect to backend")

    def _on_fetch_models(self):
        self.settings_view._default_fetch_models()