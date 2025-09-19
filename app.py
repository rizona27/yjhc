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
from utils import setup_fonts, normalize_date_string, detect_file_type, read_csv_file, read_excel_file, log_to_text_widget, cleanup_exit, log_message, OPEN_WINDOWS, MAX_WINDOWS
from gui_components import create_menu_bar, create_main_interface, create_log_window
from config import Config
from tooltip import ToolTip
from chart_utils import ChartUtils
from event_handlers import EventHandlers
from window_utils import WindowUtils
from activation import ActivationManager
from file_operations import FileOperations
from analysis_operations import AnalysisOperations

# 辅助函数：处理打包后的路径
def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# 忽略openpyxl的样式警告
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.styles.stylesheet")

class PerformanceBacktestTool:
    def __init__(self, root):
        # 隐藏窗口直到完全初始化
        root.withdraw()

        # 设置主窗口图标
        root.iconbitmap(resource_path('app.ico'))
        
        global OPEN_WINDOWS
        if OPEN_WINDOWS >= MAX_WINDOWS:
            # 使用自定义警告窗口
            warning_window = tk.Toplevel(root)
            warning_window.title("警告")
            warning_window.geometry("300x100")
            warning_window.resizable(False, False)
            warning_window.transient(root)
            warning_window.grab_set()
            
            # 设置窗口图标
            try:
                warning_window.iconbitmap('app.ico')
            except:
                pass
            
            # 设置窗口样式
            warning_window.configure(bg="#F5F8FA")
            
            # 居中显示警告窗口
            x = (warning_window.winfo_screenwidth() - 300) // 2
            y = (warning_window.winfo_screenheight() - 100) // 2
            warning_window.geometry(f"300x100+{x}+{y}")
            
            main_frame = ttk.Frame(warning_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttt.Label(main_frame, text=f"最多只能打开{MAX_WINDOWS}个窗口", 
                    wraplength=250, justify=tk.LEFT).pack(pady=10)
            
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(pady=10)
            
            ttk.Button(btn_frame, text="确定", command=root.destroy, width=10).pack()
            
            return

        OPEN_WINDOWS += 1

        self.root = root
        self.root.title("业绩表现回测工具")
        
        # 初始化配置
        self.config = Config()
        
        # 根据配置决定初始窗口大小
        show_log = self.config.get("show_log_window", False)
        initial_width = 500 + 300 if show_log else 500
        self.root.geometry(f"{initial_width}x540")  # 设置初始大小
        self.root.resizable(False, False)  # 不允许拉伸窗口

        # 设置程序图标
        try:
            self.root.iconbitmap('app.ico')
        except:
            pass

        # 窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", lambda: cleanup_exit(self.root))
        
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

        # 创建右侧日志区域
        self.log_frame = ttk.Frame(self.main_container, width=300)  # 固定宽度
        self.log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        self.log_frame.pack_propagate(False)  # 阻止框架调整大小以适应内容

        # 根据配置决定是否隐藏日志窗口
        if not show_log:
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
        self.file_operations = FileOperations(self)
        self.analysis_operations = AnalysisOperations(self)

        self.canvas.mpl_connect('motion_notify_event', self.chart_utils.on_hover)
        self.canvas.mpl_connect('axes_leave_event', self.chart_utils.on_leave)

        setup_fonts()
        self.chart_utils.initialize_chart()

        # 创建日志窗口（放在右侧框架中）
        self.log_texts = create_log_window(self, self.log_frame)

        # 更新日志菜单标签
        self.update_log_menu_label()

        # 根据激活状态更新界面
        self.activation_manager.update_activation_status(self)
        
        # 初始化按钮状态
        if self.df is None or len(self.df) == 0:
            self.components["btn_custom"].config(state=tk.DISABLED)
            self.components["btn_reset"].config(state=tk.DISABLED)
        
        # 强制更新窗口布局，确保获取到正确的尺寸
        self.root.update_idletasks()
        
        # 居中窗口
        self.window_utils.center_window(self.root)
        
        # 延迟更新图表布局，解决初始渲染问题
        self.root.after(100, self.fix_initial_layout)
        
        # 在这里调用 reset_application 来确保初始界面状态正确
        self.reset_application()

        # 显示窗口
        self.root.deiconify()
        
        self.log("欢迎使用业绩表现回测工具", "success")
        if not self.is_activated:
            self.log("软件未激活，请前往关于->说明中输入激活码", "warning")
            self.log("临时激活码: 0315 (有效期7天)", "info")
        else:
            self.log("软件已激活，请导入文件开始使用", "success")
        self.log("rizona.cn@gmail.com", "success")
        
    def fix_initial_layout(self):
        """修复初始布局问题"""
        self.root.update_idletasks()
        if hasattr(self, 'canvas'):
            self.canvas.draw()

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
        # 强制更新布局
        self.root.update_idletasks()
        if hasattr(self, 'canvas'):
            self.canvas.draw()

    def hide_log_window(self):
        """隐藏日志窗口"""
        self.log_frame.pack_forget()
        # 调整窗口大小
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"500x540+{x}+{y}")
        self.config.set("show_log_window", False)
        self.update_log_menu_label()
        # 强制更新布局
        self.root.update_idletasks()
        if hasattr(self, 'canvas'):
            self.canvas.draw()

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
        self.analysis_operations.reset_application()

    def show_readme(self):
        self.window_utils.show_readme(self)

    def show_activation(self):
        self.window_utils.show_activation(self)

    def close_readme(self, window):
        self.window_utils.close_readme(window)

    def import_data(self):
        self.file_operations.import_data()

    def calculate_fixed_freq(self):
        """计算固定周期的业绩指标，并更新到界面上"""
        self.analysis_operations.calculate_fixed_freq()

    def custom_analysis(self):
        self.analysis_operations.custom_analysis()

    def reset_to_full_view(self):
        self.analysis_operations.reset_to_full_view()

    def analyze_performance(self, start_date=None, end_date=None):
        self.analysis_operations.analyze_performance(start_date, end_date)

    def export_chart(self):
        self.analysis_operations.export_chart()

    def clear_log_text(self):
        """清空日志内容"""
        for log_text in self.log_texts.values():
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            log_text.config(state=tk.DISABLED)

    def set_export_chart_settings(self):
        """设置导出图表选项"""
        self.analysis_operations.set_export_chart_settings()

    def set_export_directory(self):
        """设置导出目录"""
        self.analysis_operations.set_export_directory()

    def set_textbox_settings(self):
        """设置提示框位置"""
        self.analysis_operations.set_textbox_settings()

    def update_activation_status(self):
        """更新激活状态界面"""
        self.activation_manager.update_activation_status(self)

if __name__ == "__main__":
    root = tk.Tk()
    app = PerformanceBacktestTool(root)
    root.mainloop()