import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import StrMethodFormatter, MaxNLocator
import sys
import os
import pandas as pd
import warnings

# 导入自定义模块
from core import PerformanceAnalysis
from utils import setup_fonts, normalize_date_string, detect_file_type, read_csv_file, read_excel_file, log_to_text_widget, cleanup_exit, log_message
from gui_components import create_menu_bar, create_main_interface, create_log_window
from config import Config

# 忽略openpyxl的样式警告
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.styles.stylesheet")

# 全局变量跟踪打开的窗口数
OPEN_WINDOWS = 0
MAX_WINDOWS = 2

class PerformanceBacktestTool:
    def __init__(self, root):
        global OPEN_WINDOWS
        if OPEN_WINDOWS >= MAX_WINDOWS:
            messagebox.showwarning("警告", f"最多只能打开{MAX_WINDOWS}个窗口")
            root.destroy()
            return
            
        OPEN_WINDOWS += 1
        
        self.root = root
        self.root.title("业绩表现回测工具")
        self.root.geometry("780x520")
        self.root.resizable(False, False)  # 锁定主窗口不允许拉伸
        
        # 设置程序图标
        try:
            self.root.iconbitmap('app.ico')
        except:
            pass
            
        # 窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", lambda: cleanup_exit(self.root))
        
        # 初始化配置
        self.config = Config()
        
        self.df = None
        self.chart_title = "净值趋势图"
        self.full_view_data = None
        self.current_start_date = None
        self.current_end_date = None
        self.current_plot_data = None  # 存储当前显示的图表数据
        
        # 修正: 初始化最高点和最低点信息，防止在没有数据时报错
        self.hover_annotation = None
        # 修正：为十字虚线和空心圆添加新的引用
        self.hover_line_x = None
        self.hover_line_y = None
        self.hover_marker = None
        self.hover_text_obj = None
        self.max_min_text_obj = [] # 用于存储 Max/Min 文本对象

        self.max_value = None
        self.min_value = None
        self.max_date_str = None
        self.min_date_str = None

        # 设置全局样式
        self.root.configure(bg=self.config.colors["background"])
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(".", background=self.config.colors["background"])
        self.style.configure("TFrame", background=self.config.colors["background"])
        self.style.configure("TLabel", background=self.config.colors["background"], foreground=self.config.colors["text"])
        self.style.configure("TEntry", fieldbackground=self.config.colors["input_bg"], foreground=self.config.colors["text"])
        self.style.configure("TLabelframe", background=self.config.colors["background"], bordercolor=self.config.colors["border"])
        self.style.configure("TLabelframe.Label", background=self.config.colors["background"], foreground=self.config.colors["primary"])
        
        self.style.configure("TButton", 
                            font=("Helvetica", 9),
                            padding=5,
                            background=self.config.colors["button"],
                            foreground="white",
                            borderwidth=1,
                            relief="flat",
                            bordercolor=self.config.colors["button"])
        
        self.style.map("TButton", 
                      background=[("active", self.config.colors["button_hover"])],
                      relief=[("active", "groove")])
        
        self.style.configure("TLabelframe", 
                            background=self.config.colors["background"],
                            bordercolor=self.config.colors["border"],
                            borderwidth=1,
                            relief="groove")
        self.style.configure("TLabelframe.Label", 
                            foreground=self.config.colors["primary"],
                            font=("Helvetica", 9, "bold"))
        
        self.style.configure("Treeview",
                            background=self.config.colors["card"],
                            foreground=self.config.colors["text"],
                            fieldbackground=self.config.colors["card"],
                            borderwidth=1,
                            font=("Helvetica", 9))
        
        self.style.configure("Treeview.Heading",
                            background=self.config.colors["group_box"],
                            foreground=self.config.colors["primary"],
                            font=("Helvetica", 9, "bold"),
                            relief="flat")
        
        # 创建菜单栏
        self.menu_bar = create_menu_bar(self)
        
        # 创建主界面
        self.main_frame, self.components = create_main_interface(self)
        
        # 初始化图表
        self.figure, self.ax = plt.subplots(figsize=(8, 3.0), dpi=100)
        self.figure.patch.set_facecolor(self.config.colors["background"])
        self.ax.set_facecolor(self.config.colors["chart_bg"])
        
        self.canvas = FigureCanvasTkAgg(self.figure, self.components["chart_frame"])
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas.mpl_connect('motion_notify_event', self.on_hover)
        self.canvas.mpl_connect('axes_leave_event', self.on_leave)
        
        setup_fonts()
        self.initialize_chart()
        
        # 创建日志窗口
        self.log_texts = create_log_window(self)
        
        self.log("欢迎使用业绩表现回测工具", "info")
        self.log("请导入文件开始使用", "info")
        self.log("rizona.cn@gmail.com", "info")

    def log(self, message, message_type="info"):
        """记录日志到所有相关的文本控件"""
        for key, log_text in self.log_texts.items():
            if key == "all" or key == message_type:
                log_to_text_widget(log_text, message, message_type)
    
    def on_start_focus_in(self, event):
        if self.components["start_entry"].get() == "YYYY-MM-DD":
            self.components["start_entry"].delete(0, tk.END)
            self.components["start_entry"].configure(foreground=self.config.colors["text"])
    
    def on_start_focus_out(self, event):
        self._validate_dates(self.components["start_entry"])
    
    def on_start_return(self, event):
        if self._validate_dates(self.components["start_entry"]):
            if self.components["end_entry"].get() and self.components["end_entry"].get() != "YYYY-MM-DD":
                self.custom_analysis()
            else:
                self.components["end_entry"].focus()
                self.components["end_entry"].select_range(0, tk.END)
    
    def on_end_focus_in(self, event):
        if self.components["end_entry"].get() == "YYYY-MM-DD":
            self.components["end_entry"].delete(0, tk.END)
            self.components["end_entry"].configure(foreground=self.config.colors["text"])
    
    def on_end_focus_out(self, event):
        self._validate_dates(self.components["end_entry"])
    
    def on_end_return(self, event):
        if self._validate_dates(self.components["end_entry"]):
            if (self.components["start_entry"].get() and self.components["start_entry"].get() != "YYYY-MM-DD" and
                self.components["end_entry"].get() and self.components["end_entry"].get() != "YYYY-MM-DD"):
                self.custom_analysis()
            else:
                self.components["start_entry"].focus()
                self.components["start_entry"].select_range(0, tk.END)

    def _validate_dates(self, entry):
        date_str = entry.get()
        if date_str == "YYYY-MM-DD" or not date_str:
            entry.configure(foreground=self.config.colors["placeholder"])
            return False

        try:
            normalized_date = normalize_date_string(date_str, self.log)
            datetime.strptime(normalized_date, "%Y-%m-%d")
            entry.delete(0, tk.END)
            entry.insert(0, normalized_date)
            entry.configure(foreground=self.config.colors["text"])
            self.log(f"日期 '{date_str}' 格式校验通过。", "success")
            return True
        except ValueError:
            messagebox.showerror("日期格式错误", f"无效的日期格式: '{date_str}'。请使用 YYYY-MM-DD 或 YYYYMMDD 格式。")
            entry.configure(foreground="red")
            self.log(f"日期 '{date_str}' 格式校验失败。", "error")
            return False
        except Exception as e:
            messagebox.showerror("日期格式错误", f"日期处理出错: {str(e)}")
            self.log(f"日期处理出错: {str(e)}", "error")
            return False

    def reset_application(self):
        self.df = None
        self.full_view_data = None
        self.current_plot_data = None  # 重置当前图表数据
        
        # 清空Max/Min数据
        self.max_value = None
        self.min_value = None
        self.max_date_str = None
        self.min_date_str = None
        
        self.initialize_chart()
        
        for item in self.components["result_tree"].get_children():
            self.components["result_tree"].delete(item)
        
        # 修正1: 重置时，固定周期指标也用 / 占位
        fixed_freq_placeholders = [
            ("近1周", '/'), ("近2周", '/'), ("近3周", '/'),
            ("近1月", '/'), ("近2月", '/'), ("近3月", '/'),
            ("近6月", '/'), ("近1年", '/'), ("成立以来", '/')
        ]
        for freq, placeholder in fixed_freq_placeholders:
            self.components["result_tree"].insert("", "end", values=(freq, placeholder, placeholder, placeholder))

        self.components["custom_range_label"].config(text="日期范围: --")
        self.components["custom_days_label"].config(text="周期天数: --")
        self.components["custom_return_label_value"].config(text="--", foreground=self.config.colors["text"])
        self.components["custom_drawdown_label_value"].config(text="--", foreground=self.config.colors["text"])
        
        self.components["start_entry"].delete(0, tk.END)
        self.components["start_entry"].insert(0, "YYYY-MM-DD")
        self.components["start_entry"].configure(foreground=self.config.colors["placeholder"])
        self.components["end_entry"].delete(0, tk.END)
        self.components["end_entry"].insert(0, "YYYY-MM-DD")
        self.components["end_entry"].configure(foreground=self.config.colors["placeholder"])
        
        # 更新菜单状态
        menu = self.root.nametowidget(".!menu")
        file_menu = menu.winfo_children()[0]  # 文件菜单是第一个
        file_menu.entryconfig("导出图表", state=tk.DISABLED)
        
        self.components["btn_reset"]['state'] = tk.DISABLED
        
        # 重置导出图表设置
        self.config.set("show_hover_data", False)
        self.config.set("hover_date", "")
        
        self.clear_log_text()
        
        self.log("应用已重置", "success")
        self.log("欢迎使用业绩表现回测工具", "info")
        self.log("请导入文件开始使用", "info")
        self.log("rizona.cn@gmail.com", "info")

    def show_readme(self):
        readme_window = tk.Toplevel(self.root)
        readme_window.title("使用说明")
        readme_window.geometry("500x400")
        readme_window.resizable(False, False)
        readme_window.configure(bg=self.config.colors["background"])
        readme_window.transient(self.root)
        
        # 设置窗口居中显示
        readme_window.update_idletasks()  # 更新窗口任务
        
        # 计算窗口居中位置
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        win_width = 500
        win_height = 400
        x = root_x + (root_width // 2) - (win_width // 2)
        y = root_y + (root_height // 2) - (win_height // 2)
        
        readme_window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        readme_window.deiconify()  # 显示窗口
        
        readme_window.grab_set()
        
        main_frame = ttk.Frame(readme_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area = tk.Text(
            scroll_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            bg=self.config.colors["card"],
            fg=self.config.colors["text"],
            font=("Helvetica", 10),
            borderwidth=1,
            relief="solid",
            padx=10,
            pady=10
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_area.yview)
        
        readme_text = """
1. 导入数据
  - 支持csv、xls、xlsx格式文件导入
  - 自动识别模板中「日期、单位净值」列

2. 数据分析
  - 自动计算固定周期业绩
  - 自动计算年化收益率、最大回撤
  - 支持自定义日期区间分析

3. 净值趋势图
  - 自动生成净值趋势图
  - 标记最高点和最低点
  - 鼠标悬停可显示日期和净值

4. 导出功能
  - 可以区间命名导出净值趋势图

5. 其他功能
  - 恢复全览：返回完整数据视图
  - 系统日志：记录操作过程

使用提示：
  - 日期格式支持多种形式[YYYY-MM-DD/YYYYMMDD/YYYY/MM/DD]
  - Mailto:rizona.cn@gmail.com
"""
        text_area.insert(tk.INSERT, readme_text)
        text_area.config(state=tk.DISABLED)
        
        author_frame = ttk.Frame(main_frame)
        author_frame.pack(fill=tk.X, pady=(0, 5))
        
        author_label = ttk.Label(
            author_frame, 
            text="Arizona.cn@gmail.com",
            font=("Helvetica", 10),
            foreground=self.config.colors["accent"],
            background=self.config.colors["card"]
        )
        author_label.pack(side=tk.BOTTOM)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        close_btn = ttk.Button(
            btn_frame, 
            text="关闭", 
            command=lambda: self.close_readme(readme_window),
            style="TButton"
        )
        close_btn.pack(pady=5, ipadx=10, ipady=3)
    
    def close_readme(self, window):
        window.grab_release()
        window.destroy()
    
    def import_data(self):
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
                 self.log("导入取消", "info")
                 return
        
            self.log(f"开始导入文件: {os.path.basename(file_path)}", "info")
            
            file_type = detect_file_type(file_path, self.log)
            self.log(f"检测到文件类型: {file_type}", "info")
            
            if file_type == 'excel':
                self.df = read_excel_file(file_path, self.log)
            else:
                self.df = read_csv_file(file_path, self.log)
            
            if self.df is None or self.df.empty:
                messagebox.showwarning("警告", "导入的数据为空")
                self.log("导入失败: 数据为空", "warning")
                return
                
            self.log(f"原始列名: {self.df.columns.tolist()}", "info")
            
            # 增强列名匹配逻辑
            date_col = None
            nav_col = None
            date_keywords = ['日期', '净值日期', 'date', '交易日期', '时间', 'time', '净值时间', '净值日期']
            nav_keywords = ['单位净值', 'net', 'nav', '净值', '单位价值', '单位份额净值', '份额净值']
            
            for col in self.df.columns:
                col_str = str(col).lower().replace(" ", "").replace("_", "")
                if date_col is None:
                    for keyword in date_keywords:
                        if keyword.lower() in col_str:
                            date_col = col
                            self.log(f"找到日期列: '{col}'", "info")
                            break
                if nav_col is None:
                    for keyword in nav_keywords:
                        if keyword.lower() in col_str:
                            nav_col = col
                            self.log(f"找到单位净值列: '{col}'", "info")
                            break
                if date_col and nav_col:
                    break
            
            if date_col is None or nav_col is None:
                if len(self.df.columns) >= 2:
                    self.log("未找到标准列名，尝试使用前两列作为日期和单位净值", "warning")
                    date_col = self.df.columns[0]
                    nav_col = self.df.columns[1]
                else:
                    messagebox.showerror("错误", "文件列数不足，至少需要两列数据")
                    self.log("导入失败: 文件列数不足", "error")
                    return
            
            self.df = self.df[[date_col, nav_col]].copy()
            self.df.columns = ['日期', '单位净值']
            self.log(f"重命名后的列名: {self.df.columns.tolist()}", "info")
            
            # 导入核心处理逻辑
            performance_analyzer = PerformanceAnalysis(self.df, self.log)
            self.df = performance_analyzer.prepare_data()
            
            if self.df is None or self.df.empty:
                messagebox.showerror("错误", "处理后的数据为空")
                self.log("导入失败: 处理后的数据为空", "error")
                return
            
            # 更新菜单状态
            menu = self.root.nametowidget(".!menu")
            file_menu = menu.winfo_children()[0]  # 文件菜单是第一个
            file_menu.entryconfig("导出图表", state=tk.NORMAL)
            
            self.components["btn_reset"]['state'] = tk.NORMAL
            
            min_date = self.df['日期'].min()
            max_date = self.df['日期'].max()
            
            if not pd.isna(min_date) and not pd.isna(max_date):
                min_date = min_date.date()
                max_date = max_date.date()
                self.components["start_entry"].delete(0, tk.END)
                self.components["start_entry"].insert(0, min_date.strftime("%Y-%m-%d"))
                self.components["start_entry"].configure(foreground=self.config.colors["text"])
                self.components["end_entry"].delete(0, tk.END)
                self.components["end_entry"].insert(0, max_date.strftime("%Y-%m-%d"))
                self.components["end_entry"].configure(foreground=self.config.colors["text"])
            else:
                self.log("警告: 数据中没有有效的日期", "warning")
            
            self.full_view_data = self.df.copy()
            self.calculate_fixed_freq()
            self.analyze_performance()
            
            self.components["custom_range_label"].config(text="日期范围: --")
            self.components["custom_days_label"].config(text="周期天数: --")
            self.components["custom_return_label_value"].config(text="--", foreground=self.config.colors["text"])
            self.components["custom_drawdown_label_value"].config(text="--", foreground=self.config.colors["text"])
            
            filename = os.path.basename(file_path)
            if len(filename) > 20:
                display_name = filename[:10] + "..." + filename[-10:]
            else:
                display_name = filename
                
            self.log(f"成功导入数据: {display_name}", "success")
            self.log(f"数据记录数: {len(self.df)}", "info")
            
            if not pd.isna(min_date) and not pd.isna(max_date):
                min_date_str = min_date.strftime("%Y-%m-%d")
                max_date_str = max_date.strftime("%Y-%m-%d")
                self.log(f"数据日期范围: {min_date_str} 至 {max_date_str}", "info")
                self.log(f"最早净值: {self.df['单位净值'].iloc[0]:.4f} (日期: {min_date_str})", "info")
                self.log(f"最新净值: {self.df['单位净值'].iloc[-1]:.4f} (日期: {max_date_str})", "info")
            else:
                self.log("警告: 无法确定日期范围", "warning")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入文件时出错:\n{str(e)}")
            self.log(f"导入失败: {str(e)}", "error")
            import traceback
            traceback.print_exc()

    def calculate_fixed_freq(self):
        """计算固定周期的业绩指标，并更新到界面上"""
        if self.df is None or len(self.df) == 0:
            # 数据为空时，保持 / 占位符
            return
        
        self.log("开始计算固定周期业绩...", "info")
        
        for item in self.components["result_tree"].get_children():
            self.components["result_tree"].delete(item)
        
        performance_analyzer = PerformanceAnalysis(self.df, self.log)
        results = performance_analyzer.calculate_fixed_freq()
        
        if not results:
            self.log("数据天数不足，无法计算固定周期业绩", "warning")
            return
            
        for values in results:
            self.components["result_tree"].insert("", "end", values=values)
            if values[1] != '/':
                self.log(f"{values[0]}: 天数={values[1]}, 年化={values[2]}, 回撤={values[3]}", "info")
            else:
                 self.log(f"数据不足，无法计算 {values[0]} 的业绩。", "info")
        
        self.log("固定周期业绩计算完成", "success")
    
    def custom_analysis(self):
        if self.df is None or len(self.df) == 0:
            messagebox.showwarning("警告", "请先导入数据文件！")
            self.log("自定义分析失败: 无数据", "warning")
            return
        
        start_date_str = self.components["start_entry"].get()
        end_date_str = self.components["end_entry"].get()
        
        if start_date_str == "YYYY-MM-DD" or end_date_str == "YYYY-MM-DD":
            messagebox.showwarning("警告", "请输入有效的日期")
            self.log("日期输入无效，请重新输入", "warning")
            return
        
        # 在点击分析按钮时再次进行最终校验
        if not self._validate_dates(self.components["start_entry"]) or not self._validate_dates(self.components["end_entry"]):
            self.log("日期格式错误，分析中止。", "error")
            return

        try:
            start_date = datetime.strptime(self.components["start_entry"].get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.components["end_entry"].get(), "%Y-%m-%d")
            
            self.log(f"开始自定义分析: {self.components['start_entry'].get()} 至 {self.components['end_entry'].get()}", "info")
            
            performance_analyzer = PerformanceAnalysis(self.df, self.log)
            result = performance_analyzer.calculate_custom_range(start_date, end_date)
            
            if result is None:
                return
                
            self.components["custom_range_label"].config(
                text=f"日期范围: {result['start_date'].strftime('%Y-%m-%d')} 至 {result['end_date'].strftime('%Y-%m-%d')}"
            )
            self.components["custom_days_label"].config(text=f"周期天数: {result['days']}天")
            
            return_color = "#E74C3C" if result['annual_return'] >= 0 else "#27AE60"
            self.components["custom_return_label_value"].config(text=f"{result['annual_return']:.2%}", foreground=return_color)
            
            drawdown_color = "#27AE60"
            self.components["custom_drawdown_label_value"].config(text=f"-{result['max_drawdown']:.2%}", foreground=drawdown_color)
            
            self.analyze_performance(start_date=start_date, end_date=end_date)
            self.log(f"自定义分析完成: 天数={result['days']}, 年化={result['annual_return']:.2%}, 回撤={result['max_drawdown']:.2%}", "success")
            self.log(f"开始净值: {result['nav_start']:.4f} (日期: {result['actual_start_date'].strftime('%Y-%m-%d')})", "info")
            self.log(f"结束净值: {result['nav_end']:.4f} (日期: {result['actual_end_date'].strftime('%Y-%m-%d')})", "info")

        except Exception as e:
            messagebox.showerror("错误", f"日期处理出错: {str(e)}")
            self.log(f"日期处理出错: {str(e)}", "error")

    def reset_to_full_view(self):
        if self.df is None or self.full_view_data is None:
            return
            
        self.df = self.full_view_data.copy()
        
        min_date = self.df['日期'].min().date()
        max_date = self.df['日期'].max().date()
        
        self.components["start_entry"].delete(0, tk.END)
        self.components["start_entry"].insert(0, min_date.strftime("%Y-%m-%d"))
        self.components["start_entry"].configure(foreground=self.config.colors["text"])
        self.components["end_entry"].delete(0, tk.END)
        self.components["end_entry"].insert(0, max_date.strftime("%Y-%m-%d"))
        self.components["end_entry"].configure(foreground=self.config.colors["text"])
        
        self.components["custom_range_label"].config(text="日期范围: --")
        self.components["custom_days_label"].config(text="周期天数: --")
        self.components["custom_return_label_value"].config(text="--", foreground=self.config.colors["text"])
        self.components["custom_drawdown_label_value"].config(text="--", foreground=self.config.colors["text"])
        
        self.analyze_performance()
        self.calculate_fixed_freq()
        
        # 重置导出图表设置
        self.config.set("show_hover_data", False)
        self.config.set("hover_date", "")
        
        self.log("已恢复全览视图", "success")
    
    def analyze_performance(self, start_date=None, end_date=None):
        if self.df is None or len(self.df) == 0:
            return
        
        self.ax.clear()
        
        performance_analyzer = PerformanceAnalysis(self.df, self.log)
        df_plot, self.chart_title, self.current_start_date, self.current_end_date = \
            performance_analyzer.prepare_chart_data(start_date, end_date)
            
        # 存储当前显示的图表数据，用于悬停事件
        self.current_plot_data = df_plot.copy()

        # 每次绘制新图表前，清除旧的悬停标注对象和标记
        if self.hover_line_x:
            try:
                self.hover_line_x.remove()
            except:
                pass
            self.hover_line_x = None
        
        if self.hover_line_y:
            try:
                self.hover_line_y.remove()
            except:
                pass
            self.hover_line_y = None
        
        if self.hover_marker:
            try:
                self.hover_marker.remove()
            except:
                pass
            self.hover_marker = None
        
        if self.hover_text_obj:
            try:
                self.hover_text_obj.remove()
            except:
                pass
            self.hover_text_obj = None

        # 每次重绘图表，都清空并重新绘制 Max/Min 文本和标记
        if self.max_min_text_obj:
            for text_obj in self.max_min_text_obj:
                try:
                    text_obj.remove()
                except:
                    pass
            self.max_min_text_obj = []
        
        unit_color = self.config.colors["chart_line"]
        
        self.ax.plot(
            df_plot['日期'], 
            df_plot['单位净值'], 
            color=unit_color, 
            linestyle='-', 
            linewidth=1.0
        )
        
        min_idx = df_plot['单位净值'].idxmin()
        max_idx = df_plot['单位净值'].idxmax()
        
        self.min_date_str = df_plot.loc[min_idx, '日期'].strftime("%y/%m/%d")
        self.min_value = df_plot.loc[min_idx, '单位净值']
        self.max_date_str = df_plot.loc[max_idx, '日期'].strftime("%y/%m/%d")
        self.max_value = df_plot.loc[max_idx, '单位净值']

        self.ax.plot(
            df_plot.loc[max_idx, '日期'], 
            self.max_value, 
            marker='o', 
            markersize=6,
            markerfacecolor='none',
            markeredgecolor=self.config.colors["max_color"], 
            markeredgewidth=1.5,
            linestyle='',
            zorder=10
        )
        
        self.ax.plot(
            df_plot.loc[min_idx, '日期'], 
            self.min_value, 
            marker='o', 
            markersize=6,
            markerfacecolor='none',
            markeredgecolor=self.config.colors["min_color"], 
            markeredgewidth=1.5,
            linestyle='',
            zorder=10
        )
        
        # 根据配置设置Max/Min文本框位置
        position = self.config.get("max_min_position")
        alpha = self.config.get("textbox_alpha")
        
        # 调整Max/Min文本框位置，避免重叠
        if position == "top-left":
            max_x, max_y = 0.02, 0.95
            min_x, min_y = 0.02, 0.85
            max_ha, max_va = 'left', 'top'
            min_ha, min_va = 'left', 'top'
        elif position == "top-right":
            max_x, max_y = 0.98, 0.95
            min_x, min_y = 0.98, 0.85
            max_ha, max_va = 'right', 'top'
            min_ha, min_va = 'right', 'top'
        elif position == "bottom-left":
            max_x, max_y = 0.02, 0.15
            min_x, min_y = 0.02, 0.05
            max_ha, max_va = 'left', 'bottom'
            min_ha, min_va = 'left', 'bottom'
        elif position == "bottom-right":
            max_x, max_y = 0.98, 0.15
            min_x, min_y = 0.98, 0.05
            max_ha, max_va = 'right', 'bottom'
            min_ha, min_va = 'right', 'bottom'
        
        # 修正：统一文本格式以保证框体大小一致，保持左对齐
        max_text = f'Max: {self.max_value: >8.4f} ({self.max_date_str})'
        min_text = f'Min: {self.min_value: >8.4f} ({self.min_date_str})'
        
        max_text_obj = self.ax.text(
            max_x, max_y,
            max_text,
            transform=self.ax.transAxes,
            fontsize=8,
            color=self.config.colors["max_color"],
            bbox=dict(
                boxstyle="round,pad=0.3",  # 减小内边距
                fc="white",
                ec="none",
                lw=0,
                alpha=alpha
            ),
            ha=max_ha,
            va=max_va,
            zorder=10
        )
        
        min_text_obj = self.ax.text(
            min_x, min_y,
            min_text,
            transform=self.ax.transAxes,
            fontsize=8,
            color=self.config.colors["min_color"],
            bbox=dict(
                boxstyle="round,pad=0.3",  # 减小内边距
                fc="white",
                ec="none",
                lw=0,
                alpha=alpha
            ),
            ha=min_ha,
            va=min_va,
            zorder=10
        )
        self.max_min_text_obj = [max_text_obj, min_text_obj]

        date_range = df_plot['日期'].max() - df_plot['日期'].min()
        days = date_range.days
        
        if days <= 30:
            date_format = '%m-%d'
            interval = max(1, int(days/7))
            locator = mdates.DayLocator(interval=interval)
        elif days <= 180:
            date_format = '%m-%d'
            interval = max(1, int(days/10))
            locator = mdates.DayLocator(interval=interval)
        elif days <= 365:
            date_format = '%m-%d'
            locator = mdates.MonthLocator()
        else:
            date_format = '%Y-%m'
            locator = mdates.MonthLocator(interval=3)
        
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        
        min_nav = df_plot['单位净值'].min()
        max_nav = df_plot['单位净值'].max()
        nav_range = max_nav - min_nav
        
        if nav_range > 0:
            buffer = nav_range * 0.05
            self.ax.set_ylim(min_nav - buffer, max_nav + buffer)
        
        self.ax.yaxis.set_major_locator(MaxNLocator(prune='both', nbins=5))
        
        self.ax.grid(True, 
                    linestyle='--', 
                    alpha=0.6, 
                    color=self.config.colors["chart_grid"])
        
        self.ax.tick_params(axis='x', 
                           which='major', 
                           labelsize=4,
                           colors=self.config.colors["text"])
        self.ax.tick_params(axis='y', 
                           which='major', 
                           labelsize=5,
                           colors=self.config.colors["text"])
        self.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.4f}'))
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.config.colors["text_light"])
        self.ax.spines['bottom'].set_color(self.config.colors["text_light"])  # 修复：set颜色 -> set_color
        
        plt.setp(self.ax.get_xticklabels(), rotation=30, ha='right', fontsize=4)
        
        self.figure.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.35)
        self.figure.tight_layout(pad=1.5)
        
        self.canvas.draw()
        self.log("净值趋势图生成完成", "success")
    
    def export_chart(self):
        if not hasattr(self, 'figure') or not self.figure:
            messagebox.showwarning("警告", "没有可导出的图表")
            return
        
        if self.current_start_date and self.current_end_date:
            if self.current_start_date.year == self.current_end_date.year:
                filename = (
                    f"{self.current_start_date.year}--"
                    f"{self.current_start_date.strftime('%m%d')}～"
                    f"{self.current_end_date.strftime('%m%d')}净值趋势图"
                )
            else:
                filename = (
                    f"{self.current_start_date.strftime('%y%m%d')}～"
                    f"{self.current_end_date.strftime('%y%m%d')}净值趋势图"
                )
        else:
            filename = "净值趋势图"
        
        # 使用配置的导出目录
        initial_dir = self.config.get("export_directory")
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("所有文件", "*.*")],
            title="保存图表",
            initialdir=initial_dir,
            initialfile=filename
        )
        
        if not file_path:
            return
        
        try:
            # 如果启用了悬停数据显示，添加悬停数据
            if self.config.get("show_hover_data") and self.config.get("hover_date"):
                try:
                    hover_date = datetime.strptime(self.config.get("hover_date"), "%Y-%m-%d")
                    if self.current_plot_data is not None:
                        # 找到最接近的日期
                        closest_idx = self.current_plot_data['日期'].sub(hover_date).abs().idxmin()
                        closest_row = self.current_plot_data.loc[closest_idx]
                        nav = closest_row['单位净值']
                        date = closest_row['日期']
                        
                        # 添加悬停十字线但不添加文本
                        self.ax.axvline(
                            x=date,
                            color=self.config.colors["chart_hover"],
                            linestyle='--',
                            linewidth=1,
                            alpha=0.5,
                            zorder=5
                        )
                        
                        self.ax.axhline(
                            y=nav,
                            color=self.config.colors["chart_hover"],
                            linestyle='--',
                            linewidth=1,
                            alpha=0.5,
                            zorder=5
                        )
                        
                        # 添加空心圆标记
                        self.ax.plot(
                            date,
                            nav,
                            marker='o',
                            markersize=5,
                            markerfacecolor='none',
                            markeredgecolor=self.config.colors["chart_hover"],
                            markeredgewidth=1.5,
                            linestyle='',
                            zorder=10
                        )
                except ValueError:
                    self.log("悬停日期格式无效，将不显示悬停数据", "warning")
            
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            self.log(f"图表已导出: {file_path}", "success")
        except Exception as e:
            messagebox.showerror("错误", f"保存图表时出错:\n{str(e)}")
            self.log(f"导出图表失败: {str(e)}", "error")
    
    def initialize_chart(self):
        self.ax.clear()
        self.current_plot_data = None  # 清空当前图表数据
        
        if self.hover_line_x:
            try:
                self.hover_line_x.remove()
            except:
                pass
            self.hover_line_x = None
        
        if self.hover_line_y:
            try:
                self.hover_line_y.remove()
            except:
                pass
            self.hover_line_y = None
        
        if self.hover_marker:
            try:
                self.hover_marker.remove()
            except:
                pass
            self.hover_marker = None
        
        if self.hover_text_obj:
            try:
                self.hover_text_obj.remove()
            except:
                pass
            self.hover_text_obj = None

        if self.max_min_text_obj:
            for text_obj in self.max_min_text_obj:
                try:
                    text_obj.remove()
                except:
                    pass
            self.max_min_text_obj = []

        self.figure.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.35)
        self.figure.tight_layout(pad=1.5)
        
        self.ax.tick_params(axis='x', 
                           which='major', 
                           labelsize=4, 
                           colors=self.config.colors["text"])
        self.ax.tick_params(axis='y', 
                           which='major', 
                           labelsize=5, 
                           colors=self.config.colors["text"])
        self.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.4f}'))
        self.ax.yaxis.set_major_locator(MaxNLocator(prune='both', nbins=5))
        
        self.ax.grid(True, 
                    linestyle='--', 
                    alpha=0.6, 
                    color=self.config.colors["chart_grid"])
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.config.colors["text_light"])
        self.ax.spines['bottom'].set_color(self.config.colors["text_light"])  # 修复：set颜色 -> set_color
        
        plt.setp(self.ax.get_xticklabels(), rotation=30, ha='right', fontsize=4)
        
        self.canvas.draw()

    def on_hover(self, event):
        """处理鼠标悬停事件，显示日期和净值，并绘制十字虚线"""
        # 使用当前显示的图表数据而不是完整数据集
        if self.current_plot_data is None or event.inaxes != self.ax:
            self.on_leave(event)
            return

        try:
            # 移除旧的悬停标注和标记
            if self.hover_text_obj:
                self.hover_text_obj.remove()
                self.hover_text_obj = None
            if self.hover_line_x:
                self.hover_line_x.remove()
                self.hover_line_x = None
            if self.hover_line_y:
                self.hover_line_y.remove()
                self.hover_line_y = None
            if self.hover_marker:
                self.hover_marker.remove()
                self.hover_marker = None

            xdata_date = mdates.num2date(event.xdata).replace(tzinfo=None)
            
            # 找到最近的日期数据点 - 使用当前显示的图表数据
            closest_idx = self.current_plot_data['日期'].sub(xdata_date).abs().idxmin()
            
            closest_row = self.current_plot_data.loc[closest_idx]
            nav = closest_row['单位净值']
            date = closest_row['日期']

            # 绘制新的十字虚线 (透明度设为0.5)
            self.hover_line_x = self.ax.axvline(
                x=date,
                color=self.config.colors["chart_hover"],
                linestyle='--',
                linewidth=1,
                alpha=0.5,
                zorder=5
            )

            self.hover_line_y = self.ax.axhline(
                y=nav,
                color=self.config.colors["chart_hover"],
                linestyle='--',
                linewidth=1,
                alpha=0.5,
                zorder=5
            )
            
            # 绘制新的空心圆
            self.hover_marker, = self.ax.plot(
                date,
                nav,
                marker='o',
                markersize=5,
                markerfacecolor='none',
                markeredgecolor=self.config.colors["chart_hover"],
                markeredgewidth=1.5,
                linestyle='',
                zorder=10
            )

            # 根据Max/Min位置确定Hover文本位置
            position = self.config.get("max_min_position")
            alpha = self.config.get("textbox_alpha")
            
            # 调整Hover文本位置，避免与Max/Min重叠
            if position in ["top-left", "top-right"]:
                # Max/Min在上方，Hover在Max下方
                hover_y = 0.75 if position == "top-left" else 0.75
            else:
                # Max/Min在下方，Hover在Max上方
                hover_y = 0.25 if position == "bottom-left" else 0.25
                
            # 根据对齐方式确定x坐标
            if position in ["top-left", "bottom-left"]:
                hover_x = 0.02
                hover_ha = 'left'
            else:
                hover_x = 0.98
                hover_ha = 'right'
            
            # 更新左上角的标注文本
            hover_data_text = f'Hover: {nav:.4f} ({date.strftime("%y/%m/%d")})'
            
            # 修正: 统一Hover文本颜色为橙色
            self.hover_text_obj = self.ax.text(
                hover_x, hover_y,
                hover_data_text,
                transform=self.ax.transAxes,
                fontsize=8,
                color=self.config.colors["chart_hover"],
                bbox=dict(
                    boxstyle="round,pad=0.3",  # 减小内边距
                    fc="white",
                    ec="none",
                    lw=0,
                    alpha=alpha
                ),
                ha=hover_ha,
                va='top',
                zorder=10
            )
            
            self.canvas.draw_idle()

        except Exception as e:
            self.on_leave(event)
            return

    def on_leave(self, event):
        """处理鼠标离开事件，移除标注和标记"""
        # 只移除悬停时创建的临时对象
        if self.hover_line_x:
            try:
                self.hover_line_x.remove()
            except:
                pass
            self.hover_line_x = None
        
        if self.hover_line_y:
            try:
                self.hover_line_y.remove()
            except:
                pass
            self.hover_line_y = None
        
        if self.hover_marker:
            try:
                self.hover_marker.remove()
            except:
                pass
            self.hover_marker = None
        
        if self.hover_text_obj:
            try:
                self.hover_text_obj.remove()
            except:
                pass
            self.hover_text_obj = None
        
        self.canvas.draw_idle()
    
    def clear_log_text(self):
        """清空日志内容"""
        for log_text in self.log_texts.values():
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            log_text.config(state=tk.DISABLED)

    def set_export_chart_settings(self):
        """设置导出图表选项"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("导出图表设置")
        settings_window.geometry("400x200")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置窗口居中显示
        settings_window.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        win_width = 400
        win_height = 200
        x = root_x + (root_width // 2) - (win_width // 2)
        y = root_y + (root_height // 2) - (win_height // 2)
        
        settings_window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        main_frame = ttk.Frame(settings_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 悬停数据显示选项
        hover_var = tk.BooleanVar(value=self.config.get("show_hover_data"))
        
        def toggle_hover_date():
            if hover_var.get():
                hover_date_frame.pack(fill=tk.X, pady=(10, 0))
            else:
                hover_date_frame.pack_forget()
        
        hover_check = ttk.Checkbutton(
            main_frame,
            text="在导出的图表中显示悬停数据",
            variable=hover_var,
            command=toggle_hover_date
        )
        hover_check.pack(anchor=tk.W)
        
        # 悬停日期选择
        hover_date_frame = ttk.Frame(main_frame)
        if hover_var.get():
            hover_date_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(hover_date_frame, text="悬停日期:").pack(side=tk.LEFT, padx=(20, 5))
        
        hover_date_var = tk.StringVar(value=self.config.get("hover_date"))
        hover_date_entry = ttk.Entry(hover_date_frame, textvariable=hover_date_var, width=12)
        hover_date_entry.pack(side=tk.LEFT)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        def save_settings():
            self.config.set("show_hover_data", hover_var.get())
            self.config.set("hover_date", hover_date_var.get())
            settings_window.destroy()
            self.log("导出图表设置已保存", "success")
        
        def cancel_settings():
            settings_window.destroy()
        
        ttk.Button(button_frame, text="确定", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings).pack(side=tk.RIGHT)

    def set_export_directory(self):
        """设置导出目录"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("导出目录设置")
        settings_window.geometry("500x250")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置窗口居中显示
        settings_window.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        win_width = 500
        win_height = 250
        x = root_x + (root_width // 2) - (win_width // 2)
        y = root_y + (root_height // 2) - (win_height // 2)
        
        settings_window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        main_frame = ttk.Frame(settings_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 当前目录选项
        current_dir_var = tk.BooleanVar(value=self.config.get("export_directory") == os.getcwd())
        
        def toggle_directory_options():
            if current_dir_var.get():
                custom_dir_frame.pack_forget()
                self.config.set("export_directory", os.getcwd())
            else:
                custom_dir_frame.pack(fill=tk.X, pady=(10, 0))
        
        current_dir_radio = ttk.Radiobutton(
            main_frame,
            text=f"保存到当前目录: {os.getcwd()}",
            variable=current_dir_var,
            value=True,
            command=toggle_directory_options
        )
        current_dir_radio.pack(anchor=tk.W)
        
        # 自定义目录选项
        custom_dir_var = tk.BooleanVar(value=not current_dir_var.get())
        
        custom_dir_radio = ttk.Radiobutton(
            main_frame,
            text="自定义保存位置:",
            variable=current_dir_var,
            value=False,
            command=toggle_directory_options
        )
        custom_dir_radio.pack(anchor=tk.W, pady=(10, 0))
        
        # 自定义目录输入框和浏览按钮
        custom_dir_frame = ttk.Frame(main_frame)
        if not current_dir_var.get():
            custom_dir_frame.pack(fill=tk.X, pady=(10, 0))
        
        custom_dir_path = tk.StringVar(value=self.config.get("export_directory") if not current_dir_var.get() else "")
        custom_dir_entry = ttk.Entry(custom_dir_frame, textvariable=custom_dir_path, width=40)
        custom_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 5))
        
        def browse_directory():
            directory = filedialog.askdirectory(initialdir=custom_dir_path.get())
            if directory:
                custom_dir_path.set(directory)
        
        ttk.Button(custom_dir_frame, text="浏览", command=browse_directory, width=8).pack(side=tk.RIGHT)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        def save_settings():
            if current_dir_var.get():
                self.config.set("export_directory", os.getcwd())
            else:
                self.config.set("export_directory", custom_dir_path.get())
            settings_window.destroy()
            self.log(f"导出目录已设置为: {self.config.get('export_directory')}", "success")
        
        def cancel_settings():
            settings_window.destroy()
        
        ttk.Button(button_frame, text="确定", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings).pack(side=tk.RIGHT)

    def set_log_window(self):
        """设置日志窗口"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("日志窗口设置")
        settings_window.geometry("300x150")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置窗口居中显示
        settings_window.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        win_width = 300
        win_height = 150
        x = root_x + (root_width // 2) - (win_width // 2)
        y = root_y + (root_height // 2) - (win_height // 2)
        
        settings_window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        main_frame = ttk.Frame(settings_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志窗口选项
        log_window_var = tk.BooleanVar(value=self.config.get("show_log_window"))
        
        ttk.Radiobutton(
            main_frame,
            text="开启日志窗口",
            variable=log_window_var,
            value=True
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            main_frame,
            text="关闭日志窗口",
            variable=log_window_var,
            value=False
        ).pack(anchor=tk.W, pady=(10, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        def save_settings():
            self.config.set("show_log_window", log_window_var.get())
            
            if log_window_var.get():
                self.log_window.deiconify()
                # 重新定位日志窗口
                self.root.update_idletasks()
                root_x = self.root.winfo_x()
                root_y = self.root.winfo_y()
                root_width = self.root.winfo_width()
                self.log_window.geometry(f"+{root_x + root_width + 10}+{root_y}")
            else:
                self.log_window.withdraw()
                
            settings_window.destroy()
            self.log(f"日志窗口已{'开启' if log_window_var.get() else '关闭'}", "success")
        
        def cancel_settings():
            settings_window.destroy()
        
        ttk.Button(button_frame, text="确定", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings).pack(side=tk.RIGHT)

    def set_textbox_settings(self):
        """设置提示框位置"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("提示框设置")
        settings_window.geometry("300x200")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置窗口居中显示
        settings_window.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        win_width = 300
        win_height = 200
        x = root_x + (root_width // 2) - (win_width // 2)
        y = root_y + (root_height // 2) - (win_height // 2)
        
        settings_window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        main_frame = ttk.Frame(settings_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="选择提示框位置:").pack(anchor=tk.W)
        
        # 位置选项
        position_var = tk.StringVar(value=self.config.get("max_min_position"))
        
        positions = [
            ("左上", "top-left"),
            ("左下", "bottom-left"),
            ("右上", "top-right"),
            ("右下", "bottom-right")
        ]
        
        for text, value in positions:
            ttk.Radiobutton(
                main_frame,
                text=text,
                variable=position_var,
                value=value
            ).pack(anchor=tk.W, pady=(5, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
        
        def save_settings():
            self.config.set("max_min_position", position_var.get())
            settings_window.destroy()
            self.log(f"提示框位置已设置为: {position_var.get()}", "success")
            
            # 重新绘制图表以应用新设置
            if self.df is not None and len(self.df) > 0:
                self.analyze_performance()
        
        def cancel_settings():
            settings_window.destroy()
        
        ttk.Button(button_frame, text="确定", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings).pack(side=tk.RIGHT)

    def hide_log_window(self):
        """隐藏日志窗口"""
        if hasattr(self, 'log_window'):
            self.log_window.withdraw()

if __name__ == "__main__":
    root = tk.Tk()
    app = PerformanceBacktestTool(root)
    root.mainloop()