import customtkinter as ctk
from ui.theme import COLORS, FONT


class BatchView(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.on_batch_start = None

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text="批量音檔轉字幕",
            font=ctk.CTkFont(family=FONT["title"][0], size=22, weight="bold"),
            text_color=COLORS["text_light"]
        ).grid(row=0, column=0, sticky="w", pady=(0, 20))

        dropzone = ctk.CTkFrame(
            self, height=220, fg_color=COLORS["bg_panel"],
            corner_radius=14, border_width=2, border_color=COLORS["border"]
        )
        dropzone.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        dropzone.grid_propagate(False)

        inner = ctk.CTkFrame(dropzone, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text="☁️", font=ctk.CTkFont(family="Segoe UI Emoji", size=40)).pack(pady=(0, 8))
        ctk.CTkLabel(inner, text="點擊此處瀏覽檔案", font=ctk.CTkFont(family=FONT["heading"][0], size=16),
                     text_color=COLORS["text_light"]).pack()
        ctk.CTkLabel(inner, text="支援 MP3, WAV, MP4, M4A, AAC, FLAC",
                     font=ctk.CTkFont(family=FONT["body"][0], size=13), text_color=COLORS["text_muted"]).pack(pady=(4, 0))

        for widget in [dropzone] + dropzone.winfo_children() + inner.winfo_children():
            widget.bind("<Button-1>", lambda e: self._handle_batch())

        settings_panel = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"], corner_radius=14)
        settings_panel.grid(row=2, column=0, sticky="ew", pady=(0, 16))

        ctk.CTkCheckBox(
            settings_panel, text="產生雙語 SRT 字幕檔",
            text_color=COLORS["text_light"], font=ctk.CTkFont(family=FONT["body"][0], size=14),
            checkbox_width=22, checkbox_height=22
        ).pack(anchor="w", padx=20, pady=16)

        ctk.CTkButton(
            self, text="▶  選擇檔案並轉換", height=48, font=ctk.CTkFont(family=FONT["body"][0], size=15),
            fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
            corner_radius=12,
            command=self._handle_batch
        ).grid(row=3, column=0, sticky="e")

    def _handle_batch(self):
        if self.on_batch_start:
            self.on_batch_start()
