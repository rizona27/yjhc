import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from matplotlib.ticker import StrMethodFormatter, MaxNLocator
import sys
import chardet
import os
import numpy as np
import matplotlib.font_manager as fm
import warnings
import re
from dateutil.parser import parse as dateutil_parse
import psutil  # 新增：用于进程管理

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
        self.root.resizable(True, True)
        
        # 设置程序图标
        try:
            self.root.iconbitmap('app.ico')
        except:
            pass
            
        # 窗口关闭事件处理 - 修改为调用cleanup_exit
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup_exit)
        
        self.df = None
        self.chart_title = "净值趋势图"
        self.full_view_data = None
        self.current_start_date = None  # 新增：当前图表的开始日期
        self.current_end_date = None    # 新增：当前图表的结束日期
        
        # 更新为更明亮、更鲜明的配色方案
        self.colors = {
            "background": "#F5F8FA",        # 更亮的背景色
            "card": "#FFFFFF",              # 卡片白色
            "primary": "#2C3E50",           # 深蓝灰
            "primary_hover": "#34495E",     # 更深的蓝灰
            "secondary": "#7F8C8D",         # 中性灰
            "accent": "#5B9BD5",            # 按钮蓝色 #5B9BD5
            "text": "#2C3E50",              # 文字色 #2C3E50
            "text_light": "#7F8C8D",        # 浅灰文字
            "chart_line": "#2980B9",        # 深蓝色
            "chart_marker": "#C0392B",      # 深红色
            "chart_grid": "#D5DBDB",        # 浅灰色网格
            "chart_bg": "#FFFFFF",          # 白色图表背景
            "button": "#5B9BD5",            # 按钮蓝色 #5B9BD5
            "button_hover": "#4A8BC5",      # 按钮悬停蓝色
            "highlight": "#4682B4",         # 高亮色 #4682B4
            "status_bar": "#E0E8F0",        # 状态栏背景
            "group_box": "#E6F0F8",         # 分组框背景
            "border": "#A0C0E0",            # 边框色
            "input_bg": "#FFFFFF",          # 输入框背景色
            "placeholder": "#AAAAAA"        # 占位符文本颜色
        }
        
        # 设置全局样式
        self.root.configure(bg=self.colors["background"])
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 配置全局样式
        self.style.configure(".", background=self.colors["background"])
        self.style.configure("TFrame", background=self.colors["background"])
        self.style.configure("TLabel", background=self.colors["background"], foreground=self.colors["text"])
        self.style.configure("TEntry", fieldbackground=self.colors["input_bg"], foreground=self.colors["text"])
        self.style.configure("TLabelframe", background=self.colors["background"], bordercolor=self.colors["border"])
        self.style.configure("TLabelframe.Label", background=self.colors["background"], foreground=self.colors["primary"])
        
        # 配置按钮样式 - 添加圆角效果
        self.style.configure("TButton", 
                            font=("Helvetica", 9),
                            padding=5,
                            background=self.colors["button"],
                            foreground="white",
                            borderwidth=1,
                            relief="flat",
                            bordercolor=self.colors["button"])
        
        # 添加按钮悬停效果
        self.style.map("TButton", 
                      background=[("active", self.colors["button_hover"])],
                      relief=[("active", "groove")])
        
        # 配置标签框架样式
        self.style.configure("TLabelframe", 
                            background=self.colors["background"],
                            bordercolor=self.colors["border"],
                            borderwidth=1,
                            relief="groove")
        self.style.configure("TLabelframe.Label", 
                            foreground=self.colors["primary"],
                            font=("Helvetica", 9, "bold"))
        
        # 配置Treeview样式
        self.style.configure("Treeview",
                            background=self.colors["card"],
                            foreground=self.colors["text"],
                            fieldbackground=self.colors["card"],
                            borderwidth=1,
                            font=("Helvetica", 9))
        
        self.style.configure("Treeview.Heading",
                            background=self.colors["group_box"],
                            foreground=self.colors["primary"],
                            font=("Helvetica", 9, "bold"),
                            relief="flat")
        
        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        main_frame.configure(style="TFrame")
        
        # 顶部区域 - 分为左右两部分
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        top_frame.configure(style="TFrame")
        
        # 左侧命令区 - 配置区
        self.cmd_frame = ttk.LabelFrame(top_frame, text="配置区", width=180)
        self.cmd_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        self.cmd_frame.configure(style="TLabelframe")
        
        # 按钮区域 - 上半部分
        btn_frame = ttk.Frame(self.cmd_frame)
        btn_frame.pack(padx=5, pady=5, fill=tk.X)
        btn_frame.configure(style="TFrame")
        
        # 导入按钮
        self.btn_import = ttk.Button(
            btn_frame, 
            text="导入数据", 
            command=self.import_data,
            style="TButton"
        )
        self.btn_import.pack(fill=tk.X, pady=3)
        
        # 导出按钮
        self.btn_export = ttk.Button(
            btn_frame, 
            text="导出图表", 
            state=tk.DISABLED, 
            command=self.export_chart,
            style="TButton"
        )
        self.btn_export.pack(fill=tk.X, pady=3)
        
        # 底部按钮容器
        bottom_btn_frame = ttk.Frame(btn_frame)
        bottom_btn_frame.pack(fill=tk.X, pady=3)
        bottom_btn_frame.configure(style="TFrame")
        
        # 添加重置按钮（左侧）
        self.btn_reset_app = ttk.Button(
            bottom_btn_frame, 
            text="重置应用", 
            command=self.reset_application,
            style="TButton"
        )
        self.btn_reset_app.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        
        # 添加使用说明按钮（右侧，与重置按钮同样大小）
        self.btn_readme = ttk.Button(
            bottom_btn_frame, 
            text="说明", 
            command=self.show_readme,
            style="TButton"
        )
        self.btn_readme.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(3, 0))
        
        # 自定义日期区间分析 - 下半部分
        custom_frame = ttk.LabelFrame(self.cmd_frame, text="自定义日期区间")
        custom_frame.pack(fill=tk.X, padx=5, pady=(5, 0), expand=True)
        custom_frame.configure(style="TLabelframe")
        
        # 开始日期选择
        start_frame = ttk.Frame(custom_frame)
        start_frame.pack(fill=tk.X, padx=3, pady=3)
        start_frame.configure(style="TFrame")
        
        ttk.Label(start_frame, text="开始日期:", width=8, 
                 style="TLabel").pack(side=tk.LEFT)
        
        # 使用普通输入框替代DateEntry
        self.start_entry = ttk.Entry(start_frame, width=12, style="TEntry")
        self.start_entry.pack(side=tk.LEFT, padx=3)
        self.start_entry.insert(0, "YYYY-MM-DD")
        self.start_entry.configure(foreground=self.colors["placeholder"])
        
        # 绑定事件
        self.start_entry.bind("<FocusIn>", self.on_start_focus_in)
        self.start_entry.bind("<FocusOut>", self.on_start_focus_out)
        self.start_entry.bind("<Return>", self.on_start_return)
        
        # 结束日期选择
        end_frame = ttk.Frame(custom_frame)
        end_frame.pack(fill=tk.X, padx=3, pady=3)
        end_frame.configure(style="TFrame")
        
        ttk.Label(end_frame, text="结束日期:", width=8, 
                 style="TLabel").pack(side=tk.LEFT)
        
        self.end_entry = ttk.Entry(end_frame, width=12, style="TEntry")
        self.end_entry.pack(side=tk.LEFT, padx=3)
        self.end_entry.insert(0, "YYYY-MM-DD")
        self.end_entry.configure(foreground=self.colors["placeholder"])
        
        # 绑定事件
        self.end_entry.bind("<FocusIn>", self.on_end_focus_in)
        self.end_entry.bind("<FocusOut>", self.on_end_focus_out)
        self.end_entry.bind("<Return>", self.on_end_return)
        
        # 分析按钮和恢复全览按钮
        button_container = ttk.Frame(custom_frame)
        button_container.pack(fill=tk.X, padx=3, pady=(0, 3))
        button_container.configure(style="TFrame")
        
        # 使用grid布局使按钮等宽
        self.btn_custom = ttk.Button(
            button_container, 
            text="分析区间", 
            command=self.custom_analysis,
            style="TButton"
        )
        self.btn_custom.grid(row=0, column=0, padx=(0, 5), sticky='ew')
        
        self.btn_reset = ttk.Button(
            button_container, 
            text="恢复全览", 
            command=self.reset_to_full_view,
            state=tk.DISABLED,
            style="TButton"
        )
        self.btn_reset.grid(row=0, column=1, sticky='ew')
        
        # 配置列权重使按钮等宽
        button_container.columnconfigure(0, weight=1)
        button_container.columnconfigure(1, weight=1)
        
        # 右侧分析区
        self.analysis_frame = ttk.Frame(top_frame)
        self.analysis_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.analysis_frame.configure(style="TFrame")
        
        # 创建水平布局容器
        analysis_horizontal_frame = ttk.Frame(self.analysis_frame)
        analysis_horizontal_frame.pack(fill=tk.BOTH, expand=True)
        analysis_horizontal_frame.configure(style="TFrame")
        
        # 左侧：固定周期回测区
        fixed_freq_frame = ttk.LabelFrame(analysis_horizontal_frame, text="固定周期回测")
        fixed_freq_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        fixed_freq_frame.configure(style="TLabelframe")
        
        # 使用Treeview显示固定周期结果
        columns = ("freq", "days", "return", "drawdown")
        self.result_tree = ttk.Treeview(
            fixed_freq_frame, 
            columns=columns, 
            show="headings",
            height=8,
            selectmode="none"
        )
        
        # 设置列标题 - 移除悬停特效
        self.result_tree.heading("freq", text="周期", anchor=tk.W)
        self.result_tree.heading("days", text="天数", anchor=tk.CENTER)
        self.result_tree.heading("return", text="年化收益率", anchor=tk.CENTER)
        self.result_tree.heading("drawdown", text="最大回撤", anchor=tk.CENTER)
        
        # 设置初始列宽
        self.result_tree.column("freq", width=70, anchor=tk.W, stretch=False)
        self.result_tree.column("days", width=50, anchor=tk.CENTER, stretch=False)
        self.result_tree.column("return", width=80, anchor=tk.CENTER, stretch=False)
        self.result_tree.column("drawdown", width=80, anchor=tk.CENTER, stretch=False)
        
        # 布局
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 右侧容器
        right_container = ttk.Frame(analysis_horizontal_frame)
        right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_container.configure(style="TFrame")
        
        # 自定义周期回测区
        custom_result_frame = ttk.LabelFrame(right_container, text="自定义周期回测")
        custom_result_frame.pack(fill=tk.BOTH, expand=True)
        custom_result_frame.configure(style="TLabelframe")
        
        # 自定义区间结果标签 - 使用更大的字体
        self.custom_result_container = ttk.Frame(custom_result_frame)
        self.custom_result_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.custom_result_container.configure(style="TFrame")
        
        # 初始化自定义结果标签 - 增大字体
        self.custom_range_label = ttk.Label(
            self.custom_result_container, 
            text="日期范围: --",
            font=("Helvetica", 9),  # 增大字体
            style="TLabel"
        )
        self.custom_range_label.pack(anchor=tk.W, pady=3)  # 增加垂直间距
        
        self.custom_days_label = ttk.Label(
            self.custom_result_container, 
            text="周期天数: --",  # 修改为周期天数
            font=("Helvetica", 9),  # 增大字体
            style="TLabel"
        )
        self.custom_days_label.pack(anchor=tk.W, pady=3)  # 增加垂直间距
        
        self.custom_return_label = ttk.Label(
            self.custom_result_container, 
            text="年化收益率: --",
            font=("Helvetica", 9),  # 增大字体
            style="TLabel"
        )
        self.custom_return_label.pack(anchor=tk.W, pady=3)  # 增加垂直间距
        
        self.custom_drawdown_label = ttk.Label(
            self.custom_result_container, 
            text="最大回撤: --",
            font=("Helvetica", 9),  # 增大字体
            style="TLabel"
        )
        self.custom_drawdown_label.pack(anchor=tk.W, pady=3)  # 增加垂直间距
        
        # 系统日志区域
        log_frame = ttk.LabelFrame(right_container, text="系统日志")  # 修改为系统日志
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(3, 0))
        log_frame.configure(style="TLabelframe")
        
        # 添加滚动条
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            height=3,
            font=("Courier", 8),
            bg=self.colors["card"],
            fg=self.colors["text"],
            borderwidth=1,
            relief="solid"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        self.log_text.config(state=tk.DISABLED)
        
        # 添加右键菜单用于复制
        self.log_text.bind("<Button-3>", self.show_log_context_menu)
        self.log_context_menu = tk.Menu(self.log_text, tearoff=0)
        self.log_context_menu.add_command(label="复制", command=self.copy_log_text)
        
        # 解决中文字体问题
        self.setup_fonts()
        
        # 底部区域 - 净值趋势图
        self.chart_frame = ttk.LabelFrame(main_frame, text="净值趋势图")
        self.chart_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        self.chart_frame.configure(style="TLabelframe")
        
        # 创建图表 - 使用固定大小
        self.figure, self.ax = plt.subplots(figsize=(8, 3.0), dpi=100)  # 增加高度
        self.figure.patch.set_facecolor(self.colors["background"])
        self.ax.set_facecolor(self.colors["chart_bg"])
        
        self.canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 初始化图表 - 确保与导入数据后大小一致
        self.initialize_chart()
        
        # 添加初始日志
        self.log("欢迎使用业绩表现回测工具")
        self.log("请导入文件开始使用")
        self.log(f"rizona.cn@gmail.com")  # 修复邮箱显示问题
        
    def show_log_context_menu(self, event):
        """显示日志上下文菜单"""
        self.log_context_menu.tk_popup(event.x_root, event.y_root)
    
    def copy_log_text(self):
        """复制选中的日志文本"""
        try:
            selected_text = self.log_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
        except:
            pass
    
    def cleanup_exit(self):
        """清理资源并完全退出程序"""
        global OPEN_WINDOWS
        OPEN_WINDOWS -= 1
        
        # 关闭所有matplotlib图形
        plt.close('all')
        
        # 销毁Tkinter窗口
        self.root.destroy()
        
        # 强制退出所有子进程
        self.terminate_child_processes()
        
        # 完全退出Python进程
        sys.exit(0)
    
    def terminate_child_processes(self):
        """终止所有子进程"""
        current_pid = os.getpid()
        try:
            parent = psutil.Process(current_pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            gone, still_alive = psutil.wait_procs(children, timeout=3)
            for p in still_alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
        except Exception as e:
            print(f"终止子进程时出错: {str(e)}")
    
    # 日期输入框事件处理函数
    def on_start_focus_in(self, event):
        """开始日期获得焦点事件"""
        if self.start_entry.get() == "YYYY-MM-DD":
            self.start_entry.delete(0, tk.END)
            self.start_entry.configure(foreground=self.colors["text"])
    
    def on_start_focus_out(self, event):
        """开始日期失去焦点事件"""
        if not self.start_entry.get():
            self.start_entry.insert(0, "YYYY-MM-DD")
            self.start_entry.configure(foreground=self.colors["placeholder"])
    
    def on_start_return(self, event):
        """开始日期回车键事件"""
        # 如果结束日期有内容且有效，则提交分析
        if self.end_entry.get() and self.end_entry.get() != "YYYY-MM-DD":
            self.custom_analysis()
        else:
            # 否则跳到结束日期
            self.end_entry.focus()
            self.end_entry.select_range(0, tk.END)
    
    def on_end_focus_in(self, event):
        """结束日期获得焦点事件"""
        if self.end_entry.get() == "YYYY-MM-DD":
            self.end_entry.delete(0, tk.END)
            self.end_entry.configure(foreground=self.colors["text"])
    
    def on_end_focus_out(self, event):
        """结束日期失去焦点事件"""
        if not self.end_entry.get():
            self.end_entry.insert(0, "YYYY-MM-DD")
            self.end_entry.configure(foreground=self.colors["placeholder"])
    
    def on_end_return(self, event):
        """结束日期回车键事件"""
        # 如果开始日期和结束日期都有内容且有效，则提交分析
        if (self.start_entry.get() and self.start_entry.get() != "YYYY-MM-DD" and
            self.end_entry.get() and self.end_entry.get() != "YYYY-MM-DD"):
            self.custom_analysis()
        elif self.start_entry.get() and self.start_entry.get() != "YYYY-MM-DD":
            # 否则如果开始日期有内容，提交分析
            self.custom_analysis()
        else:
            # 否则跳到开始日期
            self.start_entry.focus()
            self.start_entry.select_range(0, tk.END)

    def reset_application(self):
        """重置整个应用程序到初始状态"""
        self.df = None
        self.full_view_data = None
        
        # 重置图表 - 确保大小一致
        self.initialize_chart()
        
        # 清空Treeview
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 清空自定义分析结果
        self.custom_range_label.config(text="日期范围: --")
        self.custom_days_label.config(text="周期天数: --")
        self.custom_return_label.config(text="年化收益率: --")
        self.custom_drawdown_label.config(text="最大回撤: --")
        
        # 重置日期输入框
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, "YYYY-MM-DD")
        self.start_entry.configure(foreground=self.colors["placeholder"])
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, "YYYY-MM-DD")
        self.end_entry.configure(foreground=self.colors["placeholder"])
        
        # 禁用按钮
        self.btn_export['state'] = tk.DISABLED
        self.btn_reset['state'] = tk.DISABLED
        
        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 添加初始日志
        self.log("应用已重置")
        self.log("欢迎使用业绩表现回测工具")
        self.log("请导入文件开始使用")
        self.log(f"rizona.cn@gmail.com")  # 修复邮箱显示问题

    def show_readme(self):
        """显示使用说明 - 使用滚动文本框"""
        # 创建使用说明窗口
        readme_window = tk.Toplevel(self.root)
        readme_window.title("使用说明")
        readme_window.geometry("500x400")  # 减小窗口尺寸
        readme_window.resizable(False, False)
        readme_window.configure(bg=self.colors["background"])
        
        # 设置模态窗口
        readme_window.grab_set()
        readme_window.transient(self.root)
        
        # 主框架
        main_frame = ttk.Frame(readme_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加滚动文本框
        scroll_frame = ttk.Frame(main_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建文本框
        text_area = tk.Text(
            scroll_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Helvetica", 10),
            borderwidth=1,
            relief="solid",
            padx=10,
            pady=10
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_area.yview)
        
        # 添加内容
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

4. 导出功能
  - 可以区间命名导出净值趋势图

5. 其他功能
  - 恢复全览：返回完整数据视图
  - 系统日志：记录操作过程

使用提示：
  - 日期格式支持多种形式[YYYY-MM-DD/YYYYMMDD]
  - 如有需适配功能，可联系作者:rizona.cn@gmail.com
"""
        text_area.insert(tk.INSERT, readme_text)
        
        # 添加作者信息 - 使用标签样式
        author_frame = ttk.Frame(main_frame)
        author_frame.pack(fill=tk.X, pady=(0, 5))
        
        author_label = ttk.Label(
            author_frame, 
            text="rizona.cn@gmail.com",
            font=("Helvetica", 10),
            foreground=self.colors["accent"],
            background=self.colors["card"]
        )
        author_label.pack(side=tk.BOTTOM)
        
        # 添加关闭按钮
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
        """关闭说明窗口"""
        window.grab_release()
        window.destroy()

    def log(self, message):
        """添加日志信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
    
    def setup_fonts(self):
        """设置跨平台中文字体支持"""
        font_list = [
            'SimHei',        # Windows
            'Microsoft YaHei', # Windows
            'PingFang SC',   # macOS
            'Heiti SC',      # macOS
            'STHeiti',       # macOS
            'WenQuanYi Zen Hei', # Linux
            'WenQuanYi Micro Hei', # Linux
            'sans-serif'     # 最后回退
        ]
        
        available_fonts = fm.findSystemFonts(fontpaths=None, fontext='ttf')
        chinese_font = None
        
        for font_name in font_list:
            for font_path in available_fonts:
                if font_name.lower() in os.path.basename(font_path).lower():
                    chinese_font = font_path
                    break
            if chinese_font:
                break
        
        if chinese_font:
            font_prop = fm.FontProperties(fname=chinese_font)
            plt.rcParams['font.family'] = font_prop.get_name()
        else:
            plt.rcParams['font.family'] = 'sans-serif'
        
        plt.rcParams['axes.unicode_minus'] = False
    
    def detect_file_type(self, file_path):
        """检测文件类型"""
        try:
            extension = os.path.splitext(file_path)[1].lower()
            
            if extension in ['.xlsx', '.xls']:
                return 'excel'
                
            with open(file_path, 'rb') as f:
                header = f.read(4)
                
                if header == b'PK\x03\x04' or header == b'\xD0\xCF\x11\xE0':
                    return 'excel'
                
                return 'csv'
        
        except Exception as e:
            self.log(f"文件类型检测失败: {str(e)}")
            return 'csv'
    
    def clean_numeric_string(self, value):
        """清理数值字符串，移除非数字字符"""
        try:
            if isinstance(value, (int, float)):
                return value
                
            s = str(value).strip()
            s = s.replace(',', '').replace('，', '').replace(' ', '')
            cleaned = re.sub(r'[^\d\.\-]', '', s)
            
            if cleaned == '' or cleaned == '-':
                return np.nan
                
            return cleaned
        except:
            return np.nan
    
    def parse_dates(self, date_series):
        """解析日期格式 - 增强版 (移除infer_datetime_format参数)"""
        # 修复弃用警告：移除infer_datetime_format参数
        parsed_dates = pd.to_datetime(date_series, errors='coerce')
        
        na_mask = parsed_dates.isna()
        if not na_mask.any():
            return parsed_dates
        
        self.log(f"发现 {na_mask.sum()} 个日期需要特殊解析")
        
        date_formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%d/%m/%Y', '%d-%m-%Y', 
            '%m/%d/%Y', '%m-%d-%Y', '%Y年%m月%d日', '%d.%m.%Y', '%b %d, %Y', 
            '%B %d, %Y', '%y-%m-%d', '%y/%m/%d', '%m/%d/%y', '%m-%d-%y',
            '%d/%m/%y', '%d-%m-%y', '%Y.%m.%d', '%m.%d.%Y', '%d.%m.%y', '%Y_%m_%d'
        ]
        
        unparsed = date_series[na_mask]
        
        def clean_date(date_str):
            if not isinstance(date_str, str):
                date_str = str(date_str)
            date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
            date_str = re.sub(r'[^\d\-/\.年月日]', '', date_str)
            return date_str.strip()
        
        unparsed = unparsed.apply(clean_date)
        
        for date_fmt in date_formats:
            if unparsed.empty:
                break
                
            try:
                temp_parsed = pd.to_datetime(unparsed, format=date_fmt, errors='coerce')
                success_mask = temp_parsed.notna()
                if success_mask.any():
                    parsed_dates.loc[unparsed[success_mask].index] = temp_parsed[success_mask]
                    self.log(f"使用格式 '{date_fmt}' 成功解析 {success_mask.sum()} 个日期")
                    unparsed = unparsed[~success_mask]
            except Exception as e:
                self.log(f"尝试格式 '{date_fmt}' 时出错: {str(e)}")
        
        if not unparsed.empty:
            temp_parsed = unparsed.apply(dateutil_parse)
            success_mask = temp_parsed.notna()
            if success_mask.any():
                parsed_dates.loc[unparsed[success_mask].index] = temp_parsed[success_mask]
                self.log(f"使用灵活解析成功解析 {success_mask.sum()} 个日期")
        
        return parsed_dates
    
    def read_csv_file(self, file_path):
        """读取CSV文件"""
        encodings = ['utf-8', 'gbk', 'gb18030', 'latin1', 'cp1252', 'utf-16']
        
        for enc in encodings:
            try:
                test_df = pd.read_csv(file_path, encoding=enc, nrows=100)
                self.log(f"测试编码 {enc} 成功，列数: {len(test_df.columns)}")
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='warn')
                self.log(f"成功读取CSV文件: {len(df)}行 (编码: {enc})")
                return df
            except Exception as ex:
                self.log(f"编码 {enc} 失败: {str(ex)}")
        
        messagebox.showerror("错误", "无法读取CSV文件，请检查文件编码")
        self.log("读取CSV文件失败: 所有编码尝试均失败")
        return None
    
    def read_excel_file(self, file_path):
        """读取Excel文件"""
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            self.log(f"成功读取Excel文件: {len(df)}行")
            return df
        except Exception as e:
            try:
                df = pd.read_excel(file_path, engine='xlrd')
                self.log(f"成功读取Excel文件: {len(df)}行 (使用xlrd引擎)")
                return df
            except:
                try:
                    df = pd.read_excel(file_path, engine='odf')
                    self.log(f"成功读取Excel文件: {len(df)}行 (使用odf引擎)")
                    return df
                except:
                    messagebox.showerror("错误", f"无法读取Excel文件:\n{str(e)}")
                    self.log(f"读取Excel文件失败: {str(e)}")
                    return None
    
    def normalize_date_string(self, date_str):
        """标准化日期字符串为YYYY-MM-DD格式"""
        try:
            # 如果已经是YYYY-MM-DD格式，直接返回
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                return date_str
            
            # 处理YYYYMMDD格式
            if re.match(r'^\d{8}$', date_str):
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            
            # 处理YYMMDD格式 - 假设20YY
            if re.match(r'^\d{6}$', date_str):
                return f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}"
            
            # 处理YYYY/MM/DD格式
            if re.match(r'^\d{4}/\d{2}/\d{2}$', date_str):
                return date_str.replace("/", "-")
            
            # 处理YYYY.MM.DD格式
            if re.match(r'^\d{4}\.\d{2}\.\d{2}$', date_str):
                return date_str.replace(".", "-")
            
            # 尝试使用dateutil解析
            dt = dateutil_parse(date_str)
            return dt.strftime("%Y-%m-%d")
        
        except Exception as e:
            self.log(f"无法解析日期: {date_str} - {str(e)}")
            return None
    
    def import_data(self):
        """导入数据文件"""
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
                self.log("导入取消")
                return
            
            self.log(f"开始导入文件: {os.path.basename(file_path)}")
            
            file_type = self.detect_file_type(file_path)
            self.log(f"检测到文件类型: {file_type}")
            
            if file_type == 'excel':
                self.df = self.read_excel_file(file_path)
            else:
                self.df = self.read_csv_file(file_path)
            
            if self.df is None or self.df.empty:
                messagebox.showwarning("警告", "导入的数据为空")
                self.log("导入失败: 数据为空")
                return
                
            self.log(f"原始列名: {self.df.columns.tolist()}")
            
            # 增强列名匹配逻辑 - 只需要日期和单位净值两列
            date_col = None
            nav_col = None
            
            # 可能的日期列名
            date_keywords = ['日期', '净值日期', 'date', '交易日期', '时间', 'time', '净值时间', '净值日期']
            # 可能的单位净值列名
            nav_keywords = ['单位净值', 'net', 'nav', '净值', '单位价值', '单位份额净值', '份额净值']
            
            # 遍历所有列，查找匹配的列名
            for col in self.df.columns:
                col_str = str(col).lower().replace(" ", "").replace("_", "")
                
                # 检查是否是日期列
                if date_col is None:
                    for keyword in date_keywords:
                        if keyword.lower() in col_str:
                            date_col = col
                            self.log(f"找到日期列: {col} -> '日期'")
                            break
                
                # 检查是否是净值列
                if nav_col is None:
                    for keyword in nav_keywords:
                        if keyword.lower() in col_str:
                            nav_col = col
                            self.log(f"找到单位净值列: {col} -> '单位净值'")
                            break
                
                # 如果两列都已找到，停止搜索
                if date_col and nav_col:
                    break
            
            # 如果没找到日期列或净值列，尝试使用前两列作为备选
            if date_col is None or nav_col is None:
                if len(self.df.columns) >= 2:
                    self.log("未找到标准列名，尝试使用前两列作为日期和单位净值")
                    date_col = self.df.columns[0]
                    nav_col = self.df.columns[1]
                else:
                    messagebox.showerror("错误", "文件列数不足，至少需要两列数据")
                    self.log("导入失败: 文件列数不足")
                    return
            
            # 只保留需要的列
            self.df = self.df[[date_col, nav_col]].copy()
            self.df.columns = ['日期', '单位净值']
            self.log(f"重命名后的列名: {self.df.columns.tolist()}")
            
            self.log("开始解析日期列...")
            
            # 增强日期解析 - 处理YYYYMMDD格式
            self.df['日期'] = self.df['日期'].astype(str).apply(
                lambda x: re.sub(r'[^0-9]', '', x)  # 移除非数字字符
            )
            
            self.df['日期'] = self.parse_dates(self.df['日期'])
            
            invalid_mask = self.df['日期'].isna()
            invalid_count = invalid_mask.sum()
            
            if invalid_count > 0:
                self.log(f"发现 {invalid_count} 行日期格式无效")
                self.df = self.df[~invalid_mask]
                self.log(f"已删除 {invalid_count} 行无效日期数据")
            
            if len(self.df) == 0:
                messagebox.showerror("错误", "导入的数据为空")
                self.log("导入失败: 数据为空")
                return
            
            # 检查日期排序方向（升序或降序）
            if len(self.df) > 1:
                first_date = self.df['日期'].iloc[0]
                last_date = self.df['日期'].iloc[-1]
                if first_date > last_date:
                    self.log("检测到日期降序排列，将按升序重新排序")
                    self.df = self.df.sort_values('日期', ascending=True).reset_index(drop=True)
                else:
                    self.log("日期已按升序排列")
            
            min_date = self.df['日期'].min()
            max_date = self.df['日期'].max()
            
            # 格式化日期为 YYYY-MM-DD
            min_date_str = min_date.strftime("%Y-%m-%d") if not pd.isna(min_date) else "N/A"
            max_date_str = max_date.strftime("%Y-%m-%d") if not pd.isna(max_date) else "N/A"
            
            self.log(f"排序后数据:")
            self.log(f"  首行日期: {min_date_str}, 净值: {self.df['单位净值'].iloc[0]}")
            self.log(f"  尾行日期: {max_date_str}, 净值: {self.df['单位净值'].iloc[-1]}")
            
            self.log("开始处理净值列...")
            try:
                self.df['单位净值'] = self.df['单位净值'].astype(str)
                self.df['单位净值'] = self.df['单位净值'].apply(self.clean_numeric_string)
                self.df['单位净值'] = pd.to_numeric(self.df['单位净值'], errors='coerce')
                
                na_count = self.df['单位净值'].isna().sum()
                if na_count > 0:
                    self.log(f"警告: 单位净值列中有{na_count}个值无法转换为数字")
                    self.df = self.df.dropna(subset=['单位净值'])
                    self.log(f"已删除{na_count}行无效的单位净值数据")
            except Exception as e:
                self.log(f"转换单位净值列时出错: {str(e)}")
                messagebox.showerror("错误", f"无法转换单位净值列: {str(e)}")
                return
            
            if len(self.df) == 0:
                messagebox.showerror("错误", "处理后的数据为空")
                self.log("导入失败: 处理后的数据为空")
                return
            
            self.btn_export['state'] = tk.NORMAL
            self.btn_reset['state'] = tk.NORMAL
            
            min_date = self.df['日期'].min()
            max_date = self.df['日期'].max()
            
            if not pd.isna(min_date) and not pd.isna(max_date):
                min_date = min_date.date()
                max_date = max_date.date()
                self.start_entry.delete(0, tk.END)
                self.start_entry.insert(0, min_date.strftime("%Y-%m-%d"))
                self.start_entry.configure(foreground=self.colors["text"])
                self.end_entry.delete(0, tk.END)
                self.end_entry.insert(0, max_date.strftime("%Y-%m-%d"))
                self.end_entry.configure(foreground=self.colors["text"])
            else:
                self.log("警告: 数据中没有有效的日期")
            
            self.full_view_data = self.df.copy()
            self.analyze_performance()
            self.calculate_fixed_freq()
            
            self.custom_range_label.config(text="日期范围: --")
            self.custom_days_label.config(text="周期天数: --")
            self.custom_return_label.config(text="年化收益率: --")
            self.custom_drawdown_label.config(text="最大回撤: --")
            
            filename = os.path.basename(file_path)
            if len(filename) > 20:
                display_name = filename[:10] + "..." + filename[-10:]
            else:
                display_name = filename
                
            self.log(f"成功导入数据: {display_name}")
            self.log(f"数据记录数: {len(self.df)}")
            
            if not pd.isna(min_date) and not pd.isna(max_date):
                min_date_str = min_date.strftime("%Y-%m-%d")
                max_date_str = max_date.strftime("%Y-%m-%d")
                self.log(f"数据日期范围: {min_date_str} 至 {max_date_str}")
                self.log(f"最早净值: {self.df['单位净值'].iloc[0]:.4f} (日期: {min_date_str})")
                self.log(f"最新净值: {self.df['单位净值'].iloc[-1]:.4f} (日期: {max_date_str})")
            else:
                self.log("警告: 无法确定日期范围")
            
        except Exception as e:
            messagebox.showerror("错误", f"导入文件时出错:\n{str(e)}")
            self.log(f"导入失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def calculate_fixed_freq(self):
        if self.df is None or len(self.df) == 0:
            return
        
        self.log("开始计算固定周期业绩...")
        
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        if not pd.api.types.is_datetime64_any_dtype(self.df['日期']):
            self.df['日期'] = pd.to_datetime(self.df['日期'], errors='coerce')
        
        if self.df['日期'].isnull().all():
            messagebox.showerror("错误", "日期列解析失败，无法进行分析")
            self.log("计算失败: 日期列无效")
            return
            
        earliest_date = self.df['日期'].iloc[0]
        latest_date = self.df['日期'].iloc[-1]
        nav_earliest = self.df['单位净值'].iloc[0]
        nav_latest = self.df['单位净值'].iloc[-1]
        
        if pd.isna(earliest_date) or pd.isna(latest_date):
            messagebox.showerror("错误", "数据中没有有效的日期")
            self.log("计算失败: 没有有效的日期")
            return
        
        # 格式化日期为 YYYY-MM-DD
        earliest_date_str = earliest_date.strftime("%Y-%m-%d")
        latest_date_str = latest_date.strftime("%Y-%m-%d")
        
        self.log(f"实际数据日期范围: {earliest_date_str} 至 {latest_date_str}")
        self.log(f"实际最早净值: {nav_earliest:.4f}, 最新净值: {nav_latest:.4f}")
        
        # 修改：最近X → 近X
        freq_periods = {
            "近一周": 7,
            "近两周": 14,
            "近三周": 21,
            "近一月": 30,
            "近两月": 60,
            "近三月": 90,
            "近半年": 180,
            "近一年": 365
        }
        
        # 修复：确保数据按日期升序排列（从早到晚）
        df_sorted = self.df.sort_values('日期', ascending=True).reset_index(drop=True)
        
        for freq, days in freq_periods.items():
            # 计算目标日期
            target_date = latest_date - pd.Timedelta(days=days)
            
            # 找到最接近目标日期的记录（前后各浮动7天）
            mask = (df_sorted['日期'] >= (target_date - pd.Timedelta(days=7))) & \
                   (df_sorted['日期'] <= (target_date + pd.Timedelta(days=7)))
            
            if not mask.any():
                # 如果浮动范围内没有数据，尝试使用第一个数据点
                if len(df_sorted) > 0:
                    idx = 0
                    actual_days = (latest_date - df_sorted.loc[idx, '日期']).days
                    self.log(f"{freq}: 使用最早数据点 (目标天数: {days}, 实际天数: {actual_days})")
                else:
                    # 新增：数据不足时显示"--"
                    values = (freq, "N/A", "--", "--")
                    self.result_tree.insert("", "end", values=values)
                    self.log(f"{freq}: 无足够数据")
                    continue
            else:
                # 在浮动范围内找到最接近目标日期的记录
                closest_idx = None
                min_diff = float('inf')
                
                for i in df_sorted[mask].index:
                    date_diff = abs((df_sorted.loc[i, '日期'] - target_date).days)
                    if date_diff < min_diff:
                        min_diff = date_diff
                        closest_idx = i
                
                if closest_idx is None:
                    # 如果浮动范围内没有找到，使用最后一个数据点
                    idx = len(df_sorted) - 1
                    actual_days = (latest_date - df_sorted.loc[idx, '日期']).days
                    self.log(f"{freq}: 使用最新数据点 (目标天数: {days}, 实际天数: {actual_days})")
                else:
                    idx = closest_idx
                    actual_days = (latest_date - df_sorted.loc[idx, '日期']).days
                    self.log(f"{freq}: 找到接近数据点 (目标天数: {days}, 实际天数: {actual_days}, 日期差异: {min_diff}天)")
            
            nav_start = df_sorted.loc[idx, '单位净值']
            
            # 新增：检查数据天数是否不足（误差超过20%）
            data_insufficient = False
            if actual_days < days * 0.8:  # 实际天数不足目标天数的80%
                data_insufficient = True
                annual_return_str = "--"
                max_drawdown_str = "--"
                self.log(f"{freq}: 数据不足 (实际天数: {actual_days}, 目标天数: {days}, 不足比例: {(1 - actual_days/days)*100:.1f}%)")
            else:
                if actual_days <= 0:
                    annual_return = 0.0
                    max_drawdown = 0.0
                else:
                    # 计算总收益率
                    total_return = (nav_latest / nav_start) - 1
                    # 计算年化收益率
                    annual_return = ((1 + total_return) ** (365 / actual_days)) - 1
                    
                    # 计算最大回撤 - 使用目标日期之后的数据
                    nav_series = df_sorted.loc[idx:, '单位净值'].reset_index(drop=True)
                    max_drawdown = self.calculate_max_drawdown(nav_series)
                
                annual_return_str = f"{annual_return:.2%}"
                max_drawdown_str = f"{max_drawdown:.2%}"
            
            values = (
                freq, 
                f"{actual_days}天", 
                annual_return_str,
                max_drawdown_str
            )
            self.result_tree.insert("", "end", values=values)
            
            # 添加详细日志
            start_date_str = df_sorted.loc[idx, '日期'].strftime("%Y-%m-%d")
            end_date_str = latest_date.strftime("%Y-%m-%d")
            
            if not data_insufficient:
                self.log(f"{freq}: 天数={actual_days}, 年化={annual_return_str}, 回撤={max_drawdown_str}")
                self.log(f"  开始净值: {nav_start:.4f} (日期: {start_date_str})")
                self.log(f"  结束净值: {nav_latest:.4f} (日期: {end_date_str})")
        
        self.log("固定周期业绩计算完成")
    
    def calculate_max_drawdown(self, nav_series):
        """计算最大回撤"""
        if nav_series.empty:
            return 0.0
            
        cumulative_max = nav_series.cummax()
        drawdown = (cumulative_max - nav_series) / cumulative_max
        return drawdown.max()
    
    def custom_analysis(self):
        if self.df is None or len(self.df) == 0:
            messagebox.showwarning("警告", "请先导入数据文件！")
            self.log("自定义分析失败: 无数据")
            return
        
        try:
            start_date_str = self.start_entry.get()
            end_date_str = self.end_entry.get()
            
            # 如果输入的是占位符文本，则跳过
            if start_date_str == "YYYY-MM-DD" or end_date_str == "YYYY-MM-DD":
                messagebox.showwarning("警告", "请输入有效的日期")
                return
            
            # 标准化日期格式
            normalized_start = self.normalize_date_string(start_date_str)
            normalized_end = self.normalize_date_string(end_date_str)
            
            if normalized_start is None or normalized_end is None:
                messagebox.showerror("错误", "日期格式错误，请使用类似YYYY-MM-DD的格式")
                self.log(f"日期格式错误: 开始日期={start_date_str}, 结束日期={end_date_str}")
                return
            
            try:
                start_date = datetime.strptime(normalized_start, "%Y-%m-%d")
                end_date = datetime.strptime(normalized_end, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("错误", "日期格式错误，请使用类似YYYY-MM-DD的格式")
                self.log(f"日期格式错误: 开始日期={start_date_str}, 结束日期={end_date_str}")
                return
            
            # 更新输入框中的日期为标准化格式
            self.start_entry.delete(0, tk.END)
            self.start_entry.insert(0, normalized_start)
            self.start_entry.configure(foreground=self.colors["text"])
            self.end_entry.delete(0, tk.END)
            self.end_entry.insert(0, normalized_end)
            self.end_entry.configure(foreground=self.colors["text"])
            
            self.log(f"开始自定义分析: {normalized_start} 至 {normalized_end}")
            
            days = (end_date - start_date).days + 1
            
            if days <= 0:
                messagebox.showerror("错误", "结束日期必须晚于开始日期")
                self.log("日期范围错误: 结束日期早于开始日期")
                return
                
        except Exception as e:
            messagebox.showerror("错误", f"日期处理出错: {str(e)}")
            self.log(f"日期处理出错: {str(e)}")
            return
        
        if not pd.api.types.is_datetime64_any_dtype(self.df['日期']):
            self.df['日期'] = pd.to_datetime(self.df['日期'], errors='coerce')
        
        min_date = self.df['日期'].min().to_pydatetime().date()
        max_date = self.df['日期'].max().to_pydatetime().date()
        
        if start_date.date() < min_date or end_date.date() > max_date:
            messagebox.showerror("错误", f"日期超出范围! 有效范围: {min_date} 至 {max_date}")
            self.log(f"日期超出范围: {start_date.date()} - {end_date.date()} (有效范围: {min_date} - {max_date})")
            return
        
        start_mask = self.df['日期'] >= pd.Timestamp(start_date)
        if not start_mask.any():
            messagebox.showerror("错误", "无法找到开始日期对应的数据")
            self.log("错误: 找不到开始日期数据")
            return
        start_idx = start_mask.idxmax()
        
        end_mask = self.df['日期'] <= pd.Timestamp(end_date)
        if not end_mask.any():
            messagebox.showerror("错误", "无法找到结束日期对应的数据")
            self.log("错误: 找不到结束日期数据")
            return
        end_idx = end_mask[::-1].idxmax()
        
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx
        
        if start_idx > end_idx:
            messagebox.showerror("错误", "日期范围无效，请确保结束日期在开始日期之后")
            self.log("错误: 日期范围无效")
            return
        
        if start_idx >= len(self.df) or end_idx >= len(self.df):
            messagebox.showerror("错误", "索引超出范围，请检查日期选择")
            self.log("错误: 索引超出范围")
            return
        
        nav_start = self.df.loc[start_idx, '单位净值']
        nav_end = self.df.loc[end_idx, '单位净值']
        
        total_return = (nav_end / nav_start) - 1
        
        if days <= 0:
            annual_return = 0.0
        else:
            annual_return = ((1 + total_return) ** (365 / days)) - 1
        
        nav_series = self.df.loc[start_idx:end_idx, '单位净值'].reset_index(drop=True)
        max_drawdown = self.calculate_max_drawdown(nav_series)
        
        self.custom_range_label.config(
            text=f"日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        )
        self.custom_days_label.config(text=f"周期天数: {days}天")
        
        # 设置收益率颜色 - 正收益红色，负收益绿色
        return_color = "#E74C3C" if annual_return >= 0 else "#27AE60"
        self.custom_return_label.config(text=f"年化收益率: {annual_return:.2%}", foreground=return_color)
        
        # 设置最大回撤颜色为绿色
        drawdown_color = "#27AE60"
        self.custom_drawdown_label.config(text=f"最大回撤: -{max_drawdown:.2%}", foreground=drawdown_color)
        
        self.analyze_performance(start_date=start_date, end_date=end_date)
        
        # 格式化日期为 YYYY-MM-DD
        start_date_str = self.df.loc[start_idx, '日期'].strftime("%Y-%m-%d")
        end_date_str = self.df.loc[end_idx, '日期'].strftime("%Y-%m-%d")
        
        self.log(f"自定义分析完成: 天数={days}, 年化={annual_return:.2%}, 回撤={max_drawdown:.2%}")
        self.log(f"开始净值: {nav_start:.4f} (日期: {start_date_str})")
        self.log(f"结束净值: {nav_end:.4f} (日期: {end_date_str})")
    
    def reset_to_full_view(self):
        """恢复全览视图"""
        if self.df is None or self.full_view_data is None:
            return
            
        self.df = self.full_view_data.copy()
        
        min_date = self.df['日期'].min().date()
        max_date = self.df['日期'].max().date()
        
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, min_date.strftime("%Y-%m-%d"))
        self.start_entry.configure(foreground=self.colors["text"])
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, max_date.strftime("%Y-%m-%d"))
        self.end_entry.configure(foreground=self.colors["text"])
        
        self.custom_range_label.config(text="日期范围: --")
        self.custom_days_label.config(text="周期天数: --")
        self.custom_return_label.config(text="年化收益率: --")
        self.custom_drawdown_label.config(text="最大回撤: --")
        
        self.analyze_performance()
        self.calculate_fixed_freq()
        
        self.log("已恢复全览视图")
    
    def analyze_performance(self, start_date=None, end_date=None):
        if self.df is None or len(self.df) == 0:
            return
        
        self.log("生成净值趋势图...")
        
        self.ax.clear()
        
        if not pd.api.types.is_datetime64_any_dtype(self.df['日期']):
            self.df['日期'] = pd.to_datetime(self.df['日期'], errors='coerce')
        
        df_plot = self.df.copy()
        
        if start_date and end_date:
            mask = (df_plot['日期'] >= start_date) & (df_plot['日期'] <= end_date)
            df_plot = df_plot.loc[mask]
            start_str = start_date.strftime("%Y/%m/%d")
            end_str = end_date.strftime("%Y/%m/%d")
            self.chart_title = f"{start_str}~{end_str}趋势图"
            
            # 保存当前日期范围
            self.current_start_date = start_date
            self.current_end_date = end_date
        else:
            start_date = df_plot['日期'].min()
            end_date = df_plot['日期'].max()
            start_str = start_date.strftime("%Y/%m/%d")
            end_str = end_date.strftime("%Y/%m/%d")
            self.chart_title = f"{start_str}~{end_str}趋势图"
            
            # 保存当前日期范围
            self.current_start_date = start_date
            self.current_end_date = end_date
        
        unit_color = self.colors["chart_line"]
        
        # 绘制净值曲线 - 去除标注
        self.ax.plot(
            df_plot['日期'], 
            df_plot['单位净值'], 
            color=unit_color, 
            linestyle='-', 
            linewidth=1.0
        )
        
        min_idx = df_plot['单位净值'].idxmin()
        max_idx = df_plot['单位净值'].idxmax()
        
        # 获取日期和净值用于标注 - 使用月日格式
        min_date_str = df_plot.loc[min_idx, '日期'].strftime("%m-%d")
        min_value = df_plot.loc[min_idx, '单位净值']
        max_date_str = df_plot.loc[max_idx, '日期'].strftime("%m-%d")
        max_value = df_plot.loc[max_idx, '单位净值']
        
        # 标记最低点 - 使用虚线圆圈
        self.ax.plot(
            df_plot.loc[min_idx, '日期'], 
            min_value, 
            marker='o', 
            markersize=4,
            markeredgecolor="#27AE60",  # 绿色
            markerfacecolor='none',
            markeredgewidth=1.0,
            linestyle=''  # 不显示连接线
        )
        
        # 标记最高点 - 使用虚线圆圈
        self.ax.plot(
            df_plot.loc[max_idx, '日期'], 
            max_value, 
            marker='o', 
            markersize=4,
            markeredgecolor="#E74C3C",  # 红色
            markerfacecolor='none',
            markeredgewidth=1.0,
            linestyle=''  # 不显示连接线
        )
        
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        x_range = x_max - x_min
        y_range = y_max - y_min
        
        min_point = (df_plot.loc[min_idx, '日期'], min_value)
        max_point = (df_plot.loc[max_idx, '日期'], max_value)
        
        min_x_offset = 10
        min_y_offset = 20
        
        if min_point[0].timestamp() < (x_min + 0.2 * x_range):
            min_x_offset = 20
        elif min_point[0].timestamp() > (x_min + 0.8 * x_range):
            min_x_offset = -20
        
        # 标注包含日期和净值 - 使用Min标识
        self.ax.annotate(
            f'Min: {min_value:.4f}\n{min_date_str}',
            xy=min_point,
            xytext=(min_x_offset, min_y_offset),
            textcoords='offset points',
            arrowprops=dict(
                arrowstyle="->", 
                connectionstyle="arc3", 
                color="#27AE60",  # 绿色
                linestyle='dashed',  # 虚线
                alpha=0.7  # 70%透明度
            ),
            fontsize=9,  # 增大字体
            weight='bold',  # 加粗
            color="#27AE60",  # 绿色
            bbox=dict(
                boxstyle="round,pad=0.2", 
                fc="white", 
                ec="#27AE60",  # 绿色边框
                alpha=0.3,  # 降低不透明度（70%透明）
                linestyle='dashed'  # 虚线
            )
        )
        
        max_x_offset = 10
        max_y_offset = -20
        
        if max_point[0].timestamp() < (x_min + 0.2 * x_range):
            max_x_offset = 20
        elif max_point[0].timestamp() > (x_min + 0.8 * x_range):
            max_x_offset = -20
        
        # 标注包含日期和净值 - 使用Max标识
        self.ax.annotate(
            f'Max: {max_value:.4f}\n{max_date_str}',
            xy=max_point,
            xytext=(max_x_offset, max_y_offset),
            textcoords='offset points',
            arrowprops=dict(
                arrowstyle="->", 
                connectionstyle="arc3", 
                color="#E74C3C",  # 红色
                linestyle='dashed',  # 虚线
                alpha=0.7  # 70%透明度
            ),
            fontsize=9,  # 增大字体
            weight='bold',  # 加粗
            color="#E74C3C",  # 红色
            bbox=dict(
                boxstyle="round,pad=0.2", 
                fc="white", 
                ec="#E74C3C",  # 红色边框
                alpha=0.3,  # 降低不透明度（70%透明）
                linestyle='dashed'  # 虚线
            )
        )
        
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
            date_format = '%m-%d'
            locator = mdates.MonthLocator(interval=3)
        
        self.ax.xaxis.set_major_locator(locator)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        
        min_nav = df_plot['单位净值'].min()
        max_nav = df_plot['单位净值'].max()
        nav_range = max_nav - min_nav
        
        if nav_range > 0:
            buffer = nav_range * 0.05
            self.ax.set_ylim(min_nav - buffer, max_nav + buffer)
        
        # 减少Y轴刻度数量，避免过于密集
        self.ax.yaxis.set_major_locator(MaxNLocator(prune='both', nbins=5))
        
        self.ax.grid(True, 
                    linestyle='--', 
                    alpha=0.6, 
                    color=self.colors["chart_grid"])
        
        # 减小坐标轴字体大小
        self.ax.tick_params(axis='x', 
                           which='major', 
                           labelsize=4,  # 减小字体大小
                           colors=self.colors["text"])
        self.ax.tick_params(axis='y', 
                           which='major', 
                           labelsize=5,  # 减小字体大小
                           colors=self.colors["text"])
        self.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.4f}'))
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.colors["text_light"])
        self.ax.spines['bottom'].set_color(self.colors["text_light"])
        
        # 调整标签位置防止截断
        plt.setp(self.ax.get_xticklabels(), rotation=30, ha='right', fontsize=4)  # 减小字体大小
        
        # 增加图表内边距，防止文字被截断
        self.figure.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.35)  # 增加底部内边距
        
        # 添加tight_layout调用以进一步优化布局
        self.figure.tight_layout(pad=1.5)
        
        self.canvas.draw()
        self.log("净值趋势图生成完成")
    
    def export_chart(self):
        if not hasattr(self, 'figure') or not self.figure:
            messagebox.showwarning("警告", "没有可导出的图表")
            return
        
        # 优化文件名生成逻辑
        if self.current_start_date and self.current_end_date:
            # 检查是否为同一年份
            if self.current_start_date.year == self.current_end_date.year:
                # 同一年份格式：YYYY--MMDD～MMDD
                filename = (
                    f"{self.current_start_date.year}--"
                    f"{self.current_start_date.strftime('%m%d')}～"
                    f"{self.current_end_date.strftime('%m%d')}净值趋势图"
                )
            else:
                # 不同年份格式：YYMMDD～YYMMDD
                filename = (
                    f"{self.current_start_date.strftime('%y%m%d')}～"
                    f"{self.current_end_date.strftime('%y%m%d')}净值趋势图"
                )
        else:
            # 默认文件名
            filename = "净值趋势图"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("所有文件", "*.*")],
            title="保存图表",
            initialfile=filename
        )
        
        if not file_path:
            return
        
        try:
            # 保存时使用bbox_inches='tight'确保所有元素都被包含
            self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            messagebox.showinfo("成功", f"图表已保存至:\n{file_path}")
            self.log(f"图表已导出: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存图表时出错:\n{str(e)}")
            self.log(f"导出图表失败: {str(e)}")
    
    def initialize_chart(self):
        self.ax.clear()
        # 使用与导入数据后相同的布局参数
        self.figure.subplots_adjust(left=0.10, right=0.95, top=0.92, bottom=0.35)
        self.figure.tight_layout(pad=1.5)
        
        # 设置相同的坐标轴样式
        self.ax.tick_params(axis='x', 
                           which='major', 
                           labelsize=4, 
                           colors=self.colors["text"])
        self.ax.tick_params(axis='y', 
                           which='major', 
                           labelsize=5, 
                           colors=self.colors["text"])
        self.ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.4f}'))
        self.ax.yaxis.set_major_locator(MaxNLocator(prune='both', nbins=5))
        
        self.ax.grid(True, 
                    linestyle='--', 
                    alpha=0.6, 
                    color=self.colors["chart_grid"])
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(self.colors["text_light"])
        self.ax.spines['bottom'].set_color(self.colors["text_light"])
        
        # 设置相同的X轴标签旋转角度
        plt.setp(self.ax.get_xticklabels(), rotation=30, ha='right', fontsize=4)
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = PerformanceBacktestTool(root)
    root.mainloop()