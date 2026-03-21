"""
效能模式選擇器 UI 組件
提供三階段效能分級的可视化選擇介面
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
from model_registry import (
    PerformanceMode,
    get_all_tiers,
    get_tier_by_display_name,
    PERFORMANCE_TIERS
)
from logging_config import get_logger

logger = get_logger(__name__)


class PerformanceModeSelector(ctk.CTkFrame):
    """效能模式選擇器組件"""
    
    def __init__(
        self,
        master,
        on_mode_change: Optional[Callable[[PerformanceMode], None]] = None,
        **kwargs
    ) -> None:
        super().__init__(master, **kwargs)
        
        self.on_mode_change = on_mode_change
        self.current_mode: PerformanceMode = PerformanceMode.BALANCED
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """創建 UI 組件"""
        # 標題
        title_label = ctk.CTkLabel(
            self,
            text="⚡ 效能模式設定",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        title_label.pack(fill="x", padx=15, pady=(15, 10))
        
        # 說明文字
        desc_label = ctk.CTkLabel(
            self,
            text="根據您的硬體配置選擇合適的效能模式",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            anchor="w"
        )
        desc_label.pack(fill="x", padx=15, pady=(0, 15))
        
        # 創建三個模式的按鈕
        self.mode_buttons = {}
        
        for tier in get_all_tiers():
            button_frame = self._create_mode_button(tier)
            button_frame.pack(fill="x", padx=15, pady=5)
    
    def _create_mode_button(self, tier) -> ctk.CTkFrame:
        """創建單個模式按鈕"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        
        # 按鈕
        button = ctk.CTkButton(
            frame,
            text=f"{tier.icon} {tier.display_name}",
            font=ctk.CTkFont(size=14),
            height=45,
            corner_radius=10,
            fg_color="#1e293b",
            hover_color="#334155",
            anchor="w",
            command=lambda m=tier.mode: self._on_button_click(m)
        )
        button.pack(side="left", fill="x", expand=True, padx=0, pady=0)
        
        # 描述
        desc_label = ctk.CTkLabel(
            frame,
            text=tier.target_audience,
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            anchor="w",
            width=200
        )
        desc_label.pack(side="left", padx=15)
        
        self.mode_buttons[tier.mode] = button
        
        return frame
    
    def _on_button_click(self, mode: PerformanceMode) -> None:
        """按鈕點擊事件"""
        if self.current_mode == mode:
            return
        
        self.current_mode = mode
        tier = PERFORMANCE_TIERS[mode]
        
        # 更新所有按鈕的外觀
        self._update_button_appearance()
        
        logger.info(f"使用者選擇效能模式：{tier.display_name}")
        
        # 觸發回調
        if self.on_mode_change:
            try:
                self.on_mode_change(mode)
            except Exception as e:
                logger.error(f"效能模式切換失敗：{e}", exc_info=True)
                messagebox.showerror(
                    "錯誤",
                    f"切換效能模式失敗：{str(e)}\n\n請重啟應用程式以套用新設定。"
                )
    
    def _update_button_appearance(self) -> None:
        """更新按鈕外觀 (選中/未選中)"""
        for mode, button in self.mode_buttons.items():
            if mode == self.current_mode:
                # 選中狀態
                button.configure(
                    fg_color="#3b82f6",
                    hover_color="#2563eb"
                )
            else:
                # 未選中狀態
                button.configure(
                    fg_color="#1e293b",
                    hover_color="#334155"
                )
    
    def set_mode(self, mode: PerformanceMode) -> None:
        """外部設定效能模式"""
        if self.current_mode != mode:
            self.current_mode = mode
            self._update_button_appearance()
    
    def get_mode(self) -> PerformanceMode:
        """獲取當前效能模式"""
        return self.current_mode


class PerformanceModeDialog(ctk.CTkToplevel):
    """效能模式設定對話框"""
    
    def __init__(
        self,
        master,
        current_mode: PerformanceMode = PerformanceMode.BALANCED,
        on_save: Optional[Callable[[PerformanceMode], None]] = None
    ) -> None:
        super().__init__(master)
        
        self.title("效能模式設定")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # 置中顯示
        self.transient(master)
        self.grab_set()
        
        self.current_mode = current_mode
        self.on_save = on_save
        
        self._create_ui()
    
    def _create_ui(self) -> None:
        """創建對話框 UI"""
        # 主容器
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 標題
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎯 選擇效能模式",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 10))
        
        # 說明文字
        desc_text = (
            "根據您的硬體配置選擇合適的效能模式。\n"
            "切換後需要重新載入模型，可能會耗時數分鐘。"
        )
        desc_label = ctk.CTkLabel(
            main_frame,
            text=desc_text,
            font=ctk.CTkFont(size=13),
            text_color="#94a3b8",
            anchor="w",
            justify="left"
        )
        desc_label.pack(fill="x", pady=(0, 20))
        
        # 效能模式選擇器
        self.selector = PerformanceModeSelector(
            main_frame,
            on_mode_change=lambda m: setattr(self, 'current_mode', m)
        )
        self.selector.pack(fill="both", expand=True, pady=(0, 20))
        
        # 設定為當前模式
        self.selector.set_mode(self.current_mode)
        
        # 按鈕區域
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # 取消按鈕
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            font=ctk.CTkFont(size=14),
            width=100,
            height=40,
            fg_color="transparent",
            border_width=2,
            border_color="#475569",
            hover_color="#334155",
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        # 儲存按鈕
        save_btn = ctk.CTkButton(
            button_frame,
            text="儲存並套用",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=120,
            height=40,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self._on_save
        )
        save_btn.pack(side="right")
        
        # 技術說明連結
        tech_info_btn = ctk.CTkButton(
            main_frame,
            text="📖 查看技術說明",
            font=ctk.CTkFont(size=12),
            height=35,
            fg_color="transparent",
            border_width=1,
            border_color="#475569",
            hover_color="#1e293b",
            command=self._show_tech_info
        )
        tech_info_btn.pack(fill="x", pady=(10, 0))
    
    def _on_save(self) -> None:
        """儲存按鈕點擊"""
        if self.on_save:
            try:
                self.on_save(self.current_mode)
                logger.info(f"效能模式已儲存：{self.current_mode.value}")
            except Exception as e:
                logger.error(f"儲存效能模式失敗：{e}", exc_info=True)
                messagebox.showerror("錯誤", f"儲存失敗：{str(e)}")
                return
        
        self.destroy()
    
    def _show_tech_info(self) -> None:
        """顯示技術說明"""
        from model_registry import TECHNICAL_NOTES
        
        # 創建技術說明視窗
        info_window = ctk.CTkToplevel(self)
        info_window.title("📖 技術說明")
        info_window.geometry("700x500")
        info_window.resizable(True, True)
        
        # 文字區域
        text_box = ctk.CTkTextbox(
            info_window,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word"
        )
        text_box.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 插入內容
        text_box.insert("0.0", TECHNICAL_NOTES)
        text_box.configure(state="disabled")  # 只讀


# ============================================
# 使用範例
# ============================================

if __name__ == "__main__":
    # 測試程式碼
    app = ctk.CTk()
    app.geometry("600x400")
    
    def on_mode_change(mode: PerformanceMode):
        print(f"效能模式切換至：{mode.value}")
    
    selector = PerformanceModeSelector(
        app,
        on_mode_change=on_mode_change
    )
    selector.pack(fill="both", expand=True, padx=20, pady=20)
    
    app.mainloop()
