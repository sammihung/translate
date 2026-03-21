# 🔍 錄音按鈕無法使用 - 診斷指南

## 🐛 問題現象

**症狀**: 錄音按鈕（🎤）係灰色嘅，點都撳唔到

**原因**: 錄音按鈕預設係 **disabled** 狀態，只有喺引擎成功初始化之後先會啟用

---

## 🎯 可能原因

### 1. 引擎初始化失敗 (最常見)

**流程**:
```
App 啟動 
  ↓
UI 創建 (按鈕 = disabled)
  ↓
_background_init() 背景載入引擎
  ↓
如果初始化成功 → 啟用按鈕 ✅
如果初始化失敗 → 按鈕保持 disabled ❌
```

**點解會失敗**:
- 缺少依賴包 (e.g., `transformers`, `torch`, `bitsandbytes`)
- GPU 驅動問題
- 模型下載失敗 (網路問題)
- CUDA 版本唔匹配
- 記憶體不足

---

### 2. Controller 連接斷裂

**問題**: `on_record_toggle` 回調無正確連接

**檢查**:
```python
# src/app.py 應該有呢行
self.ui.on_record_toggle: Optional[Callable] = self._on_record_toggle
```

---

### 3. UI 更新執行緒問題

**問題**: `enable_record_button(True)` 喺背景執行緒調用，但係無用 `after(0, ...)`

**修復**:
```python
def enable_record_button(self, enabled: bool):
    def _update():
        self.record_btn.configure(state="normal" if enabled else "disabled")
        self.after(0, _update)  # ✅ 確保喺主執行緒更新
```

---

## 🔧 診斷步驟

### 方法 1: 查看日誌 (推薦)

**步驟**:
1. 啟動 App
2. 等待 30 秒
3. 打開 `logs/qwen_asr_YYYYMMDD.log`
4. 搵呢啲關鍵字:
   - `開始初始化引擎...`
   - `引擎初始化成功` 或 `引擎初始化失敗`
   - `啟用錄音按鈕`

**正常日誌**:
```
[INFO] 開始初始化引擎...
[INFO] 載入 ASR 模型：Qwen/Qwen3-ASR-1.7B
[INFO] 連接 Ollama：http://localhost:11434
[INFO] 引擎初始化成功，啟用錄音按鈕
```

**失敗日誌**:
```
[INFO] 開始初始化引擎...
[ERROR] 模型載入失敗：CUDA out of memory
[ERROR] 引擎初始化失敗 (success=False)
```

---

### 方法 2: 運行診斷腳本

**步驟**:
```powershell
cd C:\Users\sherm\translate\qwen-asr-translate
python test_engine_init.py
```

**預期輸出 (成功)**:
```
============================================================
🔍 QwenASR 引擎初始化測試
============================================================

[1/4] 測試 Audio Manager...
✓ 檢測到 24 個音訊設備
  第一個設備：Microphone (Realtek Audio)

[2/4] 測試 AI Controller...
✓ AI Controller 已創建

[3/4] 測試 App Controller...
✓ App Controller 已創建
  GPU 檢測：True
  GPU VRAM: 8.0 GB

[4/4] 初始化引擎...
  → [LOADING] 載入 ASR 模型...
  → [LOADING] 連接 Ollama...
  → [OK] ASR 模型已就緒
  → [OK] Ollama 已連接

✅ 引擎初始化成功！
  ASR 引擎：True
  翻譯引擎：True
  引擎就緒：True

============================================================
測試完成
============================================================
```

**失敗輸出**:
```
❌ 引擎初始化異常：No module named 'transformers'
  (或者 CUDA error, Out of memory, etc.)
```

---

### 方法 3: 檢查控制台錯誤

**步驟**:
1. 喺 App 啟動嘅命令行窗口查看
2. 搵任何紅色錯誤訊息

**常見錯誤**:
- `ModuleNotFoundError: No module named 'xxx'` → 缺少依賴
- `CUDA out of memory` → 顯存不足
- `Connection refused` → Ollama 無運行
- `404 Not Found` → 模型路徑錯誤

---

## ✅ 修復方案

### 修復 1: 添加詳細日誌 (已完成)

**修改** [`src/app.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/app.py):
```python
def load_engines() -> None:
    """背景載入引擎 - 添加詳細錯誤日誌"""
    try:
        logger.info("開始初始化引擎...")
        success = self.controller.initialize_engines(...)
        
        if success:
            logger.info("引擎初始化成功，啟用錄音按鈕")
            self.ui.enable_record_button(True)
        else:
            logger.error("引擎初始化失敗 (success=False)")
    except Exception as e:
        logger.error(f"引擎初始化異常：{e}", exc_info=True)
```

---

### 修復 2: 檢查依賴

**運行**:
```powershell
cd C:\Users\sherm\translate\qwen-asr-translate
pip install -r requirements.txt
```

**關鍵依賴**:
- `transformers` - ASR 模型
- `torch` + `torchaudio` - 深度學習框架
- `bitsandbytes` - INT8 量化 (NVIDIA GPU)
- `ollama` - 翻譯模型
- `customtkinter` - UI

---

### 修復 3: 啟動 Ollama

**檢查**:
```powershell
ollama ps
```

**如果無運行**:
```powershell
ollama serve
```

**確保模型已拉取**:
```powershell
ollama pull translategemma:4b-it-q4_K_M
```

---

### 修復 4: 手動啟用按鈕 (臨時方案)

**如果你想測試 UI 本身係咪壞咗**:

修改 [`src/ui.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/ui.py):
```python
# 搵到呢行 (大約 220 行)
self.record_btn = ctk.CTkButton(..., state="disabled")

# 改為
self.record_btn = ctk.CTkButton(..., state="normal")
```

**警告**: 咁樣做嘅話，就算引擎無載入好，按鈕都會啟用，可能會導致崩潰。只係用嚟測試 UI！

---

## 📊 快速檢查清單

- [ ] 日誌檔存在 (`logs/qwen_asr_*.log`)
- [ ] 日誌顯示 "引擎初始化成功"
- [ ] Ollama 正在運行 (`ollama ps`)
- [ ] 翻譯模型已拉取 (`ollama pull translategemma:4b-it-q4_K_M`)
- [ ] 依賴包已安裝 (`pip list | findstr torch`)
- [ ] GPU 驅動正常 (NVIDIA Control Panel 開到)
- [ ] 控制台無錯誤訊息

---

## 🎯 下一步

1. **運行診斷腳本**:
   ```powershell
   python test_engine_init.py
   ```

2. **檢查日誌**:
   - 打開最新嘅 `logs/qwen_asr_*.log`
   - 搵 "引擎初始化" 相關訊息

3. **報告錯誤**:
   - 如果見到錯誤訊息，Copy 成個錯誤
   - 檢查係邊個步驟失敗 (ASR / Ollama / 其他)

---

## 💡 常見問題

### Q1: "CUDA out of memory"
**解決**:
- 改用極速版 (`Qwen3-ASR-0.6B`)
- 關閉其他佔用 VRAM 嘅程式
- 使用 CPU 模式 (修改設定)

### Q2: "No module named 'transformers'"
**解決**:
```powershell
pip install transformers torch torchaudio bitsandbytes
```

### Q3: "Connection refused" (Ollama)
**解決**:
```powershell
ollama serve
# 新開一個 terminal
ollama pull translategemma:4b-it-q4_K_M
```

### Q4: 按鈕仍然係灰色
**解決**:
- 檢查日誌有無 "啟用錄音按鈕"
- 如果無 → 引擎初始化失敗
- 如果有 → UI 更新問題 (需要重啟 App)

---

## 📞 需要幫助？

請提供以下資訊:
1. 完整錯誤訊息 (從日誌或控制台)
2. GPU 型號同 VRAM 大小
3. `ollama ps` 輸出
4. `pip list | findstr torch` 輸出
