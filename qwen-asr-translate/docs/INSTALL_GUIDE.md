# 完整安裝指南

## 步驟 1: 安裝 Python

### 下載 Python
1. 前往 [Python 官方下載頁面](https://www.python.org/downloads/)
2. 下載 **Python 3.10** 或更高版本（建議 3.11 或 3.12）
3. 選擇 Windows installer (64-bit)

### 安裝 Python
1. 執行下載的安裝檔
2. **重要**: 勾選 ✅ **Add Python to PATH**
3. 點擊 "Install Now"
4. 等待安裝完成

### 驗證安裝
開啟命令提示字元 (CMD) 或 PowerShell，輸入:
```bash
python --version
```
應該顯示：`Python 3.1x.x`

---

## 步驟 2: 安裝 Git (選選)

### 下載 Git
1. 前往 [Git 官方下載頁面](https://git-scm.com/download/win)
2. 下載並安裝 Git for Windows

### 克隆專案 (如果使用 Git)
```bash
cd C:\Users\sammi_hung\lobsterai\project
git clone https://github.com/YOUR_USERNAME/qwen-asr-translate.git
cd qwen-asr-translate
```

**或直接解壓縮已下載的專案資料夾**

---

## 步驟 3: 建立虛擬環境

開啟命令提示字元或 PowerShell:

```bash
cd C:\Users\sammi_hung\lobsterai\project\qwen-asr-translate
python -m venv venv
```

這會在 `venv/` 資料夾中建立獨立的 Python 環境。

---

## 步驟 4: 啟動虛擬環境

### Windows CMD/PowerShell:
```bash
venv\Scripts\activate
```

成功啟動後，命令列前方會出現 `(venv)` 標記。

---

## 步驟 5: 安裝依賴套件

確保虛擬環境已啟動（看到 `(venv)`），然後執行:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

這會安裝所有必要的套件，包括:
- customtkinter (GUI)
- openvino (AI 推理)
- onnxruntime (VAD)
- pyaudio (錄音)
- librosa, soundfile (音訊處理)
- transformers (翻譯)
- 等等...

**安裝時間**: 約 5-15 分鐘（視網路速度）

---

## 步驟 6: 下載 AI 模型

### 方法 A: 使用互動式下載器（推薦）
```bash
python downloader.py
```

選擇 `0` 下載所有必需模型（約 1.2 GB）

### 方法 B: 執行批次檔
雙擊 `download-models.bat`

### 方法 C: 手動下載
1. 前往 [HuggingFace](https://huggingface.co/dseditor/Qwen3-ASR-0.6B-INT8_ASYM-OpenVINO)
2. 下載模型檔案到 `ov_models/qwen3_asr_int8/`

---

## 步驟 7: 檢查系統環境

執行檢查腳本:

```bash
python setup_checker.py
```

會顯示:
- ✅ Python 版本
- ✅ 已安裝套件
- ✅ 模型檔案
- ✅ 音訊裝置

---

## 步驟 8: 啟動程式

### CPU 模式（一般使用）
```bash
python app.py
```

或雙擊 `start.bat`

### GPU 模式（需要 NVIDIA/AMD/Intel GPU）
```bash
python app_gpu.py
```

或雙擊 `start-gpu.bat`

---

## 介面說明

### 即時轉換分頁
```
┌─────────────────────────────────────────┐
│ 🎤 音訊輸入裝置：[預設麥克風 ▼] [🔄]   │
│ 🌐 辨識語言：[auto ▼] 翻譯：[en ▼]     │
│                                         │
│        [▶ 開始錄音]                     │
│        [💾 儲存 SRT]                    │
│                                         │
│ 📝 即時字幕                             │
│ ┌─────────────────────────────────────┐ │
│ 原文：                                │ │
│ [時間戳] 說話內容...                  │ │
│                                       │ │
│ 譯文：                                │ │
│ [時間戳] Translated content...        │ │
└─────────────────────────────────────────┘
```

### 音檔轉字幕分頁
```
┌─────────────────────────────────────────┐
│ 📁 選擇檔案：[未選擇]     [瀏覽...]     │
│ 支援：MP3, WAV, FLAC, MP4, MKV, AVI... │
│                                         │
│ 來源：[auto ▼]  目標：[en ▼]           │
│ ☑ 雙語字幕                             │
│                                         │
│ 進度：[████████░░░░] 50%               │
│                                         │
│        [▶ 開始轉換]                     │
└─────────────────────────────────────────┘
```

### 設定分頁
```
┌─────────────────────────────────────────┐
│ 外觀設定                                │
│ 顏色模式：[Dark ▼]                     │
│                                         │
│ 輸出設定                                │
│ ◉ 繁體中文  ○ 簡體中文                 │
│                                         │
│ 模型設定                                │
│ 模型：[Qwen3-ASR-0.6B INT8 ▼]         │
│ 裝置：◉ CPU  ○ GPU                     │
└─────────────────────────────────────────┘
```

---

## 常見問題與解決方案

### Q1: `python` 不是有效的命令
**解決方案**: 
- 重新安裝 Python，確保勾選 "Add to PATH"
- 或重啟電腦後再試

### Q2: 套件安裝失敗
**錯誤**: `Could not find a version that satisfies the requirement...`

**解決方案**:
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### Q3: PyAudio 安裝失敗
**錯誤**: `error: command 'swig.exe' failed`

**解決方案**:
```bash
pip install pipwin
pipwin install pyaudio
```

### Q4: OpenVINO 安裝失敗
**解決方案**:
```bash
pip install openvino==2023.3.0
pip install openvino-dev==2023.3.0
```

### Q5: 模型下載很慢或失敗
**解決方案**:
- 使用鏡像來源（中國用戶）
- 手動下載後放到對應資料夾
- 檢查網路連線

### Q6: 找不到麥克風
**解決方案**:
- 確認麥克風已連接且為預設裝置
- Windows 設定 → 隱私權 → 麥克風 → 允許應用程式存取
- 重新啟動程式

### Q7: 程式啟動後立即關閉
**解決方案**:
- 使用 CMD 執行 `python app.py` 查看錯誤訊息
- 檢查是否缺少模型檔案
- 確認所有套件已正確安裝

---

## 效能優化建議

### 一般效能
- 使用 0.6B 模型：速度快，準確度足夠
- 關閉其他耗資源應用程式
- 確保足夠 RAM（至少 6GB 可用）

### GPU 加速
- 需要 Vulkan 1.2+ 支援
- 更新顯示卡驅動程式
- 使用 1.7B 模型獲得更好準確度

### 錄音品質
- 使用外接麥克風效果更佳
- 在安靜環境中錄音
- 調整麥克風增益避免過曝

---

## 下一步

安裝完成後:
1. 執行 `python setup_checker.py` 確認一切就緒
2. 執行 `python app.py` 啟動程式
3. 在即時轉換分頁測試麥克風
4. 在音檔轉字幕分頁測試檔案轉換

---

## 技術支援

遇到問題？
1. 查看 [`QUICKSTART.md`](QUICKSTART.md) 快速開始指南
2. 查看 [`ARCHITECTURE.md`](ARCHITECTURE.md) 系統架構說明
3. 查看 [`README.md`](README.md) 專案總覽
4. 執行 `python setup_checker.py` 診斷問題

---

**最後更新**: 2026-03-16  
**版本**: v1.0.0-alpha
