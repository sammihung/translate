# QwenASR 即時語音辨識與翻譯工具

基於 Qwen3-ASR 的即時語音辨識與翻譯桌面應用程式

## 🚀 快速開始

### 第一次使用？

1. **執行安裝**：雙擊 `scripts\install.bat`
2. **啟動應用程式**：
   - `start.bat` - CPU 模式（一般電腦）
   - `start-gpu.bat` - GPU 加速模式（有獨立顯示卡）

就咁簡單！

---

## 📋 功能特色

- **即時語音辨識**：麥克風輸入，自動 VAD 靜音偵測分段
- **檔案上傳翻譯**：支援音訊/影片檔案上傳並生成雙語字幕
- **OpenVINO INT8**：CPU 高效推理，支援 GPU 加速
- **雙語字幕**：並排顯示原文與翻譯，帶小窗預覽
- **多語言支援**：30+ 語系自動偵測或強制指定
- **說話者分離**：自動識別不同說話者（需額外下載模型）

---

## 💻 系統需求

### CPU 模式（最低）
- Windows 10/11 (64-bit)
- 6 GB RAM
- 2 GB 硬碟空間
- Python 3.10+

### GPU 模式（推薦）
- Vulkan 1.2+ 相容 GPU (NVIDIA/AMD/Intel)
- 8 GB RAM
- 4 GB 硬碟空間

---

## 📁 目錄結構

```
qwen-asr-translate/
│
├── 📁 src/                    # 核心程式碼
│   ├── app.py                # 主程式介面
│   ├── app_gpu.py            # GPU 版本
│   ├── asr_engine.py         # 語音辨識引擎
│   ├── vad_processor.py      # 靜音偵測邏輯
│   └── downloader.py         # 模型下載
│
├── 📁 tools/                  # 測試與除錯工具
│   ├── setup_checker.py      # 環境檢查
│   ├── test_asr.py           # ASR 測試
│   └── ...
│
├── 📁 docs/                   # 說明文件
│   ├── ARCHITECTURE.md       # 架構說明
│   ├── AUDIO_DEVICES_GUIDE.md
│   ├── SYSTEM_AUDIO_GUIDE.md
│   └── ...
│
├── 📁 scripts/                # 批次檔
│   ├── install.bat           # 安裝腳本
│   └── ...
│
├── 📄 start.bat              # 【開始使用】CPU 模式
├── 📄 start-gpu.bat          # 【開始使用】GPU 模式
├── 📄 config.ini             # 設定檔
├── 📄 requirements.txt       # Python 依賴
└── 📄 README.md              # 本檔案
```

---

## 🔧 安裝（手動）

如果自動安裝腳本無法運作，可以手動執行：

```bash
# 1. 建立虛擬環境
python -m venv venv

# 2. 激活虛擬環境
venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 下載模型（首次啟動時會自動下載）
python src\downloader.py
```

---

## 📖 使用方式

### 即時辨識模式
1. 執行 `start.bat` 或 `start-gpu.bat`
2. 選擇麥克風輸入裝置
3. 點選「開始錄音」
4. 對著麥克風說話，系統自動在停頓時辨識

### 檔案上傳模式
1. 執行應用程式
2. 切換到「檔案上傳」分頁
3. 選擇音訊/影片檔案
4. 設定目標翻譯語言
5. 點選「開始轉換」

---

## 📚 詳細文件

更多技術文件請參閱 [`docs/`](docs/) 資料夾：

- [系統架構說明](docs/ARCHITECTURE.md)
- [音訊裝置設定指南](docs/AUDIO_DEVICES_GUIDE.md)
- [系統音訊設定指南](docs/SYSTEM_AUDIO_GUIDE.md)
- [疑難排解](docs/TROUBLESHOOTING.md)
- [UI 設計說明](docs/UI_DESIGN.md)

---

## 🤖 模型來源

- **ASR 模型**: [Qwen/Qwen3-ASR-0.6B](https://huggingface.co/Qwen/Qwen3-ASR-0.6B)
- **OpenVINO INT8**: [dseditor/Qwen3-ASR-0.6B-INT8_ASYM-OpenVINO](https://huggingface.co/dseditor/Qwen3-ASR-0.6B-INT8_ASYM-OpenVINO)
- **GPU 模型**: [dseditor/Qwen3-ASR-1.7B-INT8_ASYM-OpenVINO](https://huggingface.co/dseditor/Qwen3-ASR-1.7B-INT8_ASYM-OpenVINO)
- **翻譯模型**: Helsinki-NOP/OPUS-MT 系列

---

## 🛠️ 開發者筆記

### 新增功能
- 核心邏輯請修改 `src/` 目錄下的檔案
- 測試腳本請放在 `tools/` 目錄
- 文件請放在 `docs/` 目錄

### 說話者分離 (Diarization)
如需啟用說話者分離功能，請執行：
```bash
python scripts\download-diarization.bat
```

---

## 📄 授權

MIT License

---

**💡 提示**：遇到問題？請先查看 [疑難排解指南](docs/TROUBLESHOOTING.md)
