# analysis_operations.py
import os
import tkinter as tk
import pandas as pd
from tkinter import Tk, ttk, filedialog, messagebox
from datetime import datetime
from core import PerformanceAnalysis
from utils import normalize_date_string
from tooltip import ToolTip

class AnalysisOperations:
    def __init__(self, app):
        self.app = app
        self.config = app.config

    def reset_application(self):
        """重置应用程序"""
        self.app.df = None
        self.app.full_view_data = None
        self.app.current_plot_data = None  # 重置当前图表数据

        # 清空Max/Min数据
        self.app.max_value = None
        self.app.min_value = None
        self.app.max_date_str = None
        self.app.min_date_str = None

        self.app.chart_utils.initialize_chart()

        for item in self.app.components["result_tree"].get_children():
            self.app.components["result_tree"].delete(item)

        # 重置时，固定周期指标也用 / 占位
        fixed_freq_placeholders = [
            ("近1周", '/'), ("近2周", '/'), ("近3周", '/'),
            ("近1月", '/'), ("近2月", '/'), ("近3月", '/'),
            ("近6月", '/'), ("近1年", '/'), ("成立以来", '/')
        ]
        for freq, placeholder in fixed_freq_placeholders:
            self.app.components["result_tree"].insert("", "end", values=(freq, placeholder, placeholder, placeholder))

        self.app.components["custom_range_start_label"].config(text="--")
        self.app.components["custom_range_end_label"].config(text="")
        self.app.components["custom_days_label"].config(text="--")
        self.app.components["custom_return_label_value"].config(text="--", foreground=self.config.colors["text"])
        self.app.components["custom_drawdown_label_value"].config(text="--", foreground=self.config.colors["text"])

        # 修改：确保日期输入框处于禁用状态并显示占位符
        self.app.components["start_entry"].config(state='normal') 
        self.app.components["start_entry"].delete(0, tk.END)
        self.app.components["start_entry"].insert(0, "YYYY-MM-DD")
        self.app.components["start_entry"].configure(foreground=self.config.colors["placeholder"])
        self.app.components["start_entry"].config(state='disabled')  
        
        self.app.components["end_entry"].config(state='normal')  
        self.app.components["end_entry"].delete(0, tk.END)
        self.app.components["end_entry"].insert(0, "YYYY-MM-DD")
        self.app.components["end_entry"].configure(foreground=self.config.colors["placeholder"])
        self.app.components["end_entry"].config(state='disabled')  

        # 更新菜单状态
        menu = self.app.root.nametowidget(".!menu")
        file_menu = menu.winfo_children()[0]  # 文件菜单是第一个
        file_menu.entryconfig("导出图表", state=tk.DISABLED)

        self.app.components["btn_custom"].config(state=tk.DISABLED)
        self.app.components["btn_reset"].config(state=tk.DISABLED)
        self.app.components["btn_reset_app"].config(state=tk.NORMAL)

        # 重置导出图表设置
        self.config.set("show_hover_data", False)
        self.config.set("hover_date", "")

        self.app.clear_log_text()

        self.app.log("应用已重置", "success")
        self.app.log("欢迎使用业绩表现回测工具", "success")
        self.app.log("请导入文件开始使用", "success")
        self.app.log("rizona.cn@gmail.com", "success")

    def calculate_fixed_freq(self):
        """计算固定周期的业绩指标，并更新到界面上"""
        if self.app.df is None or len(self.app.df) == 0:
            # 数据为空时，保持 / 占位符
            return

        self.app.log("开始计算固定周期业绩...", "info")

        for item in self.app.components["result_tree"].get_children():
            self.app.components["result_tree"].delete(item)

        performance_analyzer = PerformanceAnalysis(self.app.df, self.app.log)
        results = performance_analyzer.calculate_fixed_freq()

        if not results:
            self.app.log("数据天数不足，无法计算固定周期业绩", "warning")
            return

        for values in results:
            self.app.components["result_tree"].insert("", "end", values=values)
            if values[1] != '/':
                self.app.log(f"{values[0]}: 天数={values[1]}, 年化={values[2]}, 回撤={values[3]}", "info")
            else:
                 self.app.log(f"数据不足，无法计算 {values[0]} 的业绩。", "info")

        self.app.log("固定周期业绩计算完成", "success")

    def custom_analysis(self):
        """执行自定义分析"""
        if not self.app.is_activated:
            self.show_custom_message("警告", "软件未激活，无法使用此功能")
            return
            
        if self.app.df is None or len(self.app.df) == 0:
            self.show_custom_message("警告", "请先导入数据文件！")
            self.app.log("自定义分析失败: 无数据", "warning")
            return

        # 检查输入框是否被禁用（未导入数据）
        if self.app.components["start_entry"].cget('state') == 'disabled':
            self.show_custom_message("警告", "请先导入数据文件！")
            self.app.log("自定义分析失败: 输入框被禁用，无数据", "warning")
            return

        start_date_str = self.app.components["start_entry"].get()
        end_date_str = self.app.components["end_entry"].get()

        if start_date_str == "YYYY-MM-DD" or end_date_str == "YYYY-MM-DD":
            self.show_custom_message("警告", "请输入有效的日期")
            self.app.log("日期输入无效，请重新输入", "warning")
            return

        # 在点击分析按钮时再次进行最终校验
        if not self.app.event_handlers._validate_dates(self.app.components["start_entry"]) or not self.app.event_handlers._validate_dates(self.app.components["end_entry"]):
            self.app.log("日期格式错误，分析中止。", "error")
            return

        try:
            start_date = datetime.strptime(self.app.components["start_entry"].get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.app.components["end_entry"].get(), "%Y-%m-%d")
            
            # 检查日期是否在数据范围内
            if self.app.df is not None and len(self.app.df) > 0:
                min_data_date = self.app.df['日期'].min()
                max_data_date = self.app.df['日期'].max()
                
                if start_date < min_data_date or start_date > max_data_date:
                    self.show_custom_message("错误", f"开始日期必须在数据日期范围内: {min_data_date.strftime('%Y-%m-%d')} 至 {max_data_date.strftime('%Y-%m-%d')}")
                    self.app.log("开始日期超出数据范围", "error")
                    return
                    
                if end_date < min_data_date or end_date > max_data_date:
                    self.show_custom_message("错误", f"结束日期必须在数据日期范围内: {min_data_date.strftime('%Y-%m-%d')} 至 {max_data_date.strftime('%Y-%m-%d')}")
                    self.app.log("结束日期超出数据范围", "error")
                    return

            self.app.log(f"开始自定义分析: {self.app.components['start_entry'].get()} 至 {self.app.components['end_entry'].get()}", "info")

            performance_analyzer = PerformanceAnalysis(self.app.df, self.app.log)
            result = performance_analyzer.calculate_custom_range(start_date, end_date)

            if result is None:
                return

            self.app.components["custom_range_start_label"].config(
                text=f"{result['start_date'].strftime('%Y-%m-%d')}"
            )
            self.app.components["custom_range_end_label"].config(
                text=f"{result['end_date'].strftime('%Y-%m-%d')}"
            )
            self.app.components["custom_days_label"].config(text=f"{result['days']}天")

            return_color = "#E74C3C" if result['annual_return'] >= 0 else "#27AE60"
            self.app.components["custom_return_label_value"].config(text=f"{result['annual_return']:.2%}", foreground=return_color)

            drawdown_color = "#27AE60"
            self.app.components["custom_drawdown_label_value"].config(text=f"-{result['max_drawdown']:.2%}", foreground=drawdown_color)

            self.app.analyze_performance(start_date=start_date, end_date=end_date)
            self.app.log(f"自定义分析完成: 天数={result['days']}, 年化={result['annual_return']:.2%}, 回撤={result['max_drawdown']:.2%}", "success")
            self.app.log(f"开始净值: {result['nav_start']:.4f} (日期: {result['actual_start_date'].strftime('%Y-%m-%d')})", "info")
            self.app.log(f"结束净值: {result['nav_end']:.4f} (日期: {result['actual_end_date'].strftime('%Y-%m-%d')})", "info")

        except Exception as e:
            self.show_custom_message("错误", f"日期处理出错: {str(e)}")
            self.app.log(f"日期处理出错: {str(e)}", "error")

    def reset_to_full_view(self):
        """重置到全览视图"""
        if not self.app.is_activated:
            self.show_custom_message("警告", "软件未激活，无法使用此功能")
            return
            
        if self.app.df is None or self.app.full_view_data is None:
            return

        self.app.df = self.app.full_view_data.copy()

        min_date = self.app.df['日期'].min().date()
        max_date = self.app.df['日期'].max().date()

        self.app.components["start_entry"].config(state='normal')
        self.app.components["start_entry"].delete(0, tk.END)
        self.app.components["start_entry"].insert(0, min_date.strftime("%Y-%m-%d"))
        self.app.components["start_entry"].configure(foreground=self.config.colors["text"])
        
        self.app.components["end_entry"].config(state='normal')
        self.app.components["end_entry"].delete(0, tk.END)
        self.app.components["end_entry"].insert(0, max_date.strftime("%Y-%m-%d"))
        self.app.components["end_entry"].configure(foreground=self.config.colors["text"])

        self.app.components["custom_range_start_label"].config(text="--")
        self.app.components["custom_range_end_label"].config(text="")
        self.app.components["custom_days_label"].config(text="--")
        self.app.components["custom_return_label_value"].config(text="--", foreground=self.config.colors["text"])
        self.app.components["custom_drawdown_label_value"].config(text="--", foreground=self.config.colors["text"])

        self.app.analyze_performance()
        self.app.calculate_fixed_freq()

        # 重置导出图表设置
        self.config.set("show_hover_data", False)
        self.config.set("hover_date", "")

        self.app.log("已恢复全览视图", "success")

    def analyze_performance(self, start_date=None, end_date=None):
        """分析业绩并生成图表"""
        if self.app.df is None or len(self.app.df) == 0:
            return

        self.app.ax.clear()

        performance_analyzer = PerformanceAnalysis(self.app.df, self.app.log)
        df_plot, self.app.chart_title, self.app.current_start_date, self.app.current_end_date = \
            performance_analyzer.prepare_chart_data(start_date, end_date)

        # 存储当前显示的图表数据，用于悬停事件
        self.app.current_plot_data = df_plot.copy()

        # 每次绘制新图表前，清除旧的悬停标注对象和标记
        if self.app.chart_utils.hover_line_x:
            try:
                self.app.chart_utils.hover_line_x.remove()
            except:
                pass
            self.app.chart_utils.hover_line_x = None

        if self.app.chart_utils.hover_line_y:
            try:
                self.app.chart_utils.hover_line_y.remove()
            except:
                pass
            self.app.chart_utils.hover_line_y = None

        if self.app.chart_utils.hover_marker:
            try:
                self.app.chart_utils.hover_marker.remove()
            except:
                pass
            self.app.chart_utils.hover_marker = None

        if self.app.chart_utils.hover_text_obj:
            try:
                self.app.chart_utils.hover_text_obj.remove()
            except:
                pass
            self.app.chart_utils.hover_text_obj = None

        # 每次重绘图表，都清空并重新绘制 Max/Min 文本和标记
        if self.app.chart_utils.max_min_text_obj:
            for text_obj in self.app.chart_utils.max_min_text_obj:
                try:
                    text_obj.remove()
                except:
                    pass
            self.app.chart_utils.max_min_text_obj = []

        unit_color = self.config.colors["chart_line"]

        self.app.ax.plot(
            df_plot['日期'],
            df_plot['单位净值'],
            color=unit_color,
            linestyle='-',
            linewidth=1.0
        )

        min_idx = df_plot['单位净值'].idxmin()
        max_idx = df_plot['单位净值'].idxmax()

        self.app.min_date_str = df_plot.loc[min_idx, '日期'].strftime("%y/%m/%d")
        self.app.min_value = df_plot.loc[min_idx, '单位净值']
        self.app.max_date_str = df_plot.loc[max_idx, '日期'].strftime("%y/%m/%d")
        self.app.max_value = df_plot.loc[max_idx, '单位净值']

        self.app.ax.plot(
            df_plot.loc[max_idx, '日期'],
            self.app.max_value,
            marker='o',
            markersize=6,
            markerfacecolor='none',
            markeredgecolor=self.config.colors["max_color"],
            markeredgewidth=1.5,
            linestyle='',
            zorder=10
        )

        self.app.ax.plot(
            df_plot.loc[min_idx, '日期'],
            self.app.min_value,
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
            max_text = f'Max: {self.app.max_value: >8.4f} ({self.app.max_date_str})'
            min_text = f'Min: {self.app.min_value: >8.4f} ({self.app.min_date_str})'

            max_text_obj = self.app.ax.text(
                max_x, max_y,
                max_text,
                transform=self.app.ax.transAxes,
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

            min_text_obj = self.app.ax.text(
                min_x, min_y,
                min_text,
                transform=self.app.ax.transAxes,
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
            self.app.chart_utils.max_min_text_obj = [max_text_obj, min_text_obj]

        # 设置图表格式
        self.app.chart_utils.setup_chart_formatting(df_plot)

        # 如果有悬停日期设置，重新添加悬停标记
        if self.config.get("show_hover_data") and self.config.get("hover_date"):
            self.app.chart_utils.update_chart_with_hover_date()

        self.app.canvas.draw()
        self.app.log("净值趋势图生成完成", "success")

    def export_chart(self):
        """导出图表"""
        if not self.app.is_activated:
            self.show_custom_message("警告", "软件未激活，无法使用此功能")
            return
            
        if not hasattr(self.app, 'figure') or not self.app.figure:
            self.show_custom_message("警告", "没有可导出的图表")
            return

        # 使用配置的导出目录
        export_dir = self.config.get("export_directory", os.getcwd())
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        if self.app.current_start_date and self.app.current_end_date:
            if self.app.current_start_date.year == self.app.current_end_date.year:
                filename = (
                    f"{self.app.current_start_date.year}--"
                    f"{self.app.current_start_date.strftime('%m%d')}～"
                    f"{self.app.current_end_date.strftime('%m%d')}净值趋势图.png"
                )
            else:
                filename = (
                    f"{self.app.current_start_date.strftime('%y%m%d')}～"
                    f"{self.app.current_end_date.strftime('%y%m%d')}净值趋势图.png"
                )
        else:
                filename = "净值趋势图.png"

        file_path = os.path.join(export_dir, filename)

        try:
            # 如果启用了悬停数据显示，添加悬停数据
            if self.config.get("show_hover_data") and self.config.get("hover_date"):
                try:
                    hover_date = datetime.strptime(self.config.get("hover_date"), "%Y-%m-%d")
                    if self.app.current_plot_data is not None:
                        # 找到最接近的日期
                        closest_idx = self.app.current_plot_data['日期'].sub(hover_date).abs().idxmin()
                        closest_row = self.app.current_plot_data.loc[closest_idx]
                        nav = closest_row['单位净值']
                        date = closest_row['日期']

                        # 添加悬停十字线但不添加文本
                        self.app.ax.axvline(
                            x=date,
                            color=self.config.colors["chart_hover"],
                            linestyle='--',
                            linewidth=1,
                            alpha=0.5,
                            zorder=5
                        )

                        self.app.ax.axhline(
                            y=nav,
                            color=self.config.colors["chart_hover"],
                            linestyle='--',
                            linewidth=1,
                            alpha=0.5,
                            zorder=5
                        )

                        # 添加空心圆标记
                        self.app.ax.plot(
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
                    self.app.log("悬停日期格式无效，将不显示悬停数据", "warning")

            self.app.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            self.app.log(f"图表已导出: {file_path}", "success")
        except Exception as e:
            self.show_custom_message("错误", f"保存图表时出错:\n{str(e)}")
            self.app.log(f"导出图表失败: {str(e)}", "error")

    def set_export_chart_settings(self):
        """设置导出图表选项"""
        if not self.app.is_activated:
            self.show_custom_message("警告", "软件未激活，无法使用此功能")
            return
            
        if self.app.df is None or len(self.app.df) == 0:
            self.show_custom_message("警告", "请先导入数据文件！")
            self.app.log("设置导出图表失败: 无数据", "warning")
            return

        settings_window = tk.Toplevel(self.app.root)
        settings_window.title("导出图表设置")
        settings_window.geometry("200x130")
        settings_window.resizable(False, False)
        settings_window.transient(self.app.root)
        settings_window.grab_set()
        settings_window.configure(bg=self.config.colors["background"])

        # 设置窗口居中显示
        self.app.center_window_relative(settings_window, self.app.root)

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
                normalized_date = normalize_date_string(date_str, self.app.log)
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
                normalized_date = normalize_date_string(date_str, self.app.log)
                hover_date = datetime.strptime(normalized_date, "%Y-%m-%d")

                # 检查日期是否在数据范围内
                if self.app.df is not None and len(self.app.df) > 0:
                    min_date = self.app.df['日期'].min()
                    max_date = self.app.df['日期'].max()
                    if hover_date < min_date or hover_date > max_date:
                        # 显示错误提示 - 修改为200x130大小
                        error_window = tk.Toplevel(settings_window)
                        error_window.title("错误")
                        error_window.geometry("200x130")  
                        error_window.resizable(False, False)
                        error_window.transient(settings_window)
                        error_window.grab_set()
                        error_window.configure(bg=self.config.colors["background"])

                        # 居中显示错误窗口
                        self.app.center_window_relative(error_window, settings_window)
                    
                        error_msg = f"悬停日期必须在数据日期范围内: {min_date.strftime('%Y-%m-%d')} 至 {max_date.strftime('%Y-%m-%d')}"
                        
                        main_error_frame = ttk.Frame(error_window, padding=10)
                        main_error_frame.pack(fill=tk.BOTH, expand=True)
                        
                        label = ttk.Label(main_error_frame, text=error_msg, wraplength=180, justify=tk.LEFT)  # 设置换行宽度
                        label.pack(padx=10, pady=10)
                        
                        btn_frame = ttk.Frame(main_error_frame)
                        btn_frame.pack(pady=10)
                        
                        ttk.Button(btn_frame, text="确定", command=error_window.destroy, width=10).pack()
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
                self.app.chart_utils.remove_hover_date_marker()

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
                self.config.set("hover_date", normalize_date_string(hover_date_var.get(), self.app.log))
                # 设置悬停日期后，立即在图表上显示交叉线
                self.app.chart_utils.update_chart_with_hover_date()
            else:
                self.config.set("show_hover_data", False)
                self.config.set("hover_date", "")
                # 清除悬停日期标记并重新绘制图表
                self.app.chart_utils.remove_hover_date_marker()
                # 重新绘制图表以确保交叉线被清除
                if self.app.df is not None and len(self.app.df) > 0:
                    self.app.analyze_performance()
            settings_window.destroy()
            self.app.log("导出图表设置已保存", "success")

        def cancel_settings():
            settings_window.destroy()

        ttk.Button(button_frame, text="确定", command=save_settings, width=10).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings, width=10).pack(side=tk.RIGHT)

        # 初始显示状态
        toggle_hover_date()

    def set_export_directory(self):
        """设置导出目录"""
        if not self.app.is_activated:
            self.show_custom_message("警告", "软件未激活，无法使用此功能")
            return
            
        settings_window = tk.Toplevel(self.app.root)
        settings_window.title("导出目录设置")
        settings_window.geometry("200x160")  
        settings_window.resizable(False, False)
        settings_window.transient(self.app.root)
        settings_window.grab_set()
        settings_window.configure(bg=self.config.colors["background"])

        # 设置窗口居中显示
        self.app.center_window_relative(settings_window, self.app.root)

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
            self.app.log(f"导出目录已设置为: {self.config.get('export_directory')}", "success")

        def cancel_settings():
            settings_window.destroy()

        ttk.Button(button_frame, text="确定", command=save_settings, width=10).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings, width=10).pack(side=tk.RIGHT)

        # 初始显示状态
        toggle_directory_options()

    def set_textbox_settings(self):
        """设置提示框位置"""
        if not self.app.is_activated:
            self.show_custom_message("警告", "软件未激活，无法使用此功能")
            return
            
        settings_window = tk.Toplevel(self.app.root)
        settings_window.title("提示框设置")
        settings_window.geometry("200x130")
        settings_window.resizable(False, False)
        settings_window.transient(self.app.root)
        settings_window.grab_set()
        settings_window.configure(bg=self.config.colors["background"])

        # 设置窗口居中显示
        self.app.center_window_relative(settings_window, self.app.root)

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
            self.app.log("提示框设置已保存", "success")

            # 重新绘制图表以应用新设置
            if self.app.df is not None and len(self.app.df) > 0:
                self.app.analyze_performance()

        def cancel_settings():
            settings_window.destroy()

        ttk.Button(button_frame, text="确定", command=save_settings, width=10).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=cancel_settings, width=10).pack(side=tk.RIGHT)

        # 初始显示状态
        toggle_position_options()
    
    def show_custom_message(self, title, message):
        """显示自定义消息框，居中于父窗口"""
        window = tk.Toplevel(self.app.root)
        window.title(title)
        window.geometry("200x130")  
        window.resizable(False, False)
        window.transient(self.app.root)
        window.grab_set()
        window.configure(bg=self.config.colors["background"])
        
        # 居中显示于父窗口
        self.app.center_window_relative(window, self.app.root)
        
        main_frame = ttk.Frame(window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=message, 
                wraplength=180, justify=tk.LEFT).pack(pady=10)  # 设置换行宽度
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="确定", command=window.destroy, width=10).pack()