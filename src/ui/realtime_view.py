import customtkinter as ctk
from ui.theme import COLORS, SRC_LANGS, TGT_LANGS, AUDIO_SOURCE_DISPLAY


class RealtimeView(ctk.CTkFrame):

    def __init__(self, master, device_var, src_lang_var, tgt_lang_var, audio_source_var, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.device_var = device_var
        self.src_lang_var = src_lang_var
        self.tgt_lang_var = tgt_lang_var
        self.audio_source_var = audio_source_var

        self.on_refresh_devices = None
        self.on_source_change = None
        self.on_record_click = None
        self.on_export_click = None

        self._build_header()
        self._build_chat_area()
        self._build_bottom_bar()

    def _build_header(self):
        header = ctk.CTkFrame(self, height=60, fg_color=COLORS["bg_panel"], corner_radius=15)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        device_frame = ctk.CTkFrame(header, fg_color="transparent")
        device_frame.pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(device_frame, text="🎤 音訊:", text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 5))
        self.device_combo = ctk.CTkComboBox(
            device_frame, variable=self.device_var, values=["載入中..."],
            width=280, fg_color="#0f172a", border_color="#334155"
        )
        self.device_combo.pack(side="left", padx=5)

        self.source_combo = ctk.CTkComboBox(
            device_frame, variable=self.audio_source_var,
            values=AUDIO_SOURCE_DISPLAY,
            width=120, fg_color="#0f172a", border_color="#334155",
            command=self._handle_source_change
        )
        self.source_combo.pack(side="left", padx=5)

        ctk.CTkButton(
            device_frame, text="🔄", width=35,
            fg_color=COLORS["primary_muted"], hover_color=COLORS["primary"],
            command=self._handle_refresh
        ).pack(side="left", padx=5)

        lang_frame = ctk.CTkFrame(header, fg_color="transparent")
        lang_frame.pack(side="right", padx=15, pady=10)

        self.src_lang_combo = ctk.CTkComboBox(
            lang_frame, values=list(SRC_LANGS.keys()), width=130,
            fg_color="#0f172a", border_color="#334155",
            command=lambda choice: self.src_lang_var.set(SRC_LANGS[choice])
        )
        self.src_lang_combo.set("自動偵測 (Auto)")
        self.src_lang_combo.pack(side="left", padx=5)

        ctk.CTkLabel(lang_frame, text="➔", text_color=COLORS["text_muted"]).pack(side="left", padx=2)

        self.tgt_lang_combo = ctk.CTkComboBox(
            lang_frame, values=list(TGT_LANGS.keys()), width=130,
            fg_color="#0f172a", border_color="#334155",
            command=lambda choice: self.tgt_lang_var.set(TGT_LANGS[choice])
        )
        self.tgt_lang_combo.set("繁體中文 (ZH)")
        self.tgt_lang_combo.pack(side="left", padx=5)

    def _build_chat_area(self):
        self.chat_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.chat_scroll.grid(row=1, column=0, sticky="nsew")

    def _build_bottom_bar(self):
        bottom_bar = ctk.CTkFrame(self, height=80, fg_color=COLORS["bg_panel"], corner_radius=20)
        bottom_bar.grid(row=2, column=0, sticky="ew", pady=(15, 0))

        self.record_btn = ctk.CTkButton(
            bottom_bar, text="🎤", width=60, height=60, corner_radius=30,
            font=ctk.CTkFont(size=24), fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            command=self._handle_record, state="disabled"
        )
        self.record_btn.pack(side="left", padx=20, pady=10)

        self.record_status_label = ctk.CTkLabel(
            bottom_bar, text="準備就緒 (READY)",
            font=ctk.CTkFont(family="Courier", size=14),
            text_color=COLORS["text_muted"]
        )
        self.record_status_label.pack(side="left", padx=10)

        ctk.CTkButton(
            bottom_bar, text="匯出 SRT", fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"], width=100,
            command=self._handle_export
        ).pack(side="right", padx=20)

    def _handle_refresh(self):
        if self.on_refresh_devices:
            self.on_refresh_devices()

    def _handle_source_change(self, choice):
        if self.on_source_change:
            self.on_source_change(choice)

    def _handle_record(self):
        if self.on_record_click:
            self.on_record_click()

    def _handle_export(self):
        if self.on_export_click:
            self.on_export_click()

    def set_device_list(self, devices, default_index=0):
        if devices:
            self.device_combo.configure(values=devices)
            self.device_var.set(devices[default_index])
        else:
            self.device_combo.configure(values=["無可用音訊裝置"])
            self.device_var.set("無可用音訊裝置")

    def set_device_loading(self, text="搜尋裝置中..."):
        self.device_combo.configure(values=[text])
        self.device_var.set(text)

    def enable_record_button(self, enabled):
        self.record_btn.configure(state="normal" if enabled else "disabled")

    def update_record_state(self, is_recording):
        if is_recording:
            self.record_btn.configure(text="■", fg_color=COLORS["bg_panel"], hover_color="#334155")
            self.record_status_label.configure(text="LISTENING...", text_color=COLORS["success"])
        else:
            self.record_btn.configure(text="🎤", fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
            self.record_status_label.configure(text="PAUSED", text_color=COLORS["text_muted"])