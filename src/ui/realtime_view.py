import customtkinter as ctk
from ui.theme import COLORS
from ui.components import AudioLevelMeter, SourceCard, AppItem, LangButton


class RealtimeView(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.on_refresh_devices = None
        self.on_source_change = None
        self.on_record_click = None
        self.on_export_click = None
        self.on_lang_change = None
        self.on_get_apps = None

        self.current_source = "mic"
        self.src_lang = "auto"
        self.tgt_lang = "zh"

        self._build_top_bar()
        self._build_chat_area()
        self._build_bottom_bar()

    def _build_top_bar(self):
        top = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=14)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 12), padx=4)

        top.columnconfigure(0, weight=0)
        top.columnconfigure(1, weight=1)
        top.columnconfigure(2, weight=0)

        left = ctk.CTkFrame(top, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nw", padx=(16, 12), pady=14)

        ctk.CTkLabel(left, text="音訊來源", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 8))

        cards = ctk.CTkFrame(left, fg_color="transparent")
        cards.pack(anchor="w")

        self.mic_card = SourceCard(cards, "🎤", "麥克風", "mic", self._on_source_select)
        self.mic_card.pack(side="left", padx=(0, 8))
        self.mic_card.select()

        self.sys_card = SourceCard(cards, "🔊", "系統", "system", self._on_source_select)
        self.sys_card.pack(side="left", padx=8)

        self.app_card = SourceCard(cards, "🖥️", "App", "per-app", self._on_source_select)
        self.app_card.pack(side="left", padx=8)

        self.app_list = ctk.CTkScrollableFrame(left, fg_color=COLORS["bg_input"], height=90, corner_radius=10)
        self.app_list.pack(anchor="w", pady=(12, 0), fill="x")

        center = ctk.CTkFrame(top, fg_color="transparent")
        center.grid(row=0, column=1, sticky="n", padx=12, pady=14)

        ctk.CTkLabel(center, text="語言設定", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(0, 8))

        src_row = ctk.CTkFrame(center, fg_color="transparent")
        src_row.pack(anchor="w", pady=(0, 6))

        ctk.CTkLabel(src_row, text="來源", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_dim"], width=36).pack(side="left")

        self.src_btns = {}
        for label, code in [("自動", "auto"), ("日", "ja"), ("英", "en"), ("中", "zh")]:
            btn = LangButton(src_row, label, code, self._on_src_lang)
            btn.pack(side="left", padx=3)
            self.src_btns[code] = btn
        self.src_btns["auto"].select()

        tgt_row = ctk.CTkFrame(center, fg_color="transparent")
        tgt_row.pack(anchor="w")

        ctk.CTkLabel(tgt_row, text="目標", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_dim"], width=36).pack(side="left")

        self.tgt_btns = {}
        for label, code in [("中", "zh"), ("英", "en"), ("日", "ja"), ("韓", "ko")]:
            btn = LangButton(tgt_row, label, code, self._on_tgt_lang)
            btn.pack(side="left", padx=3)
            self.tgt_btns[code] = btn
        self.tgt_btns["zh"].select()

        right = ctk.CTkFrame(top, fg_color="transparent")
        right.grid(row=0, column=2, sticky="ne", padx=(12, 16), pady=14)

        self.status_dot = ctk.CTkLabel(right, text="●", font=ctk.CTkFont(size=14), text_color=COLORS["success"])
        self.status_dot.pack(side="left")

        self.status_label = ctk.CTkLabel(right, text="就緒", font=ctk.CTkFont(size=13),
                                          text_color=COLORS["text_muted"])
        self.status_label.pack(side="left", padx=8)

    def _build_chat_area(self):
        self.chat_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.chat_scroll.grid(row=1, column=0, sticky="nsew", padx=4)

    def _build_bottom_bar(self):
        bottom = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=14, height=80)
        bottom.grid(row=2, column=0, sticky="ew", pady=(12, 0), padx=4)
        bottom.grid_propagate(False)

        self.record_btn = ctk.CTkButton(
            bottom, text="🎤", width=56, height=56, corner_radius=28,
            font=ctk.CTkFont(size=24), fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            command=self._handle_record, state="disabled"
        )
        self.record_btn.pack(side="left", padx=16, pady=12)

        info = ctk.CTkFrame(bottom, fg_color="transparent")
        info.pack(side="left", padx=8)

        self.record_label = ctk.CTkLabel(info, text="準備就緒", font=ctk.CTkFont(size=13),
                                          text_color=COLORS["text_muted"])
        self.record_label.pack(anchor="w")

        self.level_meter = AudioLevelMeter(info)
        self.level_meter.pack(anchor="w", pady=(8, 0))

        ctk.CTkButton(
            bottom, text="匯出 SRT", width=100, height=36,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            command=self._handle_export
        ).pack(side="right", padx=16)

    def _on_source_select(self, source):
        self.current_source = source
        self.mic_card.deselect()
        self.sys_card.deselect()
        self.app_card.deselect()

        if source == "mic":
            self.mic_card.select()
            self._hide_app_list()
        elif source == "system":
            self.sys_card.select()
            self._hide_app_list()
        else:
            self.app_card.select()
            self._load_apps()

        if self.on_source_change:
            self.on_source_change(source, "")

    def _on_src_lang(self, code):
        self.src_lang = code
        for c, btn in self.src_btns.items():
            btn.select() if c == code else btn.deselect()
        self._notify_lang()

    def _on_tgt_lang(self, code):
        self.tgt_lang = code
        for c, btn in self.tgt_btns.items():
            btn.select() if c == code else btn.deselect()
        self._notify_lang()

    def _notify_lang(self):
        if self.on_lang_change:
            self.on_lang_change(self.src_lang, self.tgt_lang)

    def _load_apps(self):
        for w in self.app_list.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.app_list, text="掃描中...", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_muted"]).pack(pady=12)

        if self.on_get_apps:
            apps = self.on_get_apps()
            self.after(100, lambda: self._show_apps(apps))

    def _show_apps(self, apps):
        for w in self.app_list.winfo_children():
            w.destroy()

        if not apps:
            ctk.CTkLabel(self.app_list, text="沒有播放中的程式", font=ctk.CTkFont(size=12),
                         text_color=COLORS["text_muted"]).pack(pady=12)
            return

        for name, pid in apps[:5]:
            item = AppItem(self.app_list, name, self._on_app_select)
            item.pack(fill="x", pady=3)

    def _on_app_select(self, name):
        if self.on_source_change:
            self.on_source_change("per-app", name)

    def _hide_app_list(self):
        for w in self.app_list.winfo_children():
            w.destroy()

    def _handle_record(self):
        if self.on_record_click:
            self.on_record_click()

    def _handle_export(self):
        if self.on_export_click:
            self.on_export_click()

    def set_status(self, text, color=None):
        self.status_label.configure(text=text)
        if color:
            self.status_dot.configure(text_color=color)

    def enable_record_button(self, enabled):
        self.record_btn.configure(state="normal" if enabled else "disabled")

    def update_record_state(self, is_recording):
        if is_recording:
            self.record_btn.configure(text="■", fg_color="#334155")
            self.record_label.configure(text="錄音中", text_color=COLORS["success"])
        else:
            self.record_btn.configure(text="🎤", fg_color=COLORS["danger"])
            self.record_label.configure(text="已停止", text_color=COLORS["text_muted"])
            self.level_meter.reset()

    def update_audio_level(self, level):
        self.level_meter.set_level(level)

    def get_current_source(self):
        return self.current_source
