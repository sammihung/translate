# 快速開始指南

## 一鍵安裝

### 1. 安裝 Python 3.10+
從 [python.org](https://www.python.org/downloads/) 下載並安裝 Python 3.10 或更高版本。

安裝時請勾選 **✓ Add Python to PATH**

### 2. 克隆專案
```bash
git clone https://github.com/YOUR_USERNAME/qwen-asr-translate.git
cd qwen-asr-translate
```

### 3. 執行安裝腳本
雙擊執行：
```
install.bat
```

或手動執行：
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. 下載模型
雙擊執行：
```
download-models.bat
```

或執行：
```bash
python downloader.py
```
選擇 `0` 下載所有必需模型（約 1.2 GB）

## 使用方式

### CPU 模式（推薦新手）
雙擊 `start.bat` 或執行：
```bash
python app.py
```

### GPU 模式（需要 NVIDIA/AMD/Intel GPU）
雙擊 `start-gpu.bat` 或執行：
```bash
python app_gpu.py
```

## 功能說明

### 即時轉換分頁
1. 選擇麥克風輸入裝置
2. 點選「開始錄音」
3. 對著麥克風說話
4. 系統會在停頓（約 0.8 秒）後自動辨識並翻譯
5. 雙語字幕即時顯示

### 音檔轉字幕分頁
1. 點選「瀏覽」選擇音訊/影片檔案
2. 設定來源語言和目標語言
3. 勾選「雙語字幕」
4. 點選「開始轉換」
5. 完成後自動開啟輸出資料夾

### 設定分頁
- **顏色模式**: 深色/淺色/跟隨系統
- **中文輸出**: 繁體/簡體
- **模型選擇**: 0.6B（快速）或 1.7B（準確）
- **推理裝置**: CPU 或 GPU

## 常見問題

### Q: 首次啟動無法載入模型？
A: 請確認已完成模型下載，檢查 `ov_models/` 資料夾是否存在模型檔案。

### Q: GPU 模式無法啟動？
A: 
1. 確認已安裝 GPU 驅動程式
2. 執行 `start-gpu.bat` 會自動檢查並下載 GPU 模型
3. 確認顯示卡支援 Vulkan 1.2+

### Q: 辨識準確度不佳？
A: 
1. 切換到 1.7B 模型（設定分頁）
2. 使用 GPU 模式可獲得更好效果
3. 提供辨識提示（歌詞、關鍵字等）

### Q: 影片檔無法處理？
A: 程式會自動下載 ffmpeg（約 55 MB），請保持網路連線。

## 支援的格式

### 音訊
MP3, WAV, FLAC, M4A, OGG

### 影片
MP4, MKV, AVI, MOV, WMV, FLV, WebM

### 語言
自動偵測或強制指定：
- 中文（繁/簡）
- 英文
- 日文
- 韓文
- 法文
- 德文
- 西班牙文
等 30+ 種語言

## 系統需求

### CPU 模式
- Windows 10/11 (64-bit)
- 6 GB RAM
- 2 GB 可用空間
- 任意 x86-64 CPU

### GPU 模式（推薦）
- Windows 10/11 (64-bit)
- 8 GB RAM
- 4 GB 可用空間
- Vulkan 1.2+ 相容 GPU
  - NVIDIA RTX 系列
  - AMD RX 系列
  - Intel Arc

## 授權

MIT License - 詳見 [LICENSE](LICENSE) 檔案

## 致謝

本專案使用以下開源專案：
- [Qwen3-ASR](https://huggingface.co/Qwen/Qwen3-ASR-0.6B) - ASR 模型
- [OpenVINO](https://github.com/openvinotoolkit/openvino) - 推理引擎
- [Silero VAD](https://github.com/snakers4/silero-vad) - 語音活動偵測
- [OPUS-MT](https://github.com/Helsinki-NLP/Opus-MT) - 翻譯模型
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - GUI 框架
