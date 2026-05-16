import customtkinter as ctk
import numpy as np
from ui.theme import COLORS


class AudioLevelMeter(ctk.CTkFrame):

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.bars = []
        for i in range(16):
            bar = ctk.CTkFrame(self, width=8, height=24, fg_color="#1e293b", corner_radius=2)
            bar.pack(side="left", padx=2)
            self.bars.append(bar)

    def set_level(self, level):
        active = int(min(1.0, level) * 16)
        for i, bar in enumerate(self.bars):
            if i < active:
                if i < 6:
                    bar.configure(fg_color="#10b981")
                elif i < 11:
                    bar.configure(fg_color="#3b82f6")
                else:
                    bar.configure(fg_color="#ef4444")
            else:
                bar.configure(fg_color="#1e293b")

    def reset(self):
        for bar in self.bars:
            bar.configure(fg_color="#1e293b")


class SourceCard(ctk.CTkFrame):

    def __init__(self, master, icon, label, value, on_click=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_panel"], corner_radius=12, width=80, height=80, **kwargs)

        self.value = value
        self.on_click = on_click
        self.selected = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_propagate(False)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.grid(row=0, column=0)

        self.icon_label = ctk.CTkLabel(inner, text=icon, font=ctk.CTkFont(size=26))
        self.icon_label.grid(row=0, column=0, pady=(8, 4))

        self.text_label = ctk.CTkLabel(inner, text=label, font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"])
        self.text_label.grid(row=1, column=0, pady=(0, 8))

        for widget in [self, self.icon_label, self.text_label, inner]:
            widget.bind("<Button-1>", self._handle_click)

    def _handle_click(self, event):
        if self.on_click:
            self.on_click(self.value)

    def select(self):
        self.selected = True
        self.configure(fg_color=COLORS["primary_muted"], border_width=2, border_color=COLORS["primary"])
        self.text_label.configure(text_color=COLORS["text_light"])

    def deselect(self):
        self.selected = False
        self.configure(fg_color=COLORS["bg_panel"], border_width=0)
        self.text_label.configure(text_color=COLORS["text_muted"])


class AppItem(ctk.CTkFrame):

    def __init__(self, master, name, on_select=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_panel_light"], corner_radius=8, **kwargs)

        self.name = name
        self.on_select = on_select

        ctk.CTkLabel(self, text="🎵", font=ctk.CTkFont(size=14)).pack(side="left", padx=8, pady=6)
        ctk.CTkLabel(self, text=name, font=ctk.CTkFont(size=12), text_color=COLORS["text_light"]).pack(side="left", fill="x", expand=True)

        btn = ctk.CTkButton(self, text="選擇", width=50, height=28, font=ctk.CTkFont(size=11),
                           fg_color=COLORS["primary_muted"], hover_color=COLORS["primary"],
                           command=lambda: on_select(name) if on_select else None)
        btn.pack(side="right", padx=8, pady=6)


class LangButton(ctk.CTkButton):

    def __init__(self, master, text, value, on_click=None, **kwargs):
        super().__init__(master, text=text, width=52, height=32, font=ctk.CTkFont(size=12),
                        fg_color=COLORS["bg_panel"], hover_color=COLORS["primary_muted"],
                        text_color=COLORS["text_muted"], corner_radius=8, **kwargs)
        self.value = value
        self.on_click = on_click
        self.configure(command=lambda: on_click(value) if on_click else None)

    def select(self):
        self.configure(fg_color=COLORS["primary"], text_color=COLORS["text_light"])

    def deselect(self):
        self.configure(fg_color=COLORS["bg_panel"], text_color=COLORS["text_muted"])
