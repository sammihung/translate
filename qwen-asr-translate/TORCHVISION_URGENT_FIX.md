# 🔧 TORCHVISION_URGENT_FIX.md - 緊急修復報告

## 📊 問題診斷

### 核心錯誤
```
[WARN] Speaker Diarization load failed: partially initialized module 
'torchvision' has no attribute 'extension' (most likely due to a circular import)
```

### 實際測試結果 (20:43)
**已驗證功能**:
- ✅ UI 正常啟動
- ✅ VAD 語音檢測正常 (每 8 秒偵測到 1 個語音段落)
- ✅ 錄音流正常運作 (6000Hz, Mono, RMS 150.0)
- ❌ **ASR 模型載入失敗** (無日誌顯示 ASR 成功載入)
- ❌ **無辨識結果** (VAD 偵測到語音但無 ASR 輸出)
- ❌ **UI 無顯示** (因為無 ASR 結果)

### 根本原因
1. `torchvision` 套件損壞或版本不匹配
2. `torchvision::nms does not exist` 導致 ASR 載入失敗
3. ASR 失敗導致後續翻譯流程完全無法執行

---

## 🛠️ 已實施修復

### 修復 1: 更新 requirements.txt
**檔案**: [`requirements.txt`](file:///C:/Users/sherm/translate/qwen-asr-translate/requirements.txt)

**新增**:
```text
torchvision>=0.15.0
```

### 修復 2: 更新 pyproject.toml
**檔案**: [`pyproject.toml`](file:///C:/Users/sherm/translate/qwen-asr-translate/pyproject.toml)

**新增**:
```toml
dependencies = [
    "torchvision>=0.15.0",
]
```

### 修復 3: 源代碼預防措施
**檔案**: [`src/asr_engine.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/asr_engine.py) (第 35 行)

**已實施**:
```python
def load_pipeline(self) -> None:
    try:
        # 🔧 FIX: 強製提早完整載入 torchvision
        import torchvision
        
        from pyannote.audio import Pipeline
        # ...
```

---

## ⚠️ 需要用戶手動執行的步驟

由於虛擬環境 (`C:\Users\sherm\translate\qwen-asr-translate\.venv`) 的 pip 模組損壞，**無法自動執行重裝**，請按照以下步驟手動修復：

### 第一步：關閉正在運行的應用程式
如果 `main.py` 仍在運行，請按 `Ctrl+C` 停止

### 第二步：激活虛擬環境
```powershell
cd C:\Users\sherm\translate\qwen-asr-translate
.venv\Scripts\Activate.ps1
```

*(如果出現權限錯誤，請執行：`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

### 第三步：檢查 pip 是否可用
```powershell
python -m pip --version
```

如果顯示 `No module named pip`，需要先修復 pip：
```powershell
python -m ensurepip --upgrade
```

### 第四步：卸載舊版本
```powershell
pip uninstall -y torch torchvision torchaudio
```

### 第五步：清除緩存
```powershell
pip cache purge
```

### 第六步：重新安裝 CUDA 12.1 版本
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**預計耗時**: 5-10 分鐘 (取決於網絡速度)
**下載大小**: ~2GB

### 第七步：驗證安裝
```powershell
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
python -c "import torchvision; print(f'torchvision version: {torchvision.__version__}')"
```

**預期輸出**:
```
CUDA Available: True
torchvision version: 0.15.x 或更高
```

### 第八步：重新啟動應用程式
```powershell
python main.py
```

---

## 📊 驗證清單

啟動後請檢查以下日誌：

### ✅ 成功標誌
```
GPU detected!
GPU Available: True
🚀 Loading ASR: Qwen/Qwen3-ASR-1.7B on cuda...
[OK] ASR loaded on cuda (INT8: True), VRAM cleared
[OK] Speaker Diarization loaded
引擎初始化成功，啟用錄音按鈕
```

### ❌ 失敗標誌 (需要繼續修復)
```
GPU Available: False
[WARN] Speaker Diarization load failed: ...
[ERROR] ASR Load Failed: ...
```

---

## 🎯 替代方案 (如果 pip 完全損壞)

如果 `.venv` 完全損壞，建議重新創建虛擬環境：

### 方案 A: 使用 uv (推薦，快速)
```powershell
# 安裝 uv
pip install uv

# 刪除舊環境
Remove-Item -Recurse -Force .venv

# 創建新環境 (Python 3.11)
uv venv --python 3.11

# 激活環境
.venv\Scripts\Activate.ps1

# 安裝依賴 (包含 CUDA 版本)
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
uv pip install -e .
```

### 方案 B: 使用標準 venv
```powershell
# 刪除舊環境
Remove-Item -Recurse -Force .venv

# 創建新環境
python -m venv .venv

# 激活環境
.venv\Scripts\Activate.ps1

# 升級 pip
python -m pip install --upgrade pip

# 安裝 CUDA 版本
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 安裝項目依賴
pip install -e .
```

---

## 📸 螢幕截圖驗證

重新啟動後，請驗證以下內容：

1. **UI 正常顯示**
   - 主窗口出現
   - 錄音按鈕可用 (唔係灰色)
   - 設備下拉選單有內容

2. **錄音測試**
   - 點擊錄音按鈕
   - 顯示 "LISTENING..."
   - 對著麥克風講嘢

3. **ASR 辨識**
   - 講完後 UI 顯示聊天氣泡
   - 氣泡包含原文同譯文

4. **日誌驗證**
   - 檢查 `logs/qwen_asr_YYYYMMDD.log`
   - 確認無 `[ERROR] ASR Load Failed`

---

## 🎉 預期結果

修復成功後，完整工作流程：

```
1. 啟動應用程式
   → GPU detected! ✅
   → ASR loaded on cuda ✅
   
2. 點擊錄音
   → 錄音流啟動 ✅
   
3. 對著麥克風講嘢
   → VAD 偵測語音 ✅
   → ASR 辨識文字 ✅
   → UI 顯示氣泡 ✅
   → Batching 收集 ✅
   → 批量翻譯 ✅
   → 更新氣泡內容 ✅
```

---

## 📁 已修改檔案

1. **[`requirements.txt`](file:///C:/Users/sherm/translate/qwen-asr-translate/requirements.txt)** - 新增 torchvision>=0.15.0
2. **[`pyproject.toml`](file:///C:/Users/sherm/translate/qwen-asr-translate/pyproject.toml)** - 新增 torchvision>=0.15.0
3. **[`src/asr_engine.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/asr_engine.py)** - 已實施 torchvision 提早載入
4. **[`src/ui.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/ui.py)** - 已修復 UI 氣泡顯示
5. **[`FINAL_FIXES_COMPLETE.md`](file:///C:/Users/sherm/translate/qwen-asr-translate/FINAL_FIXES_COMPLETE.md)** - 修復文檔

---

## ⏱️ 預估修復時間

| 步驟 | 預計時間 |
|------|----------|
| 卸載舊版本 | 30 秒 |
| 清除緩存 | 10 秒 |
| 下載新版本 | 3-8 分鐘 (取決於網絡) |
| 安裝新版本 | 2-3 分鐘 |
| 驗證 + 測試 | 2 分鐘 |
| **總計** | **8-15 分鐘** |

---

## 🚨 重要提醒

**必須執行手動修復步驟**，因為：
1. 虛擬環境的 pip 模組損壞
2. 需要重新安裝 CUDA 版本的 PyTorch
3. 自動修復無法完成

**請按照「需要用戶手動執行的步驟」逐步行事**，如果遇到任何問題，請提供：
- 錯誤訊息截圖
- `python --version` 輸出
- `pip --version` 輸出
- 最新日誌檔 (`logs/qwen_asr_*.log`)

**多謝合作！修復後個 App 就可以完美運作！** 👏
