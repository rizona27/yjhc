# event_handlers.py
import tkinter as tk
from datetime import datetime
from utils import normalize_date_string

class EventHandlers:
    def __init__(self, app):
        self.app = app
        self.config = app.config

    def on_start_focus_in(self, event):
        if self.app.components["start_entry"].get() == "YYYY-MM-DD":
            self.app.components["start_entry"].delete(0, tk.END)
            self.app.components["start_entry"].configure(foreground=self.config.colors["text"])

    def on_start_focus_out(self, event):
        self._validate_dates(self.app.components["start_entry"])

    def on_start_return(self, event):
        if self._validate_dates(self.app.components["start_entry"]):
            if self.app.components["end_entry"].get() and self.app.components["end_entry"].get() != "YYYY-MM-DD":
                self.app.custom_analysis()
            else:
                self.app.components["end_entry"].focus()
                self.app.components["end_entry"].select_range(0, tk.END)

    def on_end_focus_in(self, event):
        if self.app.components["end_entry"].get() == "YYYY-MM-DD":
            self.app.components["end_entry"].delete(0, tk.END)
            self.app.components["end_entry"].configure(foreground=self.config.colors["text"])

    def on_end_focus_out(self, event):
        self._validate_dates(self.app.components["end_entry"])

    def on_end_return(self, event):
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
            normalized_date = normalize_date_string(date_str, self.app.log)
            datetime.strptime(normalized_date, "%Y-%m-%d")
            entry.delete(0, tk.END)
            entry.insert(0, normalized_date)
            entry.configure(foreground=self.config.colors["text"])
            self.app.log(f"日期 '{date_str}' 格式校验通过。", "success")
            return True
        except ValueError:
            # 居中显示错误提示
            error_window = tk.Toplevel(self.app.root)
            error_window.title("日期格式错误")
            error_window.geometry("400x100")
            error_window.resizable(False, False)
            error_window.transient(self.app.root)
            error_window.grab_set()
            
            # 居中显示错误窗口
            self.app.center_window_relative(error_window, self.app.root)
            
            tk.Label(error_window, text=f"无效的日期格式: '{date_str}'。请使用 YYYY-MM-DD 或 YYYYMMDD 格式。", 
                    padx=20, pady=20).pack()
            tk.Button(error_window, text="确定", command=error_window.destroy, width=10).pack(pady=10)
            
            entry.configure(foreground="red")
            self.app.log(f"日期 '{date_str}' 格式校验失败。", "error")
            return False
        except Exception as e:
            # 居中显示错误提示
            error_window = tk.Toplevel(self.app.root)
            error_window.title("日期格式错误")
            error_window.geometry("400x100")
            error_window.resizable(False, False)
            error_window.transient(self.app.root)
            error_window.grab_set()
            
            # 居中显示错误窗口
            self.app.center_window_relative(error_window, self.app.root)
            
            tk.Label(error_window, text=f"日期处理出错: {str(e)}", 
                    padx=20, pady=20).pack()
            tk.Button(error_window, text="确定", command=error_window.destroy, width=10).pack(pady=10)
            
            self.app.log(f"日期处理出错: {str(e)}", "error")
            return False