import platform

SYSTEM_FONT = "SF Pro Display" if platform.system() == "Darwin" else "Segoe UI Variable Display"
CHAT_FONT = "SF Pro Text" if platform.system() == "Darwin" else "Segoe UI"

FONT_PRESETS = [
    {"original": 14, "translated": 18, "label": "小"},
    {"original": 16, "translated": 20, "label": "標準"},
    {"original": 18, "translated": 24, "label": "大"},
    {"original": 22, "translated": 28, "label": "超大"},
]

DEFAULT_FONT_PRESET_INDEX = 1

COLORS = {
    "bg_dark": "#0B0F19",
    "bg_panel": "#172033",
    "bg_panel_light": "#1E2A42",
    "bg_input": "#0A0E17",
    "primary": "#3B82F6",
    "primary_hover": "#60A5FA",
    "primary_muted": "#1E3A8A",
    "danger": "#F43F5E",
    "danger_hover": "#E11D48",
    "success": "#10B981",
    "warning": "#F59E0B",
    "text_light": "#F8FAFC",
    "text_muted": "#94A3B8",
    "text_dim": "#475569",
    "border": "#1E293B",
    "bubble_left": "#1E293B",
    "bubble_right": "#164E63",
}

SIDEBAR_EXPANDED_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 68

NAV_ITEMS = [
    ("realtime", "⚡", "即時翻譯"),
    ("batch", "📁", "批量上傳"),
    ("settings", "⚙️", "系統設定"),
]

SRC_LANGS = {"自動偵測 (Auto)": "auto", "日文 (JA)": "ja", "英文 (EN)": "en", "中文 (ZH)": "zh", "韓文 (KO)": "ko"}
TGT_LANGS = {"繁體中文 (ZH)": "zh", "英文 (EN)": "en", "日文 (JA)": "ja", "韓文 (KO)": "ko"}

AUDIO_SOURCE_MAP = {"🎤 麥克風": "mic", "🔊 系統音訊": "system", "🖥️ Per-App": "per-app"}
AUDIO_SOURCE_DISPLAY = ["🎤 麥克風", "🔊 系統音訊", "🖥️ Per-App"]

MAX_BUBBLES = 100
MAX_FLOATING_BUBBLES = 50
MAX_CLEANED_IDS = 200

FONT = {
    "title": (SYSTEM_FONT, 22, "bold"),
    "heading": (SYSTEM_FONT, 16, "bold"),
    "subheading": (SYSTEM_FONT, 14, "bold"),
    "body": (SYSTEM_FONT, 13),
    "body_bold": (SYSTEM_FONT, 13, "bold"),
    "small": (SYSTEM_FONT, 12),
    "tiny": (SYSTEM_FONT, 11),
    "icon_large": ("Segoe UI Emoji", 22),
    "icon": ("Segoe UI Emoji", 16),
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}
