# QwenASR Real-Time Translate Tool

基於 Qwen3-ASR 的即時語音辨識與翻譯工具

## 功能特色

- **即時語音辨識**: 麥克風輸入，自動 VAD 靜音偵測分段
- **檔案上傳翻譯**: 支援音訊/影片檔案上傳並生成雙語字幕
- **OpenVINO INT8**: CPU 高效推理，支援 GPU 加速
- **雙語字幕**: 並排顯示原文與翻譯，帶小窗預覽
- **多語言支援**: 30+ 語系自動偵測或強制指定
- **說話者分離**: 自動識別不同說話者

## 系統需求

### CPU 模式（最低）
- Windows 10/11 (64-bit)
- 6 GB RAM
- 2 GB 硬碟空間
- Python 3.10+

### GPU 模式（推薦）
- Vulkan 1.2+ 相容 GPU (NVIDIA/AMD/Intel)
- 8 GB RAM
- 4 GB 硬碟空間

## 安裝步驟

### 1. 克隆倉庫
```bash
git clone https://github.com/YOUR_USERNAME/qwen-asr-translate.git
cd qwen-asr-translate
```

### 2. 建立虛擬環境
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. 安裝依賴
```bash
pip install -r requirements.txt
```

### 4. 下載模型
首次啟動時會自動下載所需模型：
- Qwen3-ASR-0.6B INT8 (~1.2 GB)
- VAD 模型 (~2 MB)
- 翻譯模型 (~500 MB)

或手動下載：
```bash
python downloader.py
```

## 使用方式

### 即時辨識模式
```bash
python app.py --mode realtime
```

1. 選擇麥克風輸入裝置
2. 點選「開始錄音」
3. 對著麥克風說話，系統自動在停頓時辨識
4. 即時顯示雙語字幕

### 檔案上傳模式
```bash
python app.py --mode upload
```

1. 選擇音訊/影片檔案
2. 設定目標翻譯語言
3. 點選「開始轉換」
4. 生成雙語 SRT 字幕檔

### GPU 加速模式
```bash
python app_gpu.py
```

使用 Vulkan GPU 後端，載入 1.7B 模型獲得更高辨識率。

## 檔案結構

```
qwen-asr-translate/
├── app.py                  # 主程式（CustomTkinter GUI）
├── app_gpu.py             # GPU 版本
├── asr_engine.py          # ASR 推理引擎
├── translate_engine.py    # 翻譯引擎
├── vad_processor.py       # VAD 靜音偵測
├── subtitle_generator.py  # 雙語字幕生成
├── ui_main.py             # 主介面
├── ui_realtime.py         # 即時辨識介面
├── ui_upload.py           # 上傳翻譯介面
├── downloader.py          # 模型下載器
├── requirements.txt       # Python 依賴
└── README.md             # 說明文件
```

## 模型來源

- **ASR 模型**: [Qwen/Qwen3-ASR-0.6B](https://huggingface.co/Qwen/Qwen3-ASR-0.6B)
- **OpenVINO INT8**: [dseditor/Qwen3-ASR-0.6B-INT8_ASYM-OpenVINO](https://huggingface.co/dseditor/Qwen3-ASR-0.6B-INT8_ASYM-OpenVINO)
- **翻譯模型**: Helsinki-NLP/OPUS-MT 系列

## 授權

MIT License
