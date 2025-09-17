# window_utils.py
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from activation import ActivationManager
import time

class WindowUtils:
    def __init__(self, app):
        self.app = app
        self.config = app.config
        self.activation_manager = ActivationManager()
        # 添加一个实例变量来存储 trace_id
        self.activation_trace_id = None

    def center_window(self, window):
        """将窗口居中显示"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

    def center_window_relative(self, window, parent):
        """将子窗口居中显示在父窗口中心"""
        parent.update_idletasks()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        window.update_idletasks()
        win_width = window.winfo_width()
        win_height = window.winfo_height()
        
        x = parent_x + (parent_width // 2) - (win_width // 2)
        y = parent_y + (parent_height // 2) - (win_height // 2)
        
        window.geometry(f"{win_width}x{win_height}+{x}+{y}")

    def show_readme(self, app):
        readme_window = tk.Toplevel(app.root)
        readme_window.title("说明")
        readme_window.geometry("320x270")
        readme_window.resizable(False, False)
        readme_window.configure(bg=self.config.colors["background"])
        readme_window.transient(app.root)

        self.center_window_relative(readme_window, app.root)
        readme_window.deiconify()
        readme_window.grab_set()

        main_frame = ttk.Frame(readme_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        help_text = """
1. 导入数据
- 支持csv、xls、xlsx格式
- 自动识别列头并排序

2. 数据分析
- 自动计算固定周期业绩
- 自动计算年化收益率、最大回撤
- 支持自定义日期区间分析

3. 净值趋势图
- 自动生成净值趋势图
- 标记最高点和最低点
- 鼠标悬停可显示日期和净值

4. 导出图表
- 可以区间命名导出趋势图

5. 其他
- 恢复全览：返回完整数据视图
- 系统日志：记录程序运行过程

提示：
- 已支持多种日期格式：
  YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD
"""
    
        help_text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            bg=self.config.colors["card"],
            fg=self.config.colors["text"],
            font=("Helvetica", 9),
            borderwidth=1,
            relief="solid",
            padx=10,
            pady=10
        )
        help_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        help_text_widget.insert(tk.END, help_text.strip())
        help_text_widget.config(state=tk.DISABLED)
        scrollbar.config(command=help_text_widget.yview)

        author_frame = ttk.Frame(main_frame)
        author_frame.pack(fill=tk.X)

        author_label = ttk.Label(
            author_frame,
            text="Arizona.cn@gmail.com",
            font=("Helvetica", 10),
            foreground=self.config.colors["accent"],
            background=self.config.colors["background"]
        )
        author_label.pack(side=tk.BOTTOM)

    def show_activation(self, app):
        activation_window = tk.Toplevel(app.root)
        activation_window.title("软件激活")
        activation_window.geometry("320x270")
        activation_window.resizable(False, False)
        activation_window.configure(bg=self.config.colors["background"])
        activation_window.transient(app.root)

        self.center_window_relative(activation_window, app.root)
        activation_window.deiconify()
        activation_window.grab_set()

        main_frame = ttk.Frame(activation_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        is_activated = self.activation_manager.check_activation()
        status_text = "已激活" if is_activated else "未激活"
        status_color = self.config.colors["success"] if is_activated else self.config.colors["error"]
        
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="激活状态:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        status_label = ttk.Label(status_frame, text=status_text, font=("Helvetica", 10, "bold"), foreground=status_color)
        status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        time_label = ttk.Label(status_frame, text="", font=("Helvetica", 9))
        time_label.pack(side=tk.RIGHT)
        
        def update_time_display():
            if is_activated:
                activation_info = self.activation_manager.get_activation_info()
                if activation_info.get("activation_type") == "temporary":
                    days, hours, minutes, seconds = self.activation_manager.get_remaining_time()
                    if days > 0 or hours > 0 or minutes > 0 or seconds > 0:
                        time_label.config(text=f"剩余时间: {days}天 {hours:02d}:{minutes:02d}:{seconds:02d}")
                        activation_window.after(1000, update_time_display)
                    else:
                        time_label.config(text="已过期")
                else:
                    time_label.config(text="永久激活")
            else:
                time_label.config(text="")
        
        update_time_display()
        
        activation_input_frame = ttk.Frame(main_frame)
        activation_input_frame.pack(fill=tk.X, pady=(10, 15))
        
        ttk.Label(activation_input_frame, text="激活码:", font=("Helvetica", 8)).pack(side=tk.LEFT)
        
        activation_entry = ttk.Entry(
            activation_input_frame, 
            width=23 
        )
        activation_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # 使用 Tkinter 的 trace 方法来实时监控输入框内容
        # 这种方法比 KeyRelease 更稳定，因为它会在内容改变时立即触发
        def on_entry_change(*args):
            # 在内部函数中引用外部类的属性
            if self.activation_trace_id:
                # 移除旧的 trace，防止无限递归
                activation_entry_var.trace_remove('write', self.activation_trace_id)
            
            current_content = activation_entry.get()
            # 移除所有非字母数字字符
            cleaned_content = ''.join(c for c in current_content if c.isalnum()).upper()
            
            # 严格截断为16个字符
            if len(cleaned_content) > 16:
                cleaned_content = cleaned_content[:16]

            # 格式化并更新输入框
            formatted_content = '-'.join(cleaned_content[i:i+4] for i in range(0, len(cleaned_content), 4))
            
            # 只有内容变化时才更新，防止不必要的刷新
            if formatted_content != current_content:
                # 记录光标位置
                cursor_pos = activation_entry.index(tk.INSERT)
                
                activation_entry.delete(0, tk.END)
                activation_entry.insert(0, formatted_content)
                
                # 重新定位光标，这里简化处理，直接将光标移到末尾
                activation_entry.icursor(tk.END)
            
            # 重新添加 trace 并保存新的 ID
            self.activation_trace_id = activation_entry_var.trace_add('write', on_entry_change)

        activation_entry_var = tk.StringVar()
        # 首次添加 trace 并保存其返回的 ID
        self.activation_trace_id = activation_entry_var.trace_add('write', on_entry_change)
        activation_entry.config(textvariable=activation_entry_var)
        
        def on_paste(event):
            try:
                clipboard_content = activation_window.clipboard_get()
                current_content = activation_entry.get()
                
                new_content = current_content + clipboard_content
                cleaned_content = ''.join(c for c in new_content if c.isalnum()).upper()
                
                if len(cleaned_content) > 16:
                    cleaned_content = cleaned_content[:16]
                
                formatted_content = '-'.join(cleaned_content[i:i+4] for i in range(0, len(cleaned_content), 4))
                
                activation_entry.delete(0, tk.END)
                activation_entry.insert(0, formatted_content)
                activation_entry.icursor(tk.END)
                
            except tk.TclError:
                pass
            return "break"
            
        activation_entry.bind('<Control-v>', on_paste)
        
        def activate_product():
            code = activation_entry.get().replace("-", "")
            if not code:
                messagebox.showwarning("警告", "请输入激活码")
                return
                
            result = self.activation_manager.activate_product(code)
            if result:
                messagebox.showinfo("成功", "软件激活成功！")
                app.is_activated = True
                app.update_activation_status()
                status_label.config(text="已激活", foreground=self.config.colors["success"])
                activation_entry.config(state=tk.DISABLED)
                activate_btn.config(state=tk.DISABLED)
                update_time_display()
                app.log("软件激活成功", "success")
            else:
                messagebox.showerror("错误", "激活码无效或已过期")
                app.log("激活失败: 激活码无效", "error")
        
        activate_btn = ttk.Button(activation_input_frame, text="激活", command=activate_product, width=8)
        activate_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        if is_activated:
            activation_entry.config(state=tk.DISABLED)
            activate_btn.config(state=tk.DISABLED)
        
        device_frame = ttk.Frame(main_frame)
        device_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(device_frame, text="设备ID:", font=("Helvetica", 9)).pack(side=tk.LEFT)
        
        device_id_var = tk.StringVar(value=self.activation_manager.get_device_id())
        device_id_entry = ttk.Entry(device_frame, textvariable=device_id_var, state="readonly", width=23)
        device_id_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        def copy_device_id():
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(device_id_var.get())
            messagebox.showinfo("成功", "设备ID已复制到剪贴板")
        
        ttk.Button(device_frame, text="复制", command=copy_device_id, width=8).pack(side=tk.LEFT, padx=(10, 0))
        
        activation_help_text = """
激活说明:
- 临时激活码: 0315 (设备绑定，有效期7天)
- 永久激活码: Mail to rizona.cn@gmail.com

Tips:
- 激活后解锁所有功能
- 未激活状态下可使用基本功能
- 过期后需要重新激活
"""
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        activation_help_text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            bg=self.config.colors["card"],
            fg=self.config.colors["text"],
            font=("Helvetica", 9),
            borderwidth=1,
            relief="solid",
            padx=10,
            pady=10
        )
        activation_help_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        activation_help_text_widget.insert(tk.END, activation_help_text.strip())
        activation_help_text_widget.config(state=tk.DISABLED)
        scrollbar.config(command=activation_help_text_widget.yview)

    def close_readme(self, window):
        window.grab_release()
        window.destroy()