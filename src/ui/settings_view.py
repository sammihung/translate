import customtkinter as ctk
import requests
import threading
from ui.theme import COLORS, FONT


class SettingsView(ctk.CTkFrame):

    def __init__(self, master, asr_model_var, asr_url_var, asr_key_var,
                 translate_model_var, translate_url_var, translate_key_var,
                 vad_duration_var, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.asr_model_var = asr_model_var
        self.asr_url_var = asr_url_var
        self.asr_key_var = asr_key_var
        self.translate_model_var = translate_model_var
        self.translate_url_var = translate_url_var
        self.translate_key_var = translate_key_var
        self.vad_duration_var = vad_duration_var

        self.on_save_settings = None
        self.show_info = None
        self.show_error = None

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        row = 0

        ctk.CTkLabel(self, text="API 設定", font=ctk.CTkFont(family=FONT["title"][0], size=20, weight="bold"),
                    text_color=COLORS["text_light"]).grid(row=row, column=0, sticky="w", pady=(0, 16))
        row += 1

        asr_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=14)
        asr_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        asr_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self._build_api_section(asr_frame, "🎤  ASR 語音辨識", self.asr_url_var, self.asr_model_var, self.asr_key_var, "asr")

        trans_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=14)
        trans_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        trans_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self._build_api_section(trans_frame, "🌐  翻譯引擎", self.translate_url_var, self.translate_model_var, self.translate_key_var, "trans")

        vad_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=14)
        vad_frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        vad_frame.grid_columnconfigure(0, weight=1)
        row += 1

        self._build_vad_section(vad_frame)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=row, column=0, sticky="e", pady=(8, 0))

        ctk.CTkButton(btn_row, text="💾  儲存設定", height=40, font=ctk.CTkFont(family=FONT["body"][0], size=14),
                     fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                     command=self._handle_save).pack()

    def _build_api_section(self, parent, title, url_var, model_var, key_var, prefix):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(header, text=title, font=ctk.CTkFont(family=FONT["subheading"][0], size=15, weight="bold"),
                     text_color=COLORS["text_light"]).pack(side="left")

        status_dot = ctk.CTkLabel(header, text="●", font=ctk.CTkFont(family=FONT["small"][0], size=12),
                                   text_color=COLORS["text_dim"])
        status_dot.pack(side="right", padx=(8, 0))

        status_lbl = ctk.CTkLabel(header, text="未連接", font=ctk.CTkFont(family=FONT["small"][0], size=12),
                                   text_color=COLORS["text_dim"])
        status_lbl.pack(side="right")

        setattr(self, f"{prefix}_dot", status_dot)
        setattr(self, f"{prefix}_lbl", status_lbl)

        fields = [
            ("API URL", url_var, "http://localhost:1234/v1"),
            ("模型名稱", model_var, "模型名稱"),
            ("API Key", key_var, "可選"),
        ]

        for label, var, placeholder in fields:
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(row, text=label, width=80, font=ctk.CTkFont(family=FONT["body"][0], size=13),
                        text_color=COLORS["text_muted"]).pack(side="left")
            ctk.CTkEntry(row, textvariable=var, height=34, font=ctk.CTkFont(family=FONT["body"][0], size=13),
                        fg_color=COLORS["bg_input"], placeholder_text=placeholder,
                        corner_radius=8).pack(side="left", fill="x", expand=True, padx=(8, 0))

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(8, 14))

        ctk.CTkButton(btn_row, text="測試連接", width=90, height=32, font=ctk.CTkFont(family=FONT["small"][0], size=12),
                      fg_color=COLORS["primary_muted"], hover_color=COLORS["primary"],
                      command=lambda: self._test_connection(url_var, prefix)).pack(side="left")

    def _build_vad_section(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(header, text="🔇  VAD 靜音分割", font=ctk.CTkFont(family=FONT["subheading"][0], size=15, weight="bold"),
                     text_color=COLORS["text_light"]).pack(side="left")

        slider_row = ctk.CTkFrame(parent, fg_color="transparent")
        slider_row.pack(fill="x", padx=16, pady=(0, 14))

        self.vad_lbl = ctk.CTkLabel(slider_row, text="1.5s", font=ctk.CTkFont(family=FONT["body"][0], size=13), width=44)
        self.vad_lbl.pack(side="left")

        ctk.CTkSlider(slider_row, variable=self.vad_duration_var, from_=0.5, to=3.0,
                     width=260, button_length=20,
                     command=lambda v: self.vad_lbl.configure(text=f"{v:.1f}s")).pack(side="left", padx=12)

    def _test_connection(self, url_var, prefix):
        dot = getattr(self, f"{prefix}_dot")
        lbl = getattr(self, f"{prefix}_lbl")

        lbl.configure(text="測試中...")
        dot.configure(text_color=COLORS["warning"])

        def test():
            try:
                resp = requests.get(f"{url_var.get()}/models", timeout=5)
                if resp.status_code == 200:
                    self.after(0, lambda: [lbl.configure(text="已連接"), dot.configure(text_color=COLORS["success"])])
                else:
                    self.after(0, lambda: [lbl.configure(text=f"錯誤 {resp.status_code}"), dot.configure(text_color=COLORS["danger"])])
            except Exception:
                self.after(0, lambda: [lbl.configure(text="連接失敗"), dot.configure(text_color=COLORS["danger"])])

        threading.Thread(target=test, daemon=True).start()

    def _handle_save(self):
        if self.on_save_settings:
            self.on_save_settings()
            if self.show_info:
                self.show_info("完成", "設定已儲存")

    def set_asr_status(self, connected):
        if connected:
            self.asr_lbl.configure(text="已連接")
            self.asr_dot.configure(text_color=COLORS["success"])
        else:
            self.asr_lbl.configure(text="未連接")
            self.asr_dot.configure(text_color=COLORS["text_dim"])

    def set_translate_status(self, connected):
        if connected:
            self.trans_lbl.configure(text="已連接")
            self.trans_dot.configure(text_color=COLORS["success"])
        else:
            self.trans_lbl.configure(text="未連接")
            self.trans_dot.configure(text_color=COLORS["text_dim"])
