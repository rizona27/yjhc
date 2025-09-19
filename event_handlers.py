# event_handlers.py
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from utils import normalize_date_string

class EventHandlers:
    def __init__(self, app):
        self.app = app
        self.config = app.config
        self.error_window = None  # 添加错误窗口引用

    def on_start_focus_in(self, event):
        # 检查输入框是否被禁用
        if self.app.components["start_entry"].cget('state') == 'disabled':
            return
        if self.app.components["start_entry"].get() == "YYYY-MM-DD":
            self.app.components["start_entry"].delete(0, tk.END)
            self.app.components["start_entry"].configure(foreground=self.config.colors["text"])

    def on_start_focus_out(self, event):
        # 检查输入框是否被禁用
        if self.app.components["start_entry"].cget('state') == 'disabled':
            return
        self._validate_dates(self.app.components["start_entry"])

    def on_start_return(self, event):
        # 检查输入框是否被禁用
        if self.app.components["start_entry"].cget('state') == 'disabled':
            return
        if self._validate_dates(self.app.components["start_entry"]):
            if self.app.components["end_entry"].get() and self.app.components["end_entry"].get() != "YYYY-MM-DD":
                self.app.custom_analysis()
            else:
                self.app.components["end_entry"].focus()
                self.app.components["end_entry"].select_range(0, tk.END)

    def on_end_focus_in(self, event):
        # 检查输入框是否被禁用
        if self.app.components["end_entry"].cget('state') == 'disabled':
            return
        if self.app.components["end_entry"].get() == "YYYY-MM-DD":
            self.app.components["end_entry"].delete(0, tk.END)
            self.app.components["end_entry"].configure(foreground=self.config.colors["text"])

    def on_end_focus_out(self, event):
        # 检查输入框是否被禁用
        if self.app.components["end_entry"].cget('state') == 'disabled':
            return
        self._validate_dates(self.app.components["end_entry"])

    def on_end_return(self, event):
        # 检查输入框是否被禁用
        if self.app.components["end_entry"].cget('state') == 'disabled':
            return
        if self._validate_dates(self.app.components["end_entry"]):
            if (self.app.components["start_entry"].get() and self.app.components["start_entry"].get() != "YYYY-MM-DD" and
                self.app.components["end_entry"].get() and self.app.components["end_entry"].get() != "YYYY-MM-DD"):
                self.app.custom_analysis()
            else:
                self.app.components["start_entry"].focus()
                self.app.components["start_entry"].select_range(0, tk.END)

    def _validate_dates(self, entry):
        date_str = entry.get()
        if date_str == "YYYY-MM-DD" or not date_str:
            entry.configure(foreground=self.config.colors["placeholder"])
            return False

        try:
            # 首先检查是否包含非数字字符（除了连字符）
            if any(c not in '0123456789-' for c in date_str.replace('-', '')):
                raise ValueError("日期包含非数字字符")
                
            normalized_date = normalize_date_string(date_str, self.app.log)
            datetime.strptime(normalized_date, "%Y-%m-%d")
            entry.delete(0, tk.END)
            entry.insert(0, normalized_date)
            entry.configure(foreground=self.config.colors["text"])
            self.app.log(f"日期 '{date_str}' 格式校验通过。", "success")
            return True
        except ValueError as e:
            # 如果已经有一个错误窗口打开，先关闭它
            if self.error_window and self.error_window.winfo_exists():
                self.error_window.destroy()
                
            # 居中显示错误提示 - 修改为200x130大小
            self.error_window = tk.Toplevel(self.app.root)
            self.error_window.title("日期格式错误")
            self.error_window.geometry("200x130")  
            self.error_window.resizable(False, False)
            self.error_window.transient(self.app.root)
            self.error_window.grab_set()
            self.error_window.configure(bg=self.config.colors["background"])
            
            # 居中显示错误窗口
            self.app.center_window_relative(self.error_window, self.app.root)
            
            # 修改这里：使用 ttk.Frame 替代 tk.Frame
            main_frame = ttk.Frame(self.error_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            error_msg = f"无效的日期格式: '{date_str}'。请使用 YYYY-MM-DD 或 YYYYMMDD 格式。"
            if str(e) != "日期包含非数字字符":
                error_msg = f"无效的日期格式: '{date_str}'。{str(e)}"
                
            ttk.Label(main_frame, text=error_msg, 
                    wraplength=180, justify=tk.LEFT).pack(pady=10)  # 设置换行宽度
            
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(pady=10)
            
            ttk.Button(btn_frame, text="确定", command=self.error_window.destroy, width=10).pack()
            
            # 绑定窗口关闭事件，确保窗口被销毁时更新引用
            self.error_window.protocol("WM_DELETE_WINDOW", self.error_window.destroy)
            
            entry.configure(foreground="red")
            self.app.log(f"日期 '{date_str}' 格式校验失败: {str(e)}", "error")
            return False
        except Exception as e:
            # 如果已经有一个错误窗口打开，先关闭它
            if self.error_window and self.error_window.winfo_exists():
                self.error_window.destroy()
                
            # 居中显示错误提示 - 修改为200x130大小
            self.error_window = tk.Toplevel(self.app.root)
            self.error_window.title("日期格式错误")
            self.error_window.geometry("200x130")  # 修改为200x130
            self.error_window.resizable(False, False)
            self.error_window.transient(self.app.root)
            self.error_window.grab_set()
            self.error_window.configure(bg=self.config.colors["background"])
            
            # 居中显示错误窗口
            self.app.center_window_relative(self.error_window, self.app.root)
            
            # 修改这里：使用 ttk.Frame 替代 tk.Frame
            main_frame = ttk.Frame(self.error_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(main_frame, text=f"日期处理出错: {str(e)}", 
                    wraplength=180, justify=tk.LEFT).pack(pady=10)  # 设置换行宽度
            
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(pady=10)
            
            ttk.Button(btn_frame, text="确定", command=self.error_window.destroy, width=10).pack()
            
            # 绑定窗口关闭事件，确保窗口被销毁时更新引用
            self.error_window.protocol("WM_DELETE_WINDOW", self.error_window.destroy)
            
            self.app.log(f"日期处理出错: {str(e)}", "error")
            return False