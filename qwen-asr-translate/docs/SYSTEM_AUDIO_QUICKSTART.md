# 🎵 系統音源功能 - 快速使用指南

## ✅ 已完成的功能

您的 QwenASR 現在支援 **收聽電腦內部聲音**！

### 主要功能

1. **🎵 系統音源收聽**
   - YouTube 影片即時字幕
   - 音樂、Podcast 轉錄
   - 線上課程自動筆記
   - 遊戲實況轉錄

2. **🎤 雙模式支援**
   - 系統音源模式：收聽電腦聲音
   - 麥克風模式：收聽外部聲音

3. **⚡ 即時處理**
   - 自動 VAD 分段
   - 即時 ASR 辨識
   - 即時翻譯
   - 雙語字幕顯示

---

## 🚀 快速開始（3 種方法）

### 方法 1: 立體聲混音 (最簡單，如果有的話)

1. **開啟音效設定**
   - 右鍵點擊工作列喇叭 → 「聲音」
   - 或按 `Win + R` → 輸入 `mmsys.cpl`

2. **啟用立體聲混音**
   - 「錄音」分頁
   - 右鍵空白 → 「顯示停用的裝置」
   - 找到「立體聲混音」→ 右鍵 → 「啟用」
   - 設為預設裝置

3. **在 QwenASR 中使用**
   - 開啟程式
   - 選擇「立體聲混音 🎵 (系統音源)」
   - 開始錄音！

### 方法 2: 一鍵設定精靈 (推薦)

雙擊執行：[`setup-audio.bat`](file:///C:/Users/sammi_hung/lobsterai/project/qwen-asr-translate/setup-audio.bat)

精靈會引導您完成所有步驟！

### 方法 3: 安裝 Virtual Cable (萬一沒有立體聲混音)

1. **下載**: https://vb-audio.com/Cable/
2. **安裝**: 執行 VBCABLE_Setup_x64.exe
3. **重啟電腦**
4. **在 QwenASR 選擇**: CABLE Output

---

## 📋 使用場景

### 場景 1: YouTube 外語影片即時翻譯

```
1. 選擇：🎵 立體聲混音
2. 設定：日文 → 繁體中文
3. 播放 YouTube 影片
4. 即時看到双语字幕！
```

### 場景 2: 線上課程轉錄

```
1. 選擇：🎵 立體聲混音
2. 設定：自動偵測 → 繁體中文
3. 播放課程影片
4. 生成完整字幕檔
```

### 場景 3: 音樂歌詞翻譯

```
1. 選擇：🎵 立體聲混音
2. 設定：英文 → 繁體中文
3. 播放音樂
4. 即時看到歌詞翻譯
```

### 場景 4: 會議錄音 (麥克風)

```
1. 選擇：🎤 麥克風陣列
2. 設定：自動偵測 → 雙語
3. 開始會議
4. 即時轉錄 + 翻譯
```

---

## 🎯 裝置選擇快速指南

在裝置列表中尋找：

| 名稱 | 圖示 | 用途 |
|------|------|------|
| 立體聲混音 | 🎵 | 收聽電腦聲音（推薦） |
| Stereo Mix | 🎵 | 收聽電腦聲音（英文系統） |
| CABLE Output | 🎵 | 虛擬音源（需安裝） |
| VoiceMeeter Output | 🎵 | 混音器輸出（進階） |
| 麥克風陣列 | 🎤 | 收聽說話（預設） |
| Microphone | 🎤 | 外接麥克風 |

---

## ⚙️ 使用步驟

### 在 QwenASR 中使用系統音源

1. **啟動程式**
   ```bash
   python app.py
   ```
   或雙擊 `start.bat`

2. **選擇裝置**
   - 在下拉選單選擇帶 🎵 圖示的裝置
   - 如：「立體聲混音 🎵 (系統音源)」

3. **設定語言**
   - 辨識語言：自動偵測 或 指定語言
   - 翻譯目標：英文、繁體中文等

4. **開始錄音**
   - 點擊「▶ 開始錄音」
   - 播放電腦聲音（YouTube、音樂等）
   - 即時看到辨識和翻譯結果！

5. **儲存結果**
   - 點擊「💾 儲存 SRT」
   - 選擇儲存位置
   - 完成！

---

## 🔧 故障排除

### ❌ 找不到「立體聲混音」

**解決方案 1**: 啟用隱藏裝置
1. 右鍵喇叭 → 聲音
2. 「錄音」分頁
3. 右鍵空白 → 「顯示停用的裝置」
4. 應該就會出現了

**解決方案 2**: 安裝 Virtual Cable
1. 執行 `setup-audio.bat`
2. 選擇選項 2
3. 下載並安裝
4. 重啟電腦

### ❌ 有裝置但無反應

**檢查清單**:
- [ ] 裝置是否已設為「預設裝置」？
- [ ] 系統音量是否開啟？
- [ ] 是否在播放聲音？
- [ ] 是否選擇正確的裝置？

**測試步驟**:
1. 選擇裝置
2. 點擊「▶ 開始錄音」
3. 播放音樂
4. 觀察音量條是否跳動

### ❌ 辨識結果不準確

**改善方法**:
- 確保音源清晰（無背景噪音）
- 調整音量到適中（70-80%）
- 使用 1.7B 模型（如有 GPU）
- 指定正確的辨識語言

---

## 📚 相關文件

| 文件 | 說明 |
|------|------|
| [`SYSTEM_AUDIO_GUIDE.md`](file:///C:/Users/sammi_hung/lobsterai/project/qwen-asr-translate/SYSTEM_AUDIO_GUIDE.md) | 完整系統音源設定指南 |
| [`AUDIO_DEVICES_GUIDE.md`](file:///C:/Users/sammi_hung/lobsterai/project/qwen-asr-translate/AUDIO_DEVICES_GUIDE.md) | 音訊裝置選擇指南 |
| [`setup-audio.bat`](file:///C:/Users/sammi_hung/lobsterai/project/qwen-asr-translate/setup-audio.bat) | 快速設定精靈 |
| [`GET_STARTED.md`](file:///C:/Users/sammi_hung/lobsterai/project/qwen-asr-translate/GET_STARTED.md) | 從這裡開始 |
| [`INSTALL_GUIDE.md`](file:///C:/Users/sammi_hung/lobsterai/project/qwen-asr-translate/INSTALL_GUIDE.md) | 安裝指南 |

---

## 💡 使用技巧

### 降低延遲
- 使用立體聲混音（延遲最低）
- 取樣率設為 48000Hz
- 關閉其他音訊軟體

### 提升準確度
- 確保音源清晰
- 音量適中（避免爆音）
- 使用高階模型（1.7B）

### 同時收聽麥克風 + 系統音
- 安裝 VoiceMeeter
- 混合兩種音源
- 調整音量平衡

---

## 🎉 應用場景

### 語言學習
- YouTube 教學影片即時字幕
- Netflix 影集學習對話
- 外文歌曲歌詞翻譯

### 工作效率
- 線上會議自動轉錄
- 網路課程筆記生成
- Podcast 逐字稿製作

### 內容創作
- 遊戲實況即時字幕
- 影片翻譯批量處理
- 直播內容存檔

---

## ⚠️ 注意事項

### 法律與道德
- ✅ 個人使用：允許
- ✅ 教育用途：允許
- ⚠️ 商業用途：注意版權

### 禁止行為
- ❌ 盜錄付費內容散播
- ❌ 侵犯版權的商業利用
- ❌ 未經授權的公開傳播

---

## 🙋 需要協助？

1. **執行設定精靈**
   ```bash
   setup-audio.bat
   ```

2. **查看完整指南**
   - [`SYSTEM_AUDIO_GUIDE.md`](file:///C:/Users/sammi_hung/lobsterai/project/qwen-asr-translate/SYSTEM_AUDIO_GUIDE.md)

3. **檢查環境**
   ```bash
   python setup_checker.py
   ```

4. **在程式中求助**
   - 點擊「❓ 系統音源設定」按鈕

---

**最後更新**: 2026-03-16  
**版本**: v1.0.0-alpha

🎉 **享受即時語音辨識與翻譯的樂趣！**
