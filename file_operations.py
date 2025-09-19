# file_operations.py
import os
import tkinter as tk
import pandas as pd
from tkinter import filedialog, messagebox
from core import PerformanceAnalysis
from utils import detect_file_type, read_csv_file, read_excel_file

class FileOperations:
    def __init__(self, app):
        self.app = app
        self.config = app.config

    def import_data(self):
        """导入数据文件"""
        # 移除激活状态检查，允许未激活状态下导入文件
        try:
            file_path = filedialog.askopenfilename(
                title="选择数据文件",
                filetypes=[
                    ("CSV文件", "*.csv"),
                    ("Excel文件", "*.xlsx;*.xls"),
                    ("所有文件", "*.*")
                ]
            )
            if not file_path:
                 self.app.log("导入取消", "info")
                 return

            self.app.log(f"开始导入文件: {os.path.basename(file_path)}", "info")

            file_type = detect_file_type(file_path, self.app.log)
            self.app.log(f"检测到文件类型: {file_type}", "info")

            if file_type == 'excel':
                self.app.df = read_excel_file(file_path, self.app.log)
            else:
                self.app.df = read_csv_file(file_path, self.app.log)

            if self.app.df is None or self.app.df.empty:
                self.show_custom_message("警告", "导入的数据为空")
                self.app.log("导入失败: 数据为空", "warning")
                return

            self.app.log(f"原始列名: {self.app.df.columns.tolist()}", "info")

            # 增强列名匹配逻辑
            date_col = None
            nav_col = None
            date_keywords = ['日期', '净值日期', 'date', '交易日期', '时间', 'time', '净值时间', '净值日期']
            nav_keywords = ['单位净值', 'net', 'nav', '净值', '单位价值', '单位份额净值', '份额净值']

            for col in self.app.df.columns:
                col_str = str(col).lower().replace(" ", "").replace("_", "")
                if date_col is None:
                    for keyword in date_keywords:
                        if keyword.lower() in col_str:
                            date_col = col
                            self.app.log(f"找到日期列: '{col}'", "info")
                            break
                if nav_col is None:
                    for keyword in nav_keywords:
                        if keyword.lower() in col_str:
                            nav_col = col
                            self.app.log(f"找到单位净值列: '{col}'", "info")
                            break
                if date_col and nav_col:
                    break

            if date_col is None or nav_col is None:
                if len(self.app.df.columns) >= 2:
                    self.app.log("未找到标准列名，尝试使用前两列作为日期和单位净值", "warning")
                    date_col = self.app.df.columns[0]
                    nav_col = self.app.df.columns[1]
                else:
                    self.show_custom_message("错误", "文件列数不足，至少需要两列数据")
                    self.app.log("导入失败: 文件列数不足", "error")
                    return

            self.app.df = self.app.df[[date_col, nav_col]].copy()
            self.app.df.columns = ['日期', '单位净值']
            self.app.log(f"重命名后的列名: {self.app.df.columns.tolist()}", "info")

            # 导入核心处理逻辑
            performance_analyzer = PerformanceAnalysis(self.app.df, self.app.log)
            self.app.df = performance_analyzer.prepare_data()

            if self.app.df is None or self.app.df.empty:
                self.show_custom_message("错误", "处理后的数据为空")
                self.app.log("导入失败: 处理后的数据为空", "error")
                return

            # 更新菜单状态 - 根据激活状态决定是否启用功能
            menu = self.app.root.nametowidget(".!menu")
            file_menu = menu.winfo_children()[0]  # 文件菜单是第一个
            
            # 根据激活状态决定是否启用导出图表
            if self.app.is_activated:
                file_menu.entryconfig("导出图表", state=tk.NORMAL)
            else:
                file_menu.entryconfig("导出图表", state=tk.DISABLED)

            # 根据激活状态决定是否启用按钮
            if self.app.is_activated:
                self.app.components["btn_custom"].config(state=tk.NORMAL)
                self.app.components["btn_reset"].config(state=tk.NORMAL)
            else:
                self.app.components["btn_custom"].config(state=tk.DISABLED)
                self.app.components["btn_reset"].config(state=tk.DISABLED)
                
            self.app.components["btn_reset_app"].config(state=tk.NORMAL)

            min_date = self.app.df['日期'].min()
            max_date = self.app.df['日期'].max()

            if not pd.isna(min_date) and not pd.isna(max_date):
                min_date = min_date.date()
                max_date = max_date.date()
                
                # 根据激活状态设置输入框状态
                if self.app.is_activated:
                    # 激活状态下启用输入框
                    self.app.components["start_entry"].config(state='normal')
                    self.app.components["start_entry"].delete(0, tk.END)
                    self.app.components["start_entry"].insert(0, min_date.strftime("%Y-%m-%d"))
                    self.app.components["start_entry"].configure(foreground=self.config.colors["text"])
                    
                    self.app.components["end_entry"].config(state='normal')
                    self.app.components["end_entry"].delete(0, tk.END)
                    self.app.components["end_entry"].insert(0, max_date.strftime("%Y-%m-%d"))
                    self.app.components["end_entry"].configure(foreground=self.config.colors["text"])
                else:
                    # 未激活状态下禁用输入框，但仍显示日期
                    self.app.components["start_entry"].config(state='disabled')
                    self.app.components["start_entry"].delete(0, tk.END)
                    self.app.components["start_entry"].insert(0, min_date.strftime("%Y-%m-%d"))
                    self.app.components["start_entry"].configure(foreground=self.config.colors["text"])
                    
                    self.app.components["end_entry"].config(state='disabled')
                    self.app.components["end_entry"].delete(0, tk.END)
                    self.app.components["end_entry"].insert(0, max_date.strftime("%Y-%m-%d"))
                    self.app.components["end_entry"].configure(foreground=self.config.colors["text"])
            else:
                self.app.log("警告: 数据中没有有效的日期", "warning")

            self.app.full_view_data = self.app.df.copy()
            self.app.calculate_fixed_freq()
            self.app.analyze_performance()

            self.app.components["custom_range_start_label"].config(text="--")
            self.app.components["custom_range_end_label"].config(text="")
            self.app.components["custom_days_label"].config(text="--")
            self.app.components["custom_return_label_value"].config(text="--", foreground=self.config.colors["text"])
            self.app.components["custom_drawdown_label_value"].config(text="--", foreground=self.config.colors["text"])

            filename = os.path.basename(file_path)
            if len(filename) > 20:
                display_name = filename[:10] + "..." + filename[-10:]
            else:
                display_name = filename

            self.app.log(f"成功导入数据: {display_name}", "success")
            self.app.log(f"数据记录数: {len(self.app.df)}", "info")

            if not pd.isna(min_date) and not pd.isna(max_date):
                min_date_str = min_date.strftime("%Y-%m-%d")
                max_date_str = max_date.strftime("%Y-%m-%d")
                self.app.log(f"数据日期范围: {min_date_str} 至 {max_date_str}", "info")
                self.app.log(f"最早净值: {self.app.df['单位净值'].iloc[0]:.4f} (日期: {min_date_str})", "info")
                self.app.log(f"最新净值: {self.app.df['单位净值'].iloc[-1]:.4f} (日期: {max_date_str})", "info")
            else:
                self.app.log("警告: 无法确定日期范围", "warning")

        except Exception as e:
            self.show_custom_message("错误", f"导入文件时出错:\n{str(e)}")
            self.app.log(f"导入失败: {str(e)}", "error")
            import traceback
            traceback.print_exc()
    
    def show_custom_message(self, title, message):
        """显示自定义消息框，居中于父窗口"""
        window = tk.Toplevel(self.app.root)
        window.title(title)
        window.geometry("200x120")
        window.resizable(False, False)
        window.transient(self.app.root)
        window.grab_set()
        window.configure(bg=self.config.colors["background"])
        
        # 居中显示于父窗口
        self.app.center_window_relative(window, self.app.root)
        
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=message, 
                wraplength=350, justify=tk.LEFT).pack(pady=10)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="确定", command=window.destroy, width=10).pack()