import customtkinter as ctk
from ui.theme import COLORS


class BatchView(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_batch_start = None

        ctk.CTkLabel(
            self, text="批量音檔轉字幕",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLORS["text_light"]
        ).pack(anchor="w", pady=(0, 20))

        dropzone = ctk.CTkFrame(
            self, height=200, fg_color=COLORS["bg_panel"],
            border_width=2, border_color="#334155"
        )
        dropzone.pack(fill="x", pady=10)
        dropzone.pack_propagate(False)
        ctk.CTkLabel(
            dropzone, text="☁️\n點擊此處瀏覽檔案\n(支援 MP3, WAV, MP4)",
            font=ctk.CTkFont(size=16), text_color=COLORS["text_muted"], justify="center"
        ).pack(expand=True)

        dropzone.bind("<Button-1>", lambda e: self._handle_batch())
        for child in dropzone.winfo_children():
            child.bind("<Button-1>", lambda e: self._handle_batch())

        settings_panel = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=15)
        settings_panel.pack(fill="x", pady=20, ipady=10)
        ctk.CTkCheckBox(
            settings_panel, text="產生雙語 SRT 字幕檔",
            text_color=COLORS["text_light"]
        ).pack(anchor="w", padx=20, pady=15)

        ctk.CTkButton(
            self, text="▶ 選擇檔案並轉換", height=45,
            fg_color=COLORS["primary"],
            command=self._handle_batch
        ).pack(anchor="e", pady=20)

    def _handle_batch(self):
        if self.on_batch_start:
            self.on_batch_start()