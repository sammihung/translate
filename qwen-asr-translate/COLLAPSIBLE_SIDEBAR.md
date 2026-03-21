# 🎨 可折疊側邊欄 (Collapsible Sidebar)

## 概述

為咗提升用戶體驗同節省螢幕空間，我哋為 CustomTkinter UI 實現咗一個專業級嘅可折疊側邊欄功能。用戶可以通過點擊「漢堡選單」按鈕來展開或收起側邊欄。

---

## ✨ 功能特點

### 1. 一鍵切換
- 點擊側邊欄頂部嘅 **☰ (漢堡選單)** 按鈕即可切換展開/收起狀態
- 展開時寬度：**200px**
- 收起時寬度：**60px**

### 2. 智能顯示
- **展開狀態**: 顯示完整文字 (例如：`⚡ 即時翻譯`)
- **收起狀態**: 只顯示 Icon (例如：`⚡`)

### 3. 狀態保持
- 側邊欄狀態會喺會話期間保持
- 切換視圖唔會影響側邊欄狀態

---

## 🛠️ 實作細節

### 核心組件

#### 1. 狀態變數

```python
self.menu_expanded: bool = True  # 預設展開
self.EXPANDED_WIDTH = 200        # 展開寬度
self.COLLAPSED_WIDTH = 60        # 收起寬度
```

#### 2. 漢堡按鈕

```python
self.toggle_btn = ctk.CTkButton(
    header_frame,
    text="☰",
    width=40,
    height=40,
    corner_radius=8,
    fg_color="transparent",
    hover_color=self.colors["bg_panel"],
    command=self.toggle_menu,
    font=ctk.CTkFont(size=18)
)
```

#### 3. 切換邏輯

```python
def toggle_menu(self) -> None:
    """切換側邊欄的展開/收起狀態"""
    self.menu_expanded = not self.menu_expanded
    
    if self.menu_expanded:
        # 展開狀態
        self.sidebar.configure(width=self.EXPANDED_WIDTH)
        self.toggle_btn.configure(text="☰")
        self.logo_label.grid()  # 顯示 Logo
        
        # 顯示按鈕文字
        for view_id, btn in self.nav_buttons.items():
            icon = self.nav_text_labels[view_id]["icon"]
            text = self.nav_text_labels[view_id]["text"]
            btn.configure(text=f"{icon}  {text}")
        
        # 顯示狀態文字
        self.status_indicator.configure(text="🟢 系統就緒")
        
    else:
        # 縮小狀態
        self.sidebar.configure(width=self.COLLAPSED_WIDTH)
        self.toggle_btn.configure(text="≡")
        self.logo_label.grid_remove()  # 隱藏 Logo
        
        # 只顯示 Icon
        for view_id, btn in self.nav_buttons.items():
            icon = self.nav_text_labels[view_id]["icon"]
            btn.configure(text=icon)
        
        # 隱藏狀態文字
        self.status_indicator.configure(text="🟢")
```

---

## 📊 UI 對比

### 展開狀態 (200px)
```
┌─────────────────────┐
│ ☰  🌊 QwenASR       │
├─────────────────────┤
│ ⚡  即時翻譯         │
│ 📁  批量上傳         │
│ ⚙️  系統設定         │
├─────────────────────┤
│ 🟢 系統就緒         │
└─────────────────────┘
```

### 收起狀態 (60px)
```
┌──────┐
│ ≡    │
├──────┤
│ ⚡   │
│ 📁   │
│ ⚙️   │
├──────┤
│ 🟢   │
└──────┘
```

---

## 🎯 使用場景

### 適合展開側邊欄的情況:
- ✅ 第一次使用，需要熟悉功能
- ✅ 需要查看完整功能名稱
- ✅ 螢幕空間充足 (外接顯示器)
- ✅ 桌面環境使用

### 適合收起側邊欄的情況:
- ✅ 螢幕空間有限 (筆記本電腦)
- ✅ 專注於主要工作區域
- ✅ 多工處理時
- ✅ 熟悉功能後嘅日常使用

---

## 💡 專業開發者小貼士

### 1. 避免元件撐開問題

CustomTkinter 嘅 Frame 大小會俾裡面嘅元件「撐開」。解決方法：

```python
# ❌ 錯誤做法：只設定 width，但按鈕文字依然好長
self.sidebar.configure(width=60)
# 按鈕文字：`⚡  即時翻譯` (會撐開 Frame)

# ✅ 正確做法：同時修改按鈕文字
self.sidebar.configure(width=60)
btn.configure(text="⚡")  # 只保留 Icon
```

### 2. 使用 `grid_remove()` vs `pack_forget()`

```python
# ✅ 推薦：grid_remove() - 保留 Grid 配置
self.logo_label.grid_remove()  # 之後可以用 grid() 恢復

# ❌ 不推薦：pack_forget() - 丟失 Grid 配置
self.logo_label.pack_forget()  # 需要重新 pack()
```

### 3. 平滑動畫效果 (進階)

如果想實現平滑過渡動畫：

```python
def toggle_menu_animated(self):
    """帶動畫的側邊欄切換 (進階)"""
    if self.menu_expanded:
        # 收起動畫
        target_width = self.COLLAPSED_WIDTH
        step = -10
    else:
        # 展開動畫
        target_width = self.EXPANDED_WIDTH
        step = 10
    
    current_width = self.sidebar.cget("width")
    
    if current_width != target_width:
        new_width = current_width + step
        if (step > 0 and new_width > target_width) or \
           (step < 0 and new_width < target_width):
            new_width = target_width
        
        self.sidebar.configure(width=new_width)
        self.after(5, self.toggle_menu_animated)  # 每 5ms 更新一次
    else:
        # 動畫完成，更新最終狀態
        self.menu_expanded = not self.menu_expanded
        self._update_button_texts()
```

---

## 🔧 自定義配置

### 修改側邊欄寬度

```python
# 喺 ui.py 嘅 __init__ 中修改
self.EXPANDED_WIDTH = 250  # 更寬 (適合長文字)
self.COLLAPSED_WIDTH = 70  # 稍微寬啲 (適合大 Icon)
```

### 修改預設狀態

```python
# 預設收起側邊欄
self.menu_expanded: bool = False
```

### 添加更多導航按鈕

```python
nav_items = [
    ("realtime", "⚡", "即時翻譯"),
    ("batch", "📁", "批量上傳"),
    ("settings", "⚙️", "系統設定"),
    ("history", "📜", "歷史記錄"),      # 新增
    ("analytics", "📊", "數據分析"),    # 新增
]
```

---

## 📁 相關檔案

- [`src/ui.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/ui.py) - UI 主檔案 (已實現)
- [`src/app.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/app.py) - 應用程式入口
- [`src/controller.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/controller.py) - 控制器

---

## 🎨 視覺設計原則

### 1. Icon 選擇
- 使用 **Unicode Emoji** (跨平台兼容)
- 每個功能有獨特且易識別嘅 Icon
- Icon 大小統一 (建議 18-24px)

### 2. 顏色對比
- 展開狀態：文字顏色 `#94a3b8` (text_muted)
- 選中狀態：文字顏色 `#3b82f6` (primary)
- Hover 效果：背景色 `#1e293b` (bg_panel)

### 3. 間距設計
- 按鈕高度：`45px`
- 按鈕間距：`3px`
- 左右邊距：`10px`
- Logo 上邊距：`15px`

---

## ✅ 測試清單

- [x] 點擊漢堡按鈕能正確切換狀態
- [x] 展開時顯示完整文字
- [x] 收起時只顯示 Icon
- [x] Logo 在收起時正確隱藏
- [x] 狀態指示器正確切換顯示
- [x] 切換視圖不影響側邊欄狀態
- [x] 側邊欄不會被內部元件撐開
- [x] 所有按鈕在兩種狀態下都可點擊

---

## 🚀 未來優化建議

### 1. 鍵盤快捷鍵
```python
# 綁定 Ctrl+B 切換側邊欄
self.master.bind("<Control-b>", lambda e: self.toggle_menu())
```

### 2. 狀態持久化
```python
# 保存到配置文件
import json

def save_sidebar_state(self):
    config = {"sidebar_expanded": self.menu_expanded}
    with open("config.json", "w") as f:
        json.dump(config, f)

def load_sidebar_state(self):
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            if not config.get("sidebar_expanded", True):
                self.toggle_menu()
    except FileNotFoundError:
        pass
```

### 3. 響應式設計
```python
# 根據視窗大小自動調整
def on_window_resize(self, event):
    if event.width < 800:
        if self.menu_expanded:
            self.toggle_menu()  # 自動收起
    elif event.width > 1000:
        if not self.menu_expanded:
            self.toggle_menu()  # 自動展開
```

---

## 🎉 總結

可折疊側邊欄功能為用戶提供咗：

✅ **更靈活嘅空間管理** - 根據需要展開或收起  
✅ **更好嘅視覺體驗** - Icon + 文字嘅智能切換  
✅ **更專業嘅介面設計** - 跟隨現代 UI 趨勢  
✅ **更高嘅使用效率** - 快速切換，專注工作  

**呢個功能已經完全整合入 [`src/ui.py`](file:///C:/Users/sherm/translate/qwen-asr-translate/src/ui.py)，即刻可以用！** 🚀
