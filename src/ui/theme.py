FONT_PRESETS = [
    {"original": 14, "translated": 18, "label": "小"},
    {"original": 16, "translated": 20, "label": "標準"},
    {"original": 18, "translated": 24, "label": "大"},
    {"original": 22, "translated": 28, "label": "超大"},
]

DEFAULT_FONT_PRESET_INDEX = 1

COLORS = {
    "bg_dark": "#0b0f19",
    "bg_panel": "#1e293b",
    "bg_panel_light": "#273449",
    "bg_input": "#0f172a",
    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
    "primary_muted": "#1e3a8a",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "success": "#10b981",
    "warning": "#f59e0b",
    "text_light": "#f8fafc",
    "text_muted": "#94a3b8",
    "text_dim": "#64748b",
    "border": "#334155",
    "bubble_left": "#1e293b",
    "bubble_right": "#064e3b",
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
    "title": ("size", 20, "weight", "bold"),
    "heading": ("size", 16, "weight", "bold"),
    "subheading": ("size", 14, "weight", "bold"),
    "body": ("size", 13),
    "body_bold": ("size", 13, "weight", "bold"),
    "small": ("size", 12),
    "tiny": ("size", 11),
    "icon_large": ("size", 22),
    "icon": ("size", 16),
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}
