from typing import Optional, List, Dict, Any
from core.logging_config import get_logger

logger = get_logger(__name__)


class SubtitleGenerator:

    def __init__(self):
        self.segments: List[Dict[str, Any]] = []

    def add_segment(self, start, end, original, translated, speaker=None):
        self.segments.append({
            'start': start,
            'end': end,
            'original': original,
            'translated': translated,
            'speaker': speaker
        })

    def format_time(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def export_srt(self, filepath: str, dual_language=True):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(self.segments, 1):
                    f.write(f"{i}\n")
                    f.write(f"{self.format_time(seg['start'])} --> {self.format_time(seg['end'])}\n")
                    if seg.get('speaker'):
                        f.write(f"{seg['speaker']}: ")
                    if dual_language:
                        f.write(f"{seg['original']}\n")
                        f.write(f"{seg['translated']}\n")
                    else:
                        f.write(f"{seg['translated']}\n")
                    f.write("\n")
            logger.info(f"字幕已匯出：{filepath}")
        except Exception as e:
            logger.error(f"匯出 SRT 失敗：{e}", exc_info=True)
            raise