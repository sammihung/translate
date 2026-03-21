"""
模型配置註冊表 - Model Registry
提供三階段效能分級配置 (極速/平衡/滿血)
"""

from typing import Dict, Literal
from dataclasses import dataclass
from enum import Enum


class PerformanceMode(Enum):
    """效能模式列舉"""
    FAST = "fast"          # ⚡ 極速版 (Low-end PC)
    BALANCED = "balanced"  # ⚖️ 平衡版 (Mainstream PC)
    FULL = "full"          # 🩸 滿血版 (Pro Workstation)


@dataclass
class ASRModelConfig:
    """ASR 模型配置"""
    name: str
    repo: str
    precision: str
    description: str
    recommended_vram: str  # 建議 VRAM


@dataclass
class TranslationModelConfig:
    """翻譯模型配置"""
    name: str
    model_tag: str
    precision: str
    description: str
    recommended_vram: str  # 建議 VRAM


@dataclass
class PerformanceTier:
    """效能分級配置"""
    mode: PerformanceMode
    display_name: str
    icon: str
    asr: ASRModelConfig
    translation: TranslationModelConfig
    target_audience: str


# ============================================
# 模型註冊表
# ============================================

AVAILABLE_MODELS = {
    "asr": {
        "fast": ASRModelConfig(
            name="Qwen3-ASR-0.6B INT8",
            repo="dseditor/Qwen3-ASR-0.6B-INT8_ASYM-OpenVINO",
            precision="int8",
            description="極速 ASR，適合無獨立顯卡或舊電腦",
            recommended_vram="4GB RAM"
        ),
        "balanced": ASRModelConfig(
            name="Qwen3-ASR-1.7B INT8",
            repo="dseditor/Qwen3-ASR-1.7B-INT8_OpenVINO",
            precision="int8",
            description="平衡 ASR，準確度與速度的最佳平衡點",
            recommended_vram="8GB RAM / 4GB VRAM"
        ),
        "full": ASRModelConfig(
            name="Qwen3-ASR-1.7B FP16",
            repo="Qwen/Qwen3-ASR-1.7B",
            precision="fp16",
            description="滿血 ASR，最高辨識準確率",
            recommended_vram="12GB VRAM"
        )
    },
    "translation": {
        "fast": TranslationModelConfig(
            name="TranslateGemma 4B 4-bit",
            model_tag="translategemma:4b-it-q4_K_M",
            precision="q4_k_m",
            description="4-bit 量化翻譯，速度極快，記憶體佔用低",
            recommended_vram="4GB VRAM / 8GB RAM"
        ),
        "balanced": TranslationModelConfig(
            name="TranslateGemma 4B 8-bit",
            model_tag="translategemma:4b-it-q8_0",
            precision="q8_0",
            description="8-bit 量化翻譯，保留更多語氣細節",
            recommended_vram="6GB VRAM / 12GB RAM"
        ),
        "full": TranslationModelConfig(
            name="TranslateGemma 4B FP16",
            model_tag="translategemma:4b-it-fp16",
            precision="fp16",
            description="16-bit 滿血翻譯，最高準確率",
            recommended_vram="16GB VRAM"
        )
    }
}

# ============================================
# 預設效能分級組合
# ============================================

PERFORMANCE_TIERS: Dict[PerformanceMode, PerformanceTier] = {
    PerformanceMode.FAST: PerformanceTier(
        mode=PerformanceMode.FAST,
        display_name="⚡ 極速版",
        icon="⚡",
        asr=AVAILABLE_MODELS["asr"]["fast"],
        translation=AVAILABLE_MODELS["translation"]["fast"],
        target_audience="無獨立顯卡、舊電腦、追求最低延遲"
    ),
    PerformanceMode.BALANCED: PerformanceTier(
        mode=PerformanceMode.BALANCED,
        display_name="⚖️ 平衡版",
        icon="⚖️",
        asr=AVAILABLE_MODELS["asr"]["balanced"],
        translation=AVAILABLE_MODELS["translation"]["balanced"],
        target_audience="入門獨顯、較新 CPU/RAM、一般用戶"
    ),
    PerformanceMode.FULL: PerformanceTier(
        mode=PerformanceMode.FULL,
        display_name="🩸 滿血版",
        icon="🩸",
        asr=AVAILABLE_MODELS["asr"]["full"],
        translation=AVAILABLE_MODELS["translation"]["full"],
        target_audience="高階 GPU (RTX 3060+)、專業用戶、追求零錯誤"
    )
}


def get_performance_tier(mode: PerformanceMode) -> PerformanceTier:
    """獲取指定效能分級的配置"""
    return PERFORMANCE_TIERS[mode]


def get_all_tiers() -> list[PerformanceTier]:
    """獲取所有效能分級配置"""
    return list(PERFORMANCE_TIERS.values())


def get_tier_display_names() -> list[str]:
    """獲取所有效能分級的顯示名稱 (用於 UI 下拉選單)"""
    return [tier.display_name for tier in get_all_tiers()]


def get_tier_by_display_name(display_name: str) -> PerformanceTier:
    """根據顯示名稱獲取效能分級配置"""
    for tier in get_all_tiers():
        if tier.display_name == display_name:
            return tier
    raise ValueError(f"未知的效能模式：{display_name}")


# ============================================
# 技術說明文檔
# ============================================

TECHNICAL_NOTES = """
## 模型量化技術說明

### ASR 模型 (語音辨識)

**為什麼 ASR 不用 4-bit？**
- 語音聲學模型對權重精度比 LLM 更敏感
- 4-bit 量化容易導致「幻聽」或辨識亂碼
- INT8 (8-bit) 已經是體積和速度的最佳平衡點

**精度對比：**
- FP16 (滿血): WER 最低，體積 ~6-7GB
- INT8 (平衡): WER 略增 1-2%，體積 ~4.3GB
- 4-bit (不推薦): WER 飆升 5-10%，不建議使用

### 翻譯模型 (LLM)

**4-bit vs 8-bit vs 16-bit：**
- q4_K_M (4-bit): 性價比最高，體積 ~2.5GB，速度飛快
- q8_0 (8-bit): 保留更多語氣細節，體積 ~4-5GB
- fp16 (16-bit): 完全不犧牲，翻譯最準確，體積 ~8GB

**Ollama 量化標籤說明：**
- q4_K_M: 4-bit K-quants Medium (推薦)
- q8_0: 8-bit 量化
- fp16: 原生半精度

### 硬體建議

**極速版 (Fast):**
- CPU: Intel i5 / AMD Ryzen 5 (第 8 代以上)
- RAM: 8GB 以上
- GPU: 無要求 (可純 CPU 運行)

**平衡版 (Balanced):**
- CPU: Intel i7 / AMD Ryzen 7
- RAM: 16GB 以上
- GPU: GTX 1650 / RTX 3050 或同等 (4GB VRAM)

**滿血版 (Full):**
- CPU: Intel i9 / AMD Ryzen 9
- RAM: 32GB 以上
- GPU: RTX 3060 / 4060 以上 (12GB+ VRAM)
"""
