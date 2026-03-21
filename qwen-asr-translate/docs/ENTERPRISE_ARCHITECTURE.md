# 🏗️ 企業級架構文檔 (Enterprise Architecture)

## 📊 專案結構

本專案採用 **領域驅動設計 (Domain-Driven Design, DDD)** 原則，將系統拆分為清晰嘅功能層：

```
qwen-asr-translate/
├── src/qwen_asr/              # 核心套件
│   ├── __init__.py            # 套件版本、作者信息
│   ├── main.py                # 唯一程式進入點 (Entry Point)
│   │
│   ├── core/                  # 核心層：基礎設施
│   │   ├── __init__.py
│   │   ├── logging_config.py  # 結構化日誌配置
│   │   └── model_registry.py  # 模型註冊表 (三階效能分級)
│   │
│   ├── config/                # 配置層：環境變數、應用設定
│   │   ├── __init__.py
│   │   └── settings.py        # pydantic-settings 配置管理
│   │
│   ├── audio/                 # 音訊處理層
│   │   ├── __init__.py
│   │   ├── audio_manager.py   # 音訊設備管理、錄音
│   │   └── vad_processor.py   # VAD 語音活動偵測
│   │
│   ├── ai/                    # AI 引擎層
│   │   ├── __init__.py
│   │   ├── asr_engine.py      # Qwen ASR 語音辨識
│   │   └── ai_controller.py   # Ollama 翻譯引擎
│   │
│   ├── domain/                # 業務邏輯層
│   │   ├── __init__.py
│   │   └── controller.py      # 調控各層互動、Batching
│   │
│   ├── ui/                    # 介面層
│   │   ├── __init__.py
│   │   └── ui.py              # CustomTkinter 視窗
│   │
│   └── utils/                 # 共用工具
│       └── __init__.py
│
├── tests/                     # 測試
│   ├── unit/                  # 單元測試
│   └── integration/           # 整合測試
│
├── deploy/                    # 部署
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/                      # 文檔
├── logs/                      # 日誌 (已忽略)
├── config/                    # 配置文件
│
├── .env.example               # 環境變數範本
├── .gitignore                 # Git 忽略規則
├── pyproject.toml             # 現代化套件管理
└── README.md
```

---

## 🎯 核心設計原則

### 1. 關注點分離 (Separation of Concerns)

每個模組只負責單一職責：

| 層級 | 職責 | 示例文件 |
|------|------|----------|
| **UI 層** | 用戶界面、事件處理 | `ui.py` |
| **Domain 層** | 業務邏輯、流程控制 | `controller.py` |
| **AI 層** | AI 模型推理 | `asr_engine.py`, `ai_controller.py` |
| **Audio 層** | 音訊硬件操作 | `audio_manager.py` |
| **Core 層** | 基礎設施 | `logging_config.py` |
| **Config 層** | 配置管理 | `settings.py` |

**優點**:
- ✅ 易於測試 (可以單獨測試每一層)
- ✅ 易於維護 (修改一層唔會影響其他層)
- ✅ 易於擴展 (可以替換某一層而不影響整體)

---

### 2. 依賴注入 (Dependency Injection)

所有配置都從 `config.settings` 注入，唔應該寫死喺代碼入面：

```python
# ❌ 錯誤做法 (寫死預設值)
class ASREngine:
    def __init__(self):
        self.threshold = 150.0  # ❌ 寫死

# ✅ 正確做法 (依賴注入)
from qwen_asr_app.config import get_config

class ASREngine:
    def __init__(self, config=None):
        self.config = config or get_config()
        self.threshold = self.config.vad_rms_threshold  # ✅ 從配置讀取
```

**優點**:
- ✅ 易於切換環境 (開發/測試/生產)
- ✅ 易於調整參數 (唔使改代碼)
- ✅ 易於測試 (可以注入 mock 配置)

---

### 3. 配置管理 (Configuration Management)

使用 `pydantic-settings` 管理所有配置：

```python
# config/settings.py
from pydantic_settings import BaseSettings

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    
    asr_model_name: str = "Qwen/Qwen3-ASR-1.7B"
    vad_rms_threshold: float = 150.0
    performance_mode: str = "balanced"

config = AppConfig()
```

**配置優先級**:
1. 環境變數 (最高)
2. `.env` 文件
3. 預設值 (最低)

**使用方法**:
```bash
# 1. 複製範本
cp .env.example .env

# 2. 編輯 .env
vi .env

# 3. 啟動應用程式
python -m qwen_asr.main
```

---

### 4. 錯誤處理 (Error Handling)

所有錯誤都應該被適當處理同記錄：

```python
import logging
from qwen_asr_app.core.logging_config import get_logger

logger = get_logger(__name__)

def process_audio(audio):
    try:
        result = asr_engine.process(audio)
        return result
    except Exception as e:
        logger.error(f"音訊處理失敗：{e}", exc_info=True)
        return None
```

**錯誤分級**:
- `DEBUG`: 調試信息 (開發環境)
- `INFO`: 一般信息 (生產環境)
- `WARNING`: 警告 (唔影響運行)
- `ERROR`: 錯誤 (功能失敗)
- `CRITICAL`: 嚴重錯誤 (系統崩潰)

---

### 5. 日誌記錄 (Logging)

使用結構化日誌，唔好用 `print()`:

```python
# ❌ 錯誤做法
print(f"ASR 結果：{result}")

# ✅ 正確做法
logger.info(f"ASR 辨識結果：{result[:50]}...")
```

**日誌格式**:
```
2026-03-21 21:19:45 | qwen_asr.asr_engine | INFO | asr_engine.py:134 | process_audio | ASR 辨識結果：早晨...
```

**包含信息**:
- 時間戳
- 模組名稱
- 日誌級別
- 文件位置
- 函數名稱
- 日誌內容

---

## 🚀 部署流程

### 本地開發

```bash
# 1. 克隆專案
git clone <repo_url>
cd qwen-asr-translate

# 2. 創建虛擬環境
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

# 3. 安裝依賴
pip install -e .

# 4. 配置環境
cp .env.example .env
vi .env  # 編輯配置

# 5. 啟動應用程式
python -m qwen_asr.main
```

### Docker 部署 (推薦)

```bash
# 1. 構建鏡像
docker build -t qwen-asr-translate:latest .

# 2. 啟動容器
docker run --gpus all -p 11434:11434 qwen-asr-translate:latest

# 3. 或使用 docker-compose
docker-compose up -d
```

---

## 📊 效能優化

### 1. Thread Pool

限制併發翻譯數量，防止資源耗盡：

```python
from concurrent.futures import ThreadPoolExecutor

# Domain 層
class AppController:
    def __init__(self, config=None):
        self.config = config or get_config()
        self.translate_pool = ThreadPoolExecutor(
            max_workers=self.config.translate_pool_max_workers
        )
```

### 2. Batching

合併多個語句進行批量翻譯：

```python
# Domain 層
class AppController:
    def __init__(self):
        self.translation_buffer = []
        self.batch_max_chars = 50
        self.batch_timeout = 1.0
    
    def add_to_buffer(self, text):
        self.translation_buffer.append(text)
        if len(self.translation_buffer) >= self.batch_max_chars:
            self.flush_buffer()
```

### 3. 模型量化

根據效能模式選擇合適嘅量化級別：

```python
# Core 層
class ModelRegistry:
    @staticmethod
    def get_model_config(mode: PerformanceMode):
        configs = {
            PerformanceMode.FAST: {
                "asr": "Qwen/Qwen3-ASR-0.6B",
                "translate": "translategemma:4b-it-q4_K_M"
            },
            PerformanceMode.BALANCED: {
                "asr": "Qwen/Qwen3-ASR-1.7B",
                "translate": "translategemma:4b-it-q8_0"
            },
            PerformanceMode.FULL: {
                "asr": "Qwen/Qwen3-ASR-1.7B",
                "translate": "translategemma:4b-it-fp16"
            }
        }
        return configs[mode]
```

---

## 🧪 測試策略

### 單元測試 (Unit Tests)

測試單一功能：

```python
# tests/unit/test_audio_manager.py
import pytest
from qwen_asr_app.audio.audio_manager import AudioManager

def test_parse_device_index():
    am = AudioManager()
    assert am.parse_device_index("麥克風 [2]") == 2
    assert am.parse_device_index("預設設備") is None
    assert am.parse_device_index("") is None
```

### 整合測試 (Integration Tests)

測試完整流程：

```python
# tests/integration/test_asr_pipeline.py
def test_asr_translation_pipeline():
    """測試 ASR → Batching → 翻譯 完整流程"""
    config = get_test_config()
    controller = AppController(config)
    
    # 模擬語音輸入
    audio_data = load_test_audio()
    result = controller.process_audio(audio_data)
    
    # 驗證結果
    assert result is not None
    assert len(result.translated) > 0
```

---

## 📁 關鍵文件說明

### `config/settings.py`
- 使用 `pydantic-settings` 管理所有配置
- 支持環境變數、`.env` 文件、預設值
- 提供類型檢查同自動補全

### `core/logging_config.py`
- 配置 RotatingFileHandler (10MB 輪轉，5 份備份)
- 全局異常捕捉 (`sys.excepthook`)
- 結構化日誌格式

### `domain/controller.py`
- 核心業務邏輯
- 調控 UI、Audio、AI 各層
- 實現 Batching、Thread Pool 等優化

### `ai/asr_engine.py`
- Qwen ASR 模型載入同推理
- 支持 INT8 量化、SDPA 加速
- 深度記憶體回收

---

## 🎯 最佳實踐

### 1. 代碼風格
- 使用 `black` 格式化代碼
- 使用 `ruff` 檢查代碼質量
- 使用 `mypy` 進行類型檢查

### 2. Git 工作流
- 使用 `pre-commit` hooks
- 每個 commit 應該通過所有測試
- 使用有意義的 commit message

### 3. 文檔
- 每個公開函數都應該有 docstring
- 使用 Sphinx 生成 API 文檔
- 保持 README.md 更新

### 4. 安全性
- 永遠唔好 commit `.env` 文件
- 使用 `.gitignore` 忽略敏感文件
- 定期更新依賴套件

---

## 🚨 常見問題

### Q: 點解要用 `src-layout`?
**A**: 避免套件路徑污染，確保測試同生產環境一致。

### Q: 點解要用 `pydantic-settings`?
**A**: 提供類型檢查、自動補全、環境變數支持，比手動解析 `.env` 更專業。

### Q: 點解要分離 Domain 層？
**A**: Domain 層包含核心業務邏輯，分離後可以獨立測試同替換，唔會影響其他層。

### Q: 點解要用 Thread Pool?
**A**: 限制併發數量，防止資源耗盡，確保系統穩定性。

---

## 📊 效能指標

| 指標 | 目標 | 測量方法 |
|------|------|----------|
| **ASR 延遲** | <500ms | 語音輸入 → 文字輸出 |
| **翻譯延遲** | <2s | 文字輸入 → 翻譯輸出 |
| **記憶體佔用** | <8GB | `nvidia-smi` / 工作管理員 |
| **UI 響應** | <100ms | 點擊按鈕 → UI 更新 |
| **錯誤率** | <1% | 錯誤日誌 / 總請求數 |

---

## 🎉 總結

本架構遵循企業級軟體工程最佳實踐：

✅ **領域驅動設計** - 清晰嘅功能分層  
✅ **依賴注入** - 易於測試同維護  
✅ **配置管理** - 支持多環境部署  
✅ **錯誤處理** - 完善嘅日誌記錄  
✅ **自動化測試** - 單元測試 + 整合測試  
✅ **Docker 部署** - 一鍵啟動，消除環境差異  

**呢個架構可以支持從個人項目到企業級產品嘅無縫擴展！** 🚀
