import customtkinter as ctk
import requests
import threading
from ui.theme import COLORS


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
        self.on_fetch_models = None
        self.show_info = None
        self.show_error = None

        self._build_content()

    def _build_content(self):
        ctk.CTkLabel(
            self, text="API 配置",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_light"]
        ).pack(anchor="w", pady=(0, 20))

        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=15)
        panel.pack(fill="x", pady=10, ipadx=20, ipady=20)

        self._build_asr_section(panel)
        self._build_translate_section(panel)
        self._build_vad_section(panel)

        ctk.CTkButton(
            self, text="🔄 從 LM Studio 取得模型列表", height=35,
            fg_color=COLORS["primary_muted"],
            command=self._handle_fetch_models
        ).pack(anchor="e", pady=10)

        ctk.CTkButton(
            self, text="💾 儲存並套用設定", height=45,
            fg_color=COLORS["primary"],
            command=self._handle_save
        ).pack(anchor="e", pady=20)

    def _build_asr_section(self, panel):
        ctk.CTkLabel(panel, text="ASR 語音辨識", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(10, 5))
        self._build_entry_row(panel, "模型 ID:", self.asr_model_var)
        self._build_entry_row(panel, "API URL:", self.asr_url_var)
        self._build_entry_row(panel, "API Key:", self.asr_key_var)

    def _build_translate_section(self, panel):
        ctk.CTkLabel(panel, text="翻譯模型", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 5))
        self._build_entry_row(panel, "模型 ID:", self.translate_model_var)
        self._build_entry_row(panel, "API URL:", self.translate_url_var)
        self._build_entry_row(panel, "API Key:", self.translate_key_var)

    def _build_vad_section(self, panel):
        ctk.CTkLabel(panel, text="VAD 靜音切割 (秒)", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(15, 5))
        slider_frame = ctk.CTkFrame(panel, fg_color="transparent")
        slider_frame.pack(anchor="w", fill="x", padx=20, pady=(0, 15))

        vad_slider = ctk.CTkSlider(
            slider_frame, variable=self.vad_duration_var,
            from_=0.5, to=3.0, number_of_steps=25, width=350
        )
        vad_slider.pack(side="left", padx=(0, 15))

        vad_value_label = ctk.CTkLabel(slider_frame, text="1.5s", font=ctk.CTkFont(family="Courier"))
        vad_value_label.pack(side="left")
        vad_slider.configure(command=lambda val: vad_value_label.configure(text=f"{val:.1f}s"))

    def _build_entry_row(self, panel, label_text, variable):
        row = ctk.CTkFrame(panel, fg_color="transparent")
        row.pack(anchor="w", fill="x", padx=20, pady=3)
        ctk.CTkLabel(row, text=label_text, width=60).pack(side="left")
        ctk.CTkEntry(row, variable=variable, width=250, fg_color="#0f172a").pack(side="left", padx=5)

    def _handle_save(self):
        if self.on_save_settings:
            self.on_save_settings()

    def _handle_fetch_models(self):
        if self.on_fetch_models:
            self.on_fetch_models()
        else:
            self._default_fetch_models()

    def _default_fetch_models(self):
        def fetch():
            try:
                url = self.asr_url_var.get()
                response = requests.get(f"{url}/models", timeout=5)
                if response.status_code == 200:
                    models = response.json().get("data", [])
                    model_ids = [m.get("id", "") for m in models]
                    self.after(0, lambda: self.show_info("Available Models", "\n".join(model_ids)))
                else:
                    self.after(0, lambda: self.show_error("Error", f"API: {response.status_code}"))
            except Exception as e:
                self.after(0, lambda: self.show_error("Error", f"Cannot connect: {e}"))
        threading.Thread(target=fetch, daemon=True).start()