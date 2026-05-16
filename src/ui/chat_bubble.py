import customtkinter as ctk
from datetime import datetime
from ui.theme import COLORS, MAX_BUBBLES, MAX_CLEANED_IDS


class ChatBubbleManager:

    def __init__(self, chat_scroll, font_sizes):
        self.chat_scroll = chat_scroll
        self.font_sizes = font_sizes
        self.chat_bubbles = {}
        self.bubble_containers = {}
        self.bubble_order = []
        self.cleaned_bubble_ids = set()

    def add_bubble(self, speaker_name, original, translated, speaker_id=1):
        bubble_id = self._create_bubble_id()
        self._create_bubble_widget(bubble_id, speaker_name, original, translated, speaker_id)
        self._cleanup_old()
        self._scroll_to_bottom()
        return bubble_id

    def update_bubble(self, bubble_id, new_translated):
        if bubble_id in self.cleaned_bubble_ids:
            return
        if bubble_id in self.chat_bubbles:
            self.chat_bubbles[bubble_id].configure(text=new_translated)
            self._scroll_to_bottom()

    def _create_bubble_id(self):
        import uuid
        return str(uuid.uuid4())

    def _create_bubble_widget(self, bubble_id, speaker_name, original, translated, speaker_id):
        is_left = speaker_id == 1
        align = "w" if is_left else "e"
        bubble_color = COLORS["bubble_left"] if is_left else COLORS["bubble_right"]
        accent_color = COLORS["primary"] if is_left else COLORS["success"]

        container = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        container.pack(fill="x", pady=(8, 8), padx=8)

        bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=16)
        bubble.pack(anchor=align, ipadx=6, ipady=6)

        header = ctk.CTkFrame(bubble, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 6))

        side_align = "left" if is_left else "right"
        ctk.CTkLabel(
            header, text=speaker_name, font=ctk.CTkFont(size=12, weight="bold"),
            text_color=accent_color
        ).pack(side=side_align)
        ctk.CTkLabel(
            header, text=datetime.now().strftime("%H:%M:%S"),
            font=ctk.CTkFont(family="Courier", size=11),
            text_color=COLORS["text_dim"]
        ).pack(side=side_align, padx=12)

        ctk.CTkLabel(
            bubble, text=original,
            font=ctk.CTkFont(size=self.font_sizes["original"], slant="italic"),
            text_color=COLORS["text_muted"], wraplength=560, justify="left"
        ).pack(anchor=align, padx=14, pady=(0, 4))

        trans_label = ctk.CTkLabel(
            bubble, text=translated,
            font=ctk.CTkFont(size=self.font_sizes["translated"], weight="bold"),
            text_color=COLORS["text_light"], wraplength=560, justify="left"
        )
        trans_label.pack(anchor=align, padx=14, pady=(0, 10))

        self.chat_bubbles[bubble_id] = trans_label
        self.bubble_containers[bubble_id] = container
        self.bubble_order.append(bubble_id)

    def _cleanup_old(self):
        while len(self.bubble_order) > MAX_BUBBLES:
            oldest_id = self.bubble_order.pop(0)
            if oldest_id in self.bubble_containers:
                self.bubble_containers[oldest_id].destroy()
                del self.bubble_containers[oldest_id]
            if oldest_id in self.chat_bubbles:
                del self.chat_bubbles[oldest_id]
            self.cleaned_bubble_ids.add(oldest_id)

        if len(self.cleaned_bubble_ids) > MAX_CLEANED_IDS:
            id_list = list(self.cleaned_bubble_ids)
            self.cleaned_bubble_ids = set(id_list[-MAX_CLEANED_IDS:])

    def _scroll_to_bottom(self):
        self.chat_scroll._parent_canvas.yview_moveto(1.0)

    def refresh_fonts(self):
        for bubble_id, trans_label in self.chat_bubbles.items():
            trans_label.configure(font=ctk.CTkFont(size=self.font_sizes["translated"], weight="bold"))
            if bubble_id in self.bubble_containers:
                for widget in self.bubble_containers[bubble_id].winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkLabel):
                                try:
                                    font_str = str(child.cget("font"))
                                    if "italic" in font_str:
                                        child.configure(font=ctk.CTkFont(size=self.font_sizes["original"], slant="italic"))
                                except Exception:
                                    pass

    def clear_cleaned_ids(self):
        self.cleaned_bubble_ids.clear()
