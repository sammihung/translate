# 🏗️ `__init__.py` 黃金法則

## 📊 核心原則

**`__init__.py` 係一家公司嘅「接待櫃檯 (Facade)」，唔係「倉庫」！**

---

## ✅ 適合放 `__init__.py` 嘅情況

### 1. 輕量級配置層 (Config) ✅

**檔案**: `src/qwen_asr/config/__init__.py`

```python
from qwen_asr_app.config.settings import AppConfig, get_config

__all__ = ["AppConfig", "get_config"]
```

**優點**:
- ✅ 啟動快速 (無重型套件)
- ✅ 路徑乾淨 (`from qwen_asr_app.config import AppConfig`)
- ✅ 易於維護

---

### 2. 核心層 (Core) ✅

**檔案**: `src/qwen_asr/core/__init__.py`

```python
from qwen_asr_app.core.logging_config import setup_logging, get_logger
from qwen_asr_app.core.model_registry import PerformanceMode, PerformanceTier

__all__ = [
    "setup_logging",
    "get_logger",
    "PerformanceMode",
    "PerformanceTier"
]
```

**優點**:
- ✅ 統一入口
- ✅ 暴露常用功能
- ✅ 隱藏內部結構

---

### 3. Domain/UI 層 ✅

**檔案**: `src/qwen_asr/domain/__init__.py` / `src/qwen_asr/ui/__init__.py`

```python
# Domain
from qwen_asr_app.domain.controller import AppController
__all__ = ["AppController"]

# UI
from qwen_asr_app.ui.ui import MainUI
__all__ = ["MainUI"]
```

**優點**:
- ✅ 乾淨嘅公開 API
- ✅ 使用者唔使知道內部檔案結構
- ✅ 易於重構內部檔案

---

## ❌ 唔適合放 `__init__.py` 嘅情況

### 1. AI 層 (重型套件) ❌

**檔案**: `src/qwen_asr/ai/__init__.py`

```python
# ❌ 災難！唔好咁寫！
from qwen_asr_app.ai.asr_engine import ASREngine  # 會載入 PyTorch (幾 GB)
```

**問題**:
- ❌ **啟動延遲**: 只要 import `qwen_asr.ai`，PyTorch 即刻載入 (幾秒)
- ❌ **記憶體暴增**: 即使只係想用 Config，都會載入成個 AI 引擎
- ❌ **循環依賴**: 容易同 Domain 層形成死結

**正確做法**:
```python
# ✅ 保持留白，或只寫註釋
"""
AI 層 - AI 模型管理

⚠️ 注意：呢層唔應該自動載入 PyTorch/Transformers
避免啟動延遲同記憶體暴增

請直接 import 特定檔案：
    from qwen_asr_app.ai.asr_engine import ASREngine
    from qwen_asr_app.ai.ai_controller import AIController
"""

# 保持留白，避免循環依賴
```

---

### 2. Audio 層 (硬件依賴) ❌

**檔案**: `src/qwen_asr/audio/__init__.py`

```python
# ❌ 唔好咁寫！
from qwen_asr_app.audio.audio_manager import AudioManager  # 會載入 PyAudio
```

**問題**:
- ❌ **硬件初始化**: PyAudio 可能會嘗試訪問音訊設備
- ❌ **啟動失敗**: 如果無音訊設備，程式直接崩潰
- ❌ **循環依賴**: 可能同 Domain 層形成死結

**正確做法**:
```python
# ✅ 保持留白，或只寫註釋
"""
Audio 層 - 音訊設備管理

⚠️ 注意：呢層唔應該自動載入 PyAudio
避免啟動延遲

請直接 import 特定檔案：
    from qwen_asr_app.audio.audio_manager import AudioManager
    from qwen_asr_app.audio.vad_processor import VADProcessor
"""

# 保持留白，避免循環依賴
```

---

## 👑 專業開發者的黃金法則

### 1. 延遲載入 (Lazy Loading)

**只喺真正需要嘅時候先載入重型套件**：

```python
# ❌ 錯誤：一啟動就載入
from qwen_asr_app.ai import ASREngine  # 載入 PyTorch

# ✅ 正確：需要嘅時候先載入
def load_asr():
    from qwen_asr_app.ai.asr_engine import ASREngine
    return ASREngine()
```

---

### 2. 最小暴露原則

**只暴露必要嘅公開 API**：

```python
# ✅ 好：只暴露核心類別
__all__ = ["AppController", "MainUI"]

# ❌ 唔好：暴露所有內部細節
__all__ = ["AppController", "MainUI", "helper_func1", "helper_func2", "CONSTANT1"]
```

---

### 3. 避免循環依賴

**檢查依賴方向**：

```
✅ 正確：
Config → Core (無依賴)
Domain → AI, Audio (單向)
UI → Domain (單向)

❌ 錯誤：
AI ↔ Domain (循環！)
Audio ↔ Domain (循環！)
```

---

## 📊 本專案的 `__init__.py` 配置

| 層級 | 是否暴露 | 原因 |
|------|----------|------|
| **Config** | ✅ 暴露 | 輕量級，無重型套件 |
| **Core** | ✅ 暴露 | 日誌、模型註冊表 (輕量) |
| **Domain** | ✅ 暴露 | 業務邏輯核心 |
| **UI** | ✅ 暴露 | 使用者介面核心 |
| **AI** | ❌ 留白 | PyTorch/Transformers 太重 |
| **Audio** | ❌ 留白 | PyAudio 硬件依賴 |
| **Utils** | ❌ 留白 | 工具函數，按需 import |

---

## 🎯 使用示例

### 優雅嘅企業級寫法

```python
# ✅ 主程式 (main.py)
from qwen_asr_app.config import AppConfig
from qwen_asr_app.core import setup_logging, get_logger
from qwen_asr_app.domain import AppController
from qwen_asr_app.ui import MainUI

# 需要 AI 時先載入
def init_ai():
    from qwen_asr_app.ai.asr_engine import ASREngine
    from qwen_asr_app.ai.ai_controller import AIController
    return AIController()

# 需要 Audio 時先載入
def init_audio():
    from qwen_asr_app.audio.audio_manager import AudioManager
    return AudioManager()
```

### 唔好嘅寫法

```python
# ❌ 暴露內部結構
from qwen_asr_app.ai.asr_engine import ASREngine  # 直接 import 檔案
from qwen_asr_app.audio.audio_manager import AudioManager

# ❌ 一啟動就載入 PyTorch
import qwen_asr_app.ai  # 災難！
```

---

## 🚨 常見錯誤

### 錯誤 1: 過度暴露

```python
# ❌ 唔好將所有嘢都放進 __init__.py
from .asr_engine import ASREngine
from .ai_controller import AIController
from .translation_engine import TranslationEngine
from .vad_processor import VADProcessor
# ... 十幾個 import

# 結果：啟動慢到癲，記憶體爆滿
```

---

### 錯誤 2: 循環依賴

```python
# ❌ ai/__init__.py
from qwen_asr_app.domain import AppController  # Domain 依賴 AI

# ❌ domain/__init__.py
from qwen_asr_app.ai import ASREngine  # AI 依賴 Domain

# 結果：Circular Import → 程式崩潰
```

---

### 錯誤 3: 忽略 `__all__`

```python
# ❌ 無定義 __all__
from .settings import AppConfig

# 結果：所有內部函數都暴露咗，使用者可能用到唔穩定嘅 API
```

---

## 🎉 總結

**`__init__.py` 係用來「包裝」同「簡化路徑」嘅工具**：

✅ **適合**:
- 輕量級配置 (Config)
- 核心功能 (Core)
- 業務邏輯 (Domain)
- 使用者介面 (UI)

❌ **唔適合**:
- 重型套件 (PyTorch, Transformers)
- 硬件依賴 (PyAudio)
- 可能形成循環依賴嘅模組

**記住**：`__init__.py` 係接待櫃檯，唔係倉庫！只暴露必要嘅公開 API，其他嘢保持留白，按需 import！

---

## 📁 參考檔案

- [`src/qwen_asr/__init__.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/qwen_asr/__init__.py)
- [`src/qwen_asr/config/__init__.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/qwen_asr/config/__init__.py)
- [`src/qwen_asr/core/__init__.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/qwen_asr/core/__init__.py)
- [`src/qwen_asr/domain/__init__.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/qwen_asr/domain/__init__.py)
- [`src/qwen_asr/ui/__init__.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/qwen_asr/ui/__init__.py)
- [`src/qwen_asr/ai/__init__.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/qwen_asr/ai/__init__.py) (留白)
- [`src/qwen_asr/audio/__init__.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/qwen_asr/audio/__init__.py) (留白)
