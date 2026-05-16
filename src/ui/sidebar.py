import customtkinter as ctk
from ui.theme import COLORS, SIDEBAR_EXPANDED_WIDTH, SIDEBAR_COLLAPSED_WIDTH, NAV_ITEMS, FONT


class Sidebar(ctk.CTkFrame):

    def __init__(self, master, on_nav_click=None, on_floating_toggle=None, on_font_cycle=None, **kwargs):
        super().__init__(master, width=SIDEBAR_EXPANDED_WIDTH, corner_radius=0, fg_color="#0f172a", **kwargs)
        self.grid_propagate(False)
        self.grid_rowconfigure(4, weight=1)

        self.on_nav_click = on_nav_click
        self.on_floating_toggle = on_floating_toggle
        self.on_font_cycle = on_font_cycle
        self.menu_expanded = True
        self.nav_buttons = {}
        self.nav_text_labels = {}

        self._build_header()
        self._build_nav()
        self._build_actions()
        self._build_status()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(20, 16))

        self.toggle_btn = ctk.CTkButton(
            header_frame, text="☰", width=44, height=44, corner_radius=10,
            fg_color="transparent", hover_color=COLORS["bg_panel"],
            command=self.toggle_menu, font=ctk.CTkFont(family=FONT["heading"][0], size=20)
        )
        self.toggle_btn.pack(side="left")

        self.logo_label = ctk.CTkLabel(
            header_frame, text="🌊 QwenASR", font=ctk.CTkFont(family=FONT["title"][0], size=20, weight="bold"),
            text_color=COLORS["primary"]
        )
        self.logo_label.pack(side="left", padx=12)

    def _build_nav(self):
        for idx, (view_id, icon, text) in enumerate(NAV_ITEMS, start=1):
            btn = ctk.CTkButton(
                self, text=f"{icon}  {text}", font=ctk.CTkFont(family=FONT["body"][0], size=15),
                fg_color="transparent", text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_panel"], anchor="w", height=48,
                corner_radius=10, command=lambda vid=view_id: self._on_nav(vid)
            )
            btn.grid(row=idx, column=0, padx=12, pady=4, sticky="ew")
            self.nav_buttons[view_id] = btn
            self.nav_text_labels[view_id] = {"icon": icon, "text": text}

    def _build_actions(self):
        self.floating_btn = ctk.CTkButton(
            self, text="🪟  浮動字幕模式", font=ctk.CTkFont(family=FONT["body"][0], size=15),
            fg_color=COLORS["primary"], text_color=COLORS["text_light"],
            hover_color=COLORS["primary_hover"], anchor="w", height=48,
            corner_radius=10, command=self._on_floating
        )
        self.floating_btn.grid(row=4, column=0, padx=12, pady=4, sticky="ew")

        self.font_btn = ctk.CTkButton(
            self, text="🔤  文字大小：標準", font=ctk.CTkFont(family=FONT["body"][0], size=15),
            fg_color=COLORS["bg_panel"], text_color=COLORS["text_light"],
            hover_color=COLORS["primary"], anchor="w", height=48,
            corner_radius=10, command=self._on_font
        )
        self.font_btn.grid(row=5, column=0, padx=12, pady=4, sticky="ew")

    def _build_status(self):
        self.status_indicator = ctk.CTkLabel(
            self, text="🟢  系統就緒", font=ctk.CTkFont(family=FONT["small"][0], size=13),
            text_color=COLORS["success"]
        )
        self.status_indicator.grid(row=6, column=0, padx=20, pady=(8, 20), sticky="w")

    def _on_nav(self, view_id):
        if self.on_nav_click:
            self.on_nav_click(view_id)

    def _on_floating(self):
        if self.on_floating_toggle:
            self.on_floating_toggle()

    def _on_font(self):
        if self.on_font_cycle:
            self.on_font_cycle()

    def toggle_menu(self):
        self.menu_expanded = not self.menu_expanded
        if self.menu_expanded:
            self.configure(width=SIDEBAR_EXPANDED_WIDTH)
            self.logo_label.pack(side="left", padx=12)
            for view_id, btn in self.nav_buttons.items():
                btn.configure(text=f"{self.nav_text_labels[view_id]['icon']}  {self.nav_text_labels[view_id]['text']}")
            self.status_indicator.configure(text="🟢  系統就緒")
            self.floating_btn.configure(text="🪟  浮動字幕模式")
            self.font_btn.configure(text=f"🔤  文字大小：{self.font_btn.cget('text').split('：')[-1] if '：' in self.font_btn.cget('text') else '標準'}")
        else:
            self.configure(width=SIDEBAR_COLLAPSED_WIDTH)
            self.logo_label.pack_forget()
            for view_id, btn in self.nav_buttons.items():
                btn.configure(text=self.nav_text_labels[view_id]['icon'])
            self.status_indicator.configure(text="🟢")
            self.floating_btn.configure(text="🪟")
            self.font_btn.configure(text="🔤")

    def set_active_nav(self, view_id):
        for btn in self.nav_buttons.values():
            btn.configure(fg_color="transparent", text_color=COLORS["text_muted"])
        self.nav_buttons[view_id].configure(fg_color=COLORS["primary_muted"], text_color=COLORS["primary"])

    def set_status(self, text, color=None):
        self.status_indicator.configure(text=text, text_color=color if color else COLORS["text_muted"])

    def set_floating_button_state(self, active):
        if active:
            self.floating_btn.configure(text="❌  關閉浮動模式" if self.menu_expanded else "❌", fg_color=COLORS["danger"])
        else:
            self.floating_btn.configure(text="🪟  浮動字幕模式" if self.menu_expanded else "🪟", fg_color=COLORS["primary"])

    def set_font_label(self, label_text):
        if self.menu_expanded:
            self.font_btn.configure(text=f"🔤  文字大小：{label_text}")
        else:
            self.font_btn.configure(text="🔤")
