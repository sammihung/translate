from typing import Callable, Optional, Dict, Any


class AppCallbacks:

    def __init__(self):
        self.on_subtitle_update: Optional[Callable[[str, str, int], str]] = None
        self.on_translation_complete: Optional[Callable[[str, str], None]] = None
        self.on_status_change: Optional[Callable[[str, str], None]] = None

    def notify_subtitle_update(self, original: str, translated: str, speaker_id: int) -> str:
        if self.on_subtitle_update:
            return self.on_subtitle_update(original, translated, speaker_id)
        return ""

    def notify_translation_complete(self, bubble_id: str, translated: str) -> None:
        if self.on_translation_complete:
            self.on_translation_complete(bubble_id, translated)

    def notify_status_change(self, status: str, color: str) -> None:
        if self.on_status_change:
            self.on_status_change(status, color)