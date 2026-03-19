# 🚨 無法打開程式？請依照以下步驟修復！

## 問題診斷

您提到無法打開應用程式。 most likely 原因是 **Python 未安裝**。

---

## ✅ 完整解決方案（3 步驟）

### 步驟 1: 安裝 Python

**為什麼需要？** QwenASR 使用 Python 編寫，必須先安裝 Python 才能執行。

**安裝步驟**:

```
1. 開啟瀏覽器
2. 前往：https://www.python.org/downloads/
3. 下載 Python 3.12 (最新版本)
4. 執行下載的安裝檔
5. ⚠️ 重要：勾選 "Add Python to PATH"
6. 點擊 "Install Now"
7. 等待安裝完成（約 2-5 分鐘）
8. 重啟電腦
```

**驗證安裝**:
開啟命令提示字元（CMD），輸入：
```
python --version
```
應該顯示：`Python 3.12.x`

---

### 步驟 2: 一鍵安裝 QwenASR

Python 安裝完成後：

```
雙擊執行：INSTALL.bat
```

這個腳本會自動：
- ✅ 檢查 Python
- ✅ 建立 `.venv` 虛擬環境
- ✅ 安裝所有依賴套件
- ✅ 啟動應用程式

**安裝時間**: 約 5-15 分鐘

---

### 步驟 3: 開始使用

安裝完成後會自動啟動，或者：

```
雙擊執行：quick-start.bat
```

---

## 🔧 其他解決方案

### 方案 A: 自動檢查與修復

**雙擊執行**: [`INSTALL.bat`](INSTALL.bat)

這個腳本會：
1. 自動檢查 Python 是否安裝
2. 自動檢查版本是否符合
3. 自動安裝依賴套件
4. 自動啟動應用程式

---

### 方案 B: 手動檢查

**雙擊執行**: [`LAUNCH.bat`](LAUNCH.bat)

這個腳本會：
1. 檢查 Python 是否已安裝
2. 檢查虛擬環境是否存在
3. 啟動應用程式
4. 提供詳細錯誤訊息

---

## 📋 快速參考

| 檔案 | 用途 |
|------|------|
| [`INSTALL.bat`](INSTALL.bat) | **首次安裝用**（會檢查 Python） |
| [`LAUNCH.bat`](LAUNCH.bat) | 啟動並檢查錯誤 |
| [`quick-start.bat`](quick-start.bat) | 快速啟動（已安裝後） |
| [`setup-audio.bat`](setup-audio.bat) | 設定系統音源 |

---

## ❓ 常見問題

### Q: 雙擊腳本後沒反應？
**A**: Python 未安裝
- 解法：執行 `INSTALL.bat` 會自動引導

### Q: 顯示 "python 不是有效的命令"？
**A**: Python 未安裝或未加入 PATH
- 解法：重新安裝 Python，勾選 "Add Python to PATH"

### Q: 安裝套件時出錯？
**A**: 網路問題或相容性問題
- 解法：執行 `SETUP_WIZARD.bat` 會自動修復

### Q: 找不到立體聲混音？
**A**: 電腦沒有此功能
- 解法：執行 `setup-audio.bat` 安裝 Virtual Cable

---

## 🎯 完整安裝流程圖

```
開始
  │
  ├─→ 安裝 Python 3.12
  │   (https://www.python.org/downloads/)
  │
  ├─→ 重啟電腦
  │
  ├─→ 雙擊 INSTALL.bat
  │   (自動檢查 + 安裝)
  │
  ├─→ 等待安裝完成
  │   (5-15 分鐘)
  │
  └─→ 應用程式自動啟動 ✅
```

---

## 📞 需要更多協助？

1. **查看完整指南**: [`ONE_CLICK_GUIDE.md`](ONE_CLICK_GUIDE.md)
2. **檢查環境**: 執行 `python setup_checker.py`
3. **查看錯誤**: 執行 `LAUNCH.bat` 會顯示詳細錯誤

---

## 🎉 完成後

安裝成功後，您會看到 QwenASR 的視窗：
- 選擇音訊裝置（麥克風或立體聲混音）
- 設定語言
- 點擊「▶ 開始錄音」
- 享受即時語音辨識與翻譯！

---

**立即開始**: 雙擊 [`INSTALL.bat`](INSTALL.bat)
