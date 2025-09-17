# app.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import sys
import os
import pandas as pd
import warnings
import json
import hashlib
import uuid

# 导入自定义模块
from core import PerformanceAnalysis
from utils import setup_fonts, normalize_date_string, detect_file_type, read_csv_file, read_excel_file, log_to_text_widget, cleanup_exit, log_message
from gui_components import create_menu_bar, create_main_interface, create_log_window
from config import Config
from tooltip import ToolTip
from chart_utils import ChartUtils
from event_handlers import EventHandlers
from window_utils import WindowUtils
from activation import ActivationManager

# 忽略openpyxl的样式警告
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.styles.stylesheet")

# 全局变量跟踪打开的窗口数
OPEN_WINDOWS = 0
MAX_WINDOWS = 1

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
        # 初始宽度设为500，不包含日志区域
        self.root.geometry("500x540")  
        self.root.resizable(False, False)  # 不允许拉伸窗口

        # 设置程序图标
        try:
            self.root.iconbitmap('app.ico')
        except:
            pass

        # 窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", lambda: cleanup_exit(self.root))

        # 初始化配置
        self.config = Config()
        
        # 初始化激活管理器
        self.activation_manager = ActivationManager()
        self.is_activated = self.activation_manager.check_activation()

        self.df = None
        self.chart_title = "净值趋势图"
        self.full_view_data = None
        self.current_start_date = None
        self.current_end_date = None
        self.current_plot_data = None  # 存储当前显示的图表数据

        # 修正: 初始化最高点和最低点信息，防止在没有数据时报错
        self.hover_annotation = None
        # 修正：为十字虚线和空心圆添加新的引用
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

        self.style.configure("TLabelframe.Label", 
                            background=self.config.colors["background"], 
                            foreground=self.config.colors["primary"],
                            font=("Helvetica", 9, "bold"))

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

        # 创建主容器
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 创建左侧内容区域
        self.left_frame = ttk.Frame(self.main_container)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建右侧日志区域（初始隐藏）
        self.log_frame = ttk.Frame(self.main_container, width=300)  # 固定宽度
        self.log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.log_frame.pack_propagate(False)  # 阻止框架调整大小以适应内容

        # 初始隐藏日志区域
        self.log_frame.pack_forget()

        # 创建菜单栏
        self.menu_bar, self.settings_menu = create_menu_bar(self)

        # 创建主界面（放在左侧框架中）
        self.main_frame, self.components = create_main_interface(self, self.left_frame)

        # 初始化图表
        self.figure, self.ax = plt.subplots(figsize=(6.5, 3.5), dpi=100)  # 减小图表宽度
        self.figure.patch.set_facecolor(self.config.colors["background"])
        self.ax.set_facecolor(self.config.colors["chart_bg"])

        self.canvas = FigureCanvasTkAgg(self.figure, self.components["chart_frame"])
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 初始化工具类
        self.chart_utils = ChartUtils(self)
        self.event_handlers = EventHandlers(self)
        self.window_utils = WindowUtils(self)

        self.canvas.mpl_connect('motion_notify_event', self.chart_utils.on_hover)
        self.canvas.mpl_connect('axes_leave_event', self.chart_utils.on_leave)

        setup_fonts()
        self.chart_utils.initialize_chart()

        # 创建日志窗口（放在右侧框架中）
        self.log_texts = create_log_window(self, self.log_frame)

        # 根据配置决定是否显示日志窗口
        if self.config.get("show_log_window", False):
            self.show_log_window()
        else:
            self.hide_log_window()

        # 设置窗口居中显示
        self.window_utils.center_window(self.root)
        
        # 根据激活状态更新界面
        self.update_activation_status()
        
        self.log("欢迎使用业绩表现回测工具", "success")
        if not self.is_activated:
            self.log("软件未激活，请前往关于->说明中输入激活码", "warning")
            self.log("临时激活码: 0315 (有效期7天)", "info")
        else:
            self.log("软件已激活，请导入文件开始使用", "success")
        self.log("rizona.cn@gmail.com", "success")

    def update_activation_status(self):
        """根据激活状态更新界面"""
        if not self.is_activated:
            # 禁用设置菜单
            self.settings_menu.entryconfig(0, state=tk.DISABLED)  # 导出图表设置
            self.settings_menu.entryconfig(1, state=tk.DISABLED)  # 导出目录设置
            self.settings_menu.entryconfig(2, state=tk.DISABLED)  # 提示框设置
            self.settings_menu.entryconfig(3, state=tk.DISABLED)  # 日志窗口
            
            # 禁用自定义分析按钮
            self.components["btn_custom"].config(state=tk.DISABLED)
            
            # 禁用全览按钮
            self.components["btn_reset"].config(state=tk.DISABLED)
            
            # 启用日期输入框（允许查看但不能分析）
            self.components["start_entry"].config(state=tk.NORMAL)
            self.components["end_entry"].config(state=tk.NORMAL)

            # 启用重置按钮
            self.components["btn_reset_app"].config(state=tk.NORMAL)

        else:
            # 启用设置菜单
            self.settings_menu.entryconfig(0, state=tk.NORMAL)
            self.settings_menu.entryconfig(1, state=tk.NORMAL)
            self.settings_menu.entryconfig(2, state=tk.NORMAL)
            self.settings_menu.entryconfig(3, state=tk.NORMAL)
            
            # 启用自定义分析按钮
            self.components["btn_custom"].config(state=tk.NORMAL)
            self.components["btn_reset"].config(state=tk.NORMAL)
            self.components["btn_reset_app"].config(state=tk.NORMAL)
            
            # 启用日期输入框
            self.components["start_entry"].config(state=tk.NORMAL)
            self.components["end_entry"].config(state=tk.NORMAL)

    def center_window(self, window):
        """将窗口居中显示"""
        self.window_utils.center_window(window)

    def center_window_relative(self, window, parent):
        """将子窗口居中显示在父窗口中心"""
        self.window_utils.center_window_relative(window, parent)

    def update_log_menu_label(self):
        """更新日志菜单项的标签"""
        if self.config.get("show_log_window", True):
            self.settings_menu.entryconfig(3, label="关闭日志")
        else:
            self.settings_menu.entryconfig(3, label="开启日志")

    def show_log_window(self):
        """显示日志窗口"""
        self.log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        # 调整窗口大小
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{500 + 300}x540+{x}+{y}")
        self.config.set("show_log_window", True)
        self.update_log_menu_label()

    def hide_log_window(self):
        """隐藏日志窗口"""
        self.log_frame.pack_forget()
        # 调整窗口大小
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"500x540+{x}+{y}")
        self.config.set("show_log_window", False)
        self.update_log_menu_label()

    def set_log_window(self):
        """切换日志窗口显示/隐藏"""
        if not self.is_activated:
            messagebox.showwarning("警告", "软件未激活，无法使用此功能")
            return
            
        if self.config.get("show_log_window", True):
            self.hide_log_window()
            self.log("已关闭日志窗口", "success")
        else:
            self.show_log_window()
            self.log("已开启日志窗口", "success")

    def log(self, message, message_type="info"):
        """记录日志到所有相关的文本控件"""
        for key, log_text in self.log_texts.items():
            if key == "all" or key == message_type:
                log_to_text_widget(log_text, message, message_type)

    def on_start_focus_in(self, event):
        self.event_handlers.on_start_focus_in(event)

    def on_start_focus_out(self, event):
        self.event_handlers.on_start_focus_out(event)

    def on_start_return(self, event):
        self.event_handlers.on_start_return(event)

    def on_end_focus_in(self, event):
        self.event_handlers.on_end_focus_in(event)

    def on_end_focus_out(self, event):
        self.event_handlers.on_end_focus_out(event)

    def on_end_return(self, event):
        self.event_handlers.on_end_return(event)

    def reset_application(self):
        # 移除激活检查，允许未激活状态下重置应用
        self.df = None
        self.full_view_data = None
        self.current_plot_data = None  # 重置当前图表数据

        # 清空Max/Min数据
        self.max_value = None
        self.min_value = None
        self.max_date_str = None
        self.min_date_str = None

        self.chart_utils.initialize_chart()

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

        self.components["custom_range_start_label"].config(text="--")
        self.components["custom_range_end_label"].config(text="")
        self.components["custom_days_label"].config(text="--")
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
        self.log("欢迎使用业绩表现回测工具", "success")
        self.log("请导入文件开始使用", "success")
        self.log("rizona.cn@gmail.com", "success")

    def show_readme(self):
        self.window_utils.show_readme(self)

    def show_activation(self):
        self.window_utils.show_activation(self)

    def close_readme(self, window):
        self.window_utils.close_readme(window)

    def import_data(self):
        # 移除激活检查，允许未激活状态下导入文件
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

            self.components["custom_range_start_label"].config(text="--")
            self.components["custom_range_end_label"].config(text="")
            self.components["custom_days_label"].config(text="--")
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
        if not self.is_activated:
            messagebox.showwarning("警告", "软件未激活，无法使用此功能")
            return
            
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
        if not self.event_handlers._validate_dates(self.components["start_entry"]) or not self.event_handlers._validate_dates(self.components["end_entry"]):
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

            self.components["custom_range_start_label"].config(
                text=f"{result['start_date'].strftime('%Y-%m-%d')}"
            )
            self.components["custom_range_end_label"].config(
                text=f"{result['end_date'].strftime('%Y-%m-%d')}"
            )
            self.components["custom_days_label"].config(text=f"{result['days']}天")

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
        if not self.is_activated:
            messagebox.showwarning("警告", "软件未激活，无法使用此功能")
            return
            
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

        self.components["custom_range_start_label"].config(text="--")
        self.components["custom_range_end_label"].config(text="")
        self.components["custom_days_label"].config(text="--")
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
        if self.chart_utils.hover_line_x:
            try:
                self.chart_utils.hover_line_x.remove()
            except:
                pass
            self.chart_utils.hover_line_x = None

        if self.chart_utils.hover_line_y:
            try:
                self.chart_utils.hover_line_y.remove()
            except:
                pass
            self.chart_utils.hover_line_y = None

        if self.chart_utils.hover_marker:
            try:
                self.chart_utils.hover_marker.remove()
            except:
                pass
            self.chart_utils.hover_marker = None

        if self.chart_utils.hover_text_obj:
            try:
                self.chart_utils.hover_text_obj.remove()
            except:
                pass
            self.chart_utils.hover_text_obj = None

        # 每次重绘图表，都清空并重新绘制 Max/Min 文本和标记
        if self.chart_utils.max_min_text_obj:
            for text_obj in self.chart_utils.max_min_text_obj:
                try:
                    text_obj.remove()
                except:
                    pass
            self.chart_utils.max_min_text_obj = []

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

        # 检查是否显示文本框
        if self.config.get("show_textbox", True):
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
            self.chart_utils.max_min_text_obj = [max_text_obj, min_text_obj]

        # 设置图表格式
        self.chart_utils.setup_chart_formatting(df_plot)

        self.canvas.draw()
        self.log("净值趋势图生成完成", "success")

    def export_chart(self):
        if not self.is_activated:
            messagebox.showwarning("警告", "软件未激活，无法使用此功能")
            return
            
        if not hasattr(self, 'figure') or not self.figure:
            messagebox.showwarning("警告", "没有可导出的图表")
            return

        # 使用当前程序目录
        export_dir = os.getcwd()
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        if self.current_start_date and self.current_end_date:
            if self.current_start_date.year == self.current_end_date.year:
                filename = (
                    f"{self.current_start_date.year}--"
                    f"{self.current_start_date.strftime('%m%d')}～"
                    f"{self.current_end_date.strftime('%m%d')}净值趋势图.png"
                )
            else:
                filename = (
                    f"{self.current_start_date.strftime('%y%m%d')}～"
                    f"{self.current_end_date.strftime('%y%m%d')}净值趋势图.png"
                )
        else:
            filename = "净值趋势图.png"

        file_path = os.path.join(export_dir, filename)

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

    def clear_log_text(self):
        """清空日志内容"""
        for log_text in self.log_texts.values():
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            log_text.config(state=tk.DISABLED)

    def set_export_chart_settings(self):
        """设置导出图表选项"""
        if not self.is_activated:
            messagebox.showwarning("警告", "软件未激活，无法使用此功能")
            return
            
        if self.df is None or len(self.df) == 0:
            messagebox.showwarning("警告", "请先导入数据文件！")
            self.log("设置导出图表失败: 无数据", "warning")
            return

        settings_window = tk.Toplevel(self.root)
        settings_window.title("导出图表设置")
        settings_window.geometry("210x130")  # 增加高度以容纳更多内容
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # 设置窗口居中显示
        self.center_window_relative(settings_window, self.root)

        main_frame = ttk.Frame(settings_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 按钮框架 - 提前定义
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        # 悬停数据显示选项
        hover_var = tk.BooleanVar(value=self.config.get("show_hover_data"))
        hover_date_var = tk.StringVar(value=self.config.get("hover_date"))

        def validate_date_format():
            date_str = hover_date_entry.get().strip()
            if not date_str:
                return True
            
            try:
                normalized_date = normalize_date_string(date_str, self.log)
                datetime.strptime(normalized_date, "%Y-%m-%d")
                hover_date_entry.configure(foreground=self.config.colors["text"])
                return True
            except ValueError:
                hover_date_entry.configure(foreground="red")
                return False

        def validate_date_range():
            if not validate_date_format():
                return False
            
            date_str = hover_date_entry.get().strip()
            try:
                normalized_date = normalize_date_string(date_str, self.log)
                hover_date = datetime.strptime(normalized_date, "%Y-%m-%d")

                # 检查日期是否在数据范围内
                if self.df is not None and len(self.df) > 0:
                    min_date = self.df['日期'].min()
                    max_date = self.df['日期'].max()
                    if hover_date < min_date or hover_date > max_date:
                        # 显示错误提示
                        error_window = tk.Toplevel(settings_window)
                        error_window.title("错误")
                        error_window.geometry("210x130")
                        error_window.resizable(False, False)
                        error_window.transient(settings_window)
                        error_window.grab_set()

                        # 居中显示错误窗口
                        self.center_window_relative(error_window, settings_window)
                    
                        error_msg = f"悬停日期必须在数据日期范围内: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}"
                        label = tk.Label(error_window, text=error_msg, wraplength=180, justify=tk.LEFT)
                        label.pack(padx=10, pady=10)
                        tk.Button(error_window, text="确定", command=error_window.destroy, width=10).pack(pady=10)
                        return False
                return True
            except:
                return False

        def on_hover_date_change(*args):
            validate_date_format()

        hover_date_var.trace('w', on_hover_date_change)

        def toggle_hover_date():
            if hover_var.get():
                hover_date_frame.pack(fill=tk.X, pady=(5, 0))
                # 立即验证日期范围
                validate_date_range()
            else:
                hover_date_frame.pack_forget()
                # 关闭悬停数据时，立即清除图表上的悬停标记
                self.chart_utils.remove_hover_date_marker()

        hover_check = ttk.Checkbutton(
            main_frame,
            text="悬停数据开启/关闭",
            variable=hover_var,
            command=toggle_hover_date
        )
        hover_check.pack(anchor=tk.W)

        # 悬停日期输入框
        hover_date_frame = ttk.Frame(main_frame)
        if hover_var.get():
            hover_date_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(hover_date_frame, text="悬停日期:").pack(side=tk.LEFT, padx=(20, 5))
        hover_date_entry = ttk.Entry(hover_date_frame, textvariable=hover_date_var, width=15)
        hover_date_entry.pack(side=tk.LEFT)
        hover_date_entry.bind("<FocusOut>", lambda e: validate_date_range())

        def save_settings():
            if hover_var.get():
                if not validate_date_format() or not validate_date_range():
                    return
                self.config.set("show_hover_data", True)
                self.config.set("hover_date", normalize_date_string(hover_date_var.get(), self.log))
                # 设置悬停日期后，立即在图表上显示交叉线
                self.chart_utils.update_chart_with_hover_date()
            else:
                self.config.set("show_hover_data", False)
                self.config.set("hover_date", "")
                # 清除悬停日期标记
                self.chart_utils.remove_hover_date_marker()
            settings_window.destroy()
            self.log("导出图表设置已保存", "success")

        def cancel_settings():
            settings_window.destroy()

        ttk.Button(button_frame, text="确定", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings).pack(side=tk.RIGHT)

        # 初始显示状态
        toggle_hover_date()

    def set_export_directory(self):
        """设置导出目录"""
        if not self.is_activated:
            messagebox.showwarning("警告", "软件未激活，无法使用此功能")
            return
            
        settings_window = tk.Toplevel(self.root)
        settings_window.title("导出目录设置")
        settings_window.geometry("210x170")  
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # 设置窗口居中显示
        self.center_window_relative(settings_window, self.root)

        main_frame = ttk.Frame(settings_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 按钮框架 - 提前定义
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        # 当前目录选项
        current_dir_var = tk.BooleanVar(value=self.config.get("export_directory") == os.getcwd())
        
        # 存储当前选择的目录
        selected_dir = tk.StringVar(value=self.config.get("export_directory"))
        
        def toggle_directory_options():
            if current_dir_var.get():
                # 选择当前目录
                selected_dir.set(os.getcwd())
                custom_dir_frame.pack_forget()
            else:
                # 选择自定义目录
                custom_dir_frame.pack(fill=tk.X, pady=(5, 0))
                # 如果还没有选择过自定义目录，使用当前配置
                if selected_dir.get() == os.getcwd():
                    selected_dir.set(self.config.get("export_directory"))

        def browse_directory():
            directory = filedialog.askdirectory(initialdir=selected_dir.get())
            if directory:
                selected_dir.set(directory)
                # 更新工具提示
                custom_dir_radio.tooltip.update_text(directory)

        current_dir_radio = ttk.Radiobutton(
            main_frame,
            text="保存到当前目录",
            variable=current_dir_var,
            value=True,
            command=toggle_directory_options
        )
        current_dir_radio.pack(anchor=tk.W, pady=(5, 0))

        # 自定义目录选项
        custom_dir_radio = ttk.Radiobutton(
            main_frame,
            text="自定义保存位置",
            variable=current_dir_var,
            value=False,
            command=toggle_directory_options
        )
        custom_dir_radio.pack(anchor=tk.W, pady=(5, 0))

        # 为自定义目录单选按钮添加工具提示
        custom_dir_radio.tooltip = ToolTip(custom_dir_radio, selected_dir.get())

        # 自定义目录框架
        custom_dir_frame = ttk.Frame(main_frame)
        if not current_dir_var.get():
            custom_dir_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 浏览按钮
        browse_button = ttk.Button(
            custom_dir_frame, 
            text="选择目录",
            command=browse_directory,
            width=10
        )
        browse_button.pack(side=tk.LEFT, padx=(20, 5))
        
        def save_settings():
            if current_dir_var.get():
                self.config.set("export_directory", os.getcwd())
            else:
                self.config.set("export_directory", selected_dir.get())
            settings_window.destroy()
            self.log(f"导出目录已设置为: {self.config.get('export_directory')}", "success")

        def cancel_settings():
            settings_window.destroy()

        ttk.Button(button_frame, text="确定", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings).pack(side=tk.RIGHT)

        # 初始显示状态
        toggle_directory_options()

    def set_textbox_settings(self):
        """设置提示框位置"""
        if not self.is_activated:
            messagebox.showwarning("警告", "软件未激活，无法使用此功能")
            return
            
        settings_window = tk.Toplevel(self.root)
        settings_window.title("提示框设置")
        settings_window.geometry("210x130")  # 调整大小
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # 设置窗口居中显示
        self.center_window_relative(settings_window, self.root)

        main_frame = ttk.Frame(settings_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 按钮框架 - 提前定义
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        # 提示框启用选项
        show_textbox_var = tk.BooleanVar(value=self.config.get("show_textbox", True))

        def toggle_position_options():
            if show_textbox_var.get():
                position_frame.pack(fill=tk.X, pady=(10, 0))
            else:
                position_frame.pack_forget()

        ttk.Checkbutton(
            main_frame,
            text="开启/关闭提示框",
            variable=show_textbox_var,
            command=toggle_position_options
        ).pack(anchor=tk.W)

        # 位置选项
        position_frame = ttk.Frame(main_frame)
        if show_textbox_var.get():
            position_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(position_frame, text="位置:").pack(side=tk.LEFT, padx=(20, 5))
        
        # 位置映射
        position_map = {
            "左上角": "top-left",
            "右上角": "top-right",
            "左下角": "bottom-left",
            "右下角": "bottom-right"
        }
        
        # 反向映射，用于设置当前值
        reverse_position_map = {v: k for k, v in position_map.items()}
        
        position_var = tk.StringVar(value=reverse_position_map.get(self.config.get("max_min_position", "top-left"), "左上角"))
        position_combo = ttk.Combobox(
            position_frame,
            textvariable=position_var,
            values=list(position_map.keys()),
            state="readonly",
            width=15
        )
        position_combo.pack(side=tk.LEFT)

        def save_settings():
            self.config.set("show_textbox", show_textbox_var.get())
            if show_textbox_var.get():
                self.config.set("max_min_position", position_map[position_var.get()])
            settings_window.destroy()
            self.log("提示框设置已保存", "success")

            # 重新绘制图表以应用新设置
            if self.df is not None and len(self.df) > 0:
                self.analyze_performance()

        def cancel_settings():
            settings_window.destroy()

        ttk.Button(button_frame, text="确定", command=save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings).pack(side=tk.RIGHT)

        # 初始显示状态
        toggle_position_options()

if __name__ == "__main__":
    root = tk.Tk()
    app = PerformanceBacktestTool(root)
    root.mainloop()