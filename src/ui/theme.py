FONT_PRESETS = [
    {"original": 11, "translated": 14, "label": "小"},
    {"original": 13, "translated": 16, "label": "標準"},
    {"original": 15, "translated": 18, "label": "大"},
    {"original": 18, "translated": 22, "label": "超大"},
]

DEFAULT_FONT_PRESET_INDEX = 1

COLORS = {
    "bg_dark": "#0b0f19",
    "bg_panel": "#1e293b",
    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
    "primary_muted": "#1e3a8a",
    "danger": "#ef4444",
    "danger_hover": "#dc2626",
    "success": "#10b981",
    "text_light": "#f8fafc",
    "text_muted": "#94a3b8",
}

SIDEBAR_EXPANDED_WIDTH = 200
SIDEBAR_COLLAPSED_WIDTH = 60

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