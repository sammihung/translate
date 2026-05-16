import tkinter as tk
import customtkinter as ctk
from core.logging_config import get_logger
from ui.theme import COLORS, MAX_FLOATING_BUBBLES, CHAT_FONT
from datetime import datetime

logger = get_logger(__name__)


class FloatingOverlay:

    def __init__(self, master, font_sizes):
        self.master = master
        self.font_sizes = font_sizes
        self.floating_window = None
        self.floating_chat_scroll = None
        self.floating_chat_bubbles = {}
        self.floating_bubble_containers = {}
        self.floating_bubble_order = []

    def open(self, cleaned_bubble_ids):
        try:
            self.floating_window = tk.Toplevel(self.master)
            self.floating_window.title("浮動字幕")
            self.floating_window.attributes("-topmost", True)
            self.floating_window.attributes("-alpha", 0.88)
            self.floating_window.geometry("900x240+100+100")
            self.floating_window.resizable(True, True)
            self.floating_window.configure(bg=COLORS["bg_dark"])

            if hasattr(self.master, 'withdraw'):
                self.master.withdraw()

            bubble_frame = ctk.CTkFrame(
                self.floating_window, fg_color=COLORS["bg_dark"], corner_radius=16,
                border_width=2, border_color=COLORS["primary"]
            )
            bubble_frame.pack(fill="both", expand=True, padx=12, pady=12)

            self.floating_chat_scroll = ctk.CTkScrollableFrame(
                bubble_frame, fg_color="transparent", corner_radius=0
            )
            self.floating_chat_scroll.pack(fill="both", expand=True, padx=12, pady=12)

            self.floating_window.protocol("WM_DELETE_WINDOW", self.close)
            self.floating_chat_bubbles = {}
            self.floating_bubble_containers = {}
            self.floating_bubble_order = []

            logger.info("浮動字幕模式已開啟")
            return True
        except Exception as e:
            logger.error(f"開啟浮動窗口失敗：{e}", exc_info=True)
            return False

    def close(self, main_window_deiconify=None):
        try:
            if self.floating_window and self.floating_window.winfo_exists():
                self.floating_window.destroy()

            self.floating_window = None
            self.floating_chat_bubbles = {}
            self.floating_bubble_containers = {}
            self.floating_bubble_order = []

            if main_window_deiconify and hasattr(main_window_deiconify, 'deiconify'):
                main_window_deiconify.deiconify()

            logger.info("浮動字幕模式已關閉")
            return True
        except Exception as e:
            logger.error(f"關閉浮動窗口失敗：{e}", exc_info=True)
            return False

    def is_open(self):
        return self.floating_window is not None and self.floating_window.winfo_exists()

    def add_bubble(self, bubble_id, speaker_name, original, translated, speaker_id=1, cleaned_bubble_ids=None):
        if not self.is_open():
            return

        is_left = speaker_id == 1
        align = "w" if is_left else "e"
        bubble_color = COLORS["bubble_left"] if is_left else COLORS["bubble_right"]

        container = ctk.CTkFrame(self.floating_chat_scroll, fg_color="transparent")
        container.pack(fill="x", pady=6, padx=6)

        bubble = ctk.CTkFrame(container, fg_color=bubble_color, corner_radius=12)
        bubble.pack(anchor=align, ipadx=8, ipady=8)

        ctk.CTkLabel(
            bubble, text=original,
            font=ctk.CTkFont(family=CHAT_FONT, size=self.font_sizes["original"], slant="italic"),
            text_color=COLORS["text_muted"], wraplength=680, justify="left"
        ).pack(anchor=align, padx=12, pady=(0, 4))

        trans_label = ctk.CTkLabel(
            bubble, text=translated,
            font=ctk.CTkFont(family=CHAT_FONT, size=self.font_sizes["translated"], weight="bold"),
            text_color=COLORS["text_light"], wraplength=680, justify="left"
        )
        trans_label.pack(anchor=align, padx=12, pady=(0, 8))

        self.floating_chat_bubbles[bubble_id] = trans_label
        self.floating_bubble_containers[bubble_id] = container
        self.floating_bubble_order.append(bubble_id)

        self.floating_chat_scroll._parent_canvas.yview_moveto(1.0)

        self._cleanup_old(cleaned_bubble_ids)

    def update_bubble(self, bubble_id, new_translated, cleaned_bubble_ids=None):
        if not self.is_open():
            return
        if cleaned_bubble_ids and bubble_id in cleaned_bubble_ids:
            return
        if bubble_id in self.floating_chat_bubbles:
            self.floating_chat_bubbles[bubble_id].configure(text=new_translated)
            self.floating_chat_scroll._parent_canvas.yview_moveto(1.0)

    def _cleanup_old(self, cleaned_bubble_ids=None):
        while len(self.floating_bubble_order) > MAX_FLOATING_BUBBLES:
            oldest_id = self.floating_bubble_order.pop(0)
            if oldest_id in self.floating_bubble_containers:
                self.floating_bubble_containers[oldest_id].destroy()
                del self.floating_bubble_containers[oldest_id]
            if oldest_id in self.floating_chat_bubbles:
                del self.floating_chat_bubbles[oldest_id]
            if cleaned_bubble_ids is not None:
                cleaned_bubble_ids.add(oldest_id)

    def refresh_fonts(self):
        if not self.is_open():
            return
        for bubble_id, trans_label in self.floating_chat_bubbles.items():
            trans_label.configure(font=ctk.CTkFont(family=CHAT_FONT, size=self.font_sizes["translated"], weight="bold"))
            if bubble_id in self.floating_bubble_containers:
                for widget in self.floating_bubble_containers[bubble_id].winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkLabel):
                                try:
                                    font_str = str(child.cget("font"))
                                    if "italic" in font_str:
                                        child.configure(font=ctk.CTkFont(family=CHAT_FONT, size=self.font_sizes["original"], slant="italic"))
                                except Exception:
                                    pass
