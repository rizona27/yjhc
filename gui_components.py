# gui_components.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from utils import log_to_text_widget

def create_menu_bar(app):
    """创建菜单栏"""
    menubar = tk.Menu(app.root)
    app.root.config(menu=menubar)

    # 文件菜单
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="文件", menu=file_menu)
    file_menu.add_command(label="导入文件", command=app.import_data)
    file_menu.add_command(label="导出图表", command=app.export_chart, state=tk.DISABLED)
    file_menu.add_separator()
    file_menu.add_command(label="退出", command=lambda: app.root.quit())

    # 设置菜单
    settings_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="设置", menu=settings_menu)

    # 按照新顺序添加菜单项
    settings_menu.add_command(
        label="导出图表设置",
        command=app.set_export_chart_settings
    )

    settings_menu.add_command(
        label="导出目录设置",
        command=app.set_export_directory
    )

    settings_menu.add_command(
        label="提示框设置",
        command=app.set_textbox_settings
    )

    # 日志窗口设置 - 根据当前状态显示不同的文本
    log_window_label = "关闭日志" if app.config.get("show_log_window", True) else "开启日志"
    settings_menu.add_command(
        label=log_window_label,
        command=app.set_log_window
    )

    # 关于菜单
    about_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="关于", menu=about_menu)
    about_menu.add_command(label="使用说明", command=app.show_readme)
    about_menu.add_command(label="工具激活", command=app.show_activation)  

    return menubar, settings_menu

def create_main_interface(app, parent):
    """创建主界面，使用 place 布局"""
    main_frame = ttk.Frame(parent)
    main_frame.pack(fill=tk.BOTH, expand=True)
    main_frame.configure(style="TFrame")

    # 计算布局参数
    main_width = 800  # 主窗口宽度
    log_width = 300   # 日志窗口宽度
    chart_height = 270 # 图表高度
    top_height = 240  # 增加顶部组件高度到240
    
    # 可用宽度减去日志窗口和边距
    available_width = main_width - log_width - 20
    
    # 左侧容器 - 自定义周期回测
    left_width = 170
    left_container = ttk.LabelFrame(main_frame, text="自定义周期回测")
    left_container.place(x=10, y=10, width=left_width, height=top_height)
    left_container.configure(style="TLabelframe")
    left_container.pack_propagate(False)

    # 自定义周期回测结果 - 上半部分
    custom_result_container = ttk.Frame(left_container)
    custom_result_container.pack(fill=tk.X, padx=5, pady=(2, 2))
    custom_result_container.configure(style="TFrame")

    # 使用grid布局确保对齐和紧凑
    row_idx = 0
    label_width = 10
    value_width = 12

    ttk.Label(custom_result_container, text="日期范围:", width=label_width, anchor=tk.W,
              font=("Helvetica", 9), style="TLabel").grid(row=row_idx, column=0, sticky=tk.W, padx=(0, 2))
    custom_range_start_label = ttk.Label(custom_result_container, text="--", width=value_width,
              font=("Helvetica", 9), style="TLabel")
    custom_range_start_label.grid(row=row_idx, column=1, sticky=tk.W)
    row_idx += 1

    ttk.Label(custom_result_container, text="至:", width=label_width, anchor=tk.W,
              font=("Helvetica", 9), style="TLabel").grid(row=row_idx, column=0, sticky=tk.W, padx=(0, 2))
    custom_range_end_label = ttk.Label(custom_result_container, text="", width=value_width,
              font=("Helvetica", 9), style="TLabel")
    custom_range_end_label.grid(row=row_idx, column=1, sticky=tk.W)
    row_idx += 1

    ttk.Label(custom_result_container, text="周期天数:", width=label_width, anchor=tk.W,
              font=("Helvetica", 9), style="TLabel").grid(row=row_idx, column=0, sticky=tk.W, padx=(0, 2))
    custom_days_label = ttk.Label(custom_result_container, text="--", width=value_width,
              font=("Helvetica", 9), style="TLabel")
    custom_days_label.grid(row=row_idx, column=1, sticky=tk.W)
    row_idx += 1

    ttk.Label(custom_result_container, text="年化收益率:", width=label_width, anchor=tk.W,
              font=("Helvetica", 9), style="TLabel").grid(row=row_idx, column=0, sticky=tk.W, padx=(0, 2))
    custom_return_label_value = ttk.Label(custom_result_container, text="--", width=value_width,
              font=("Helvetica", 9), style="TLabel")
    custom_return_label_value.grid(row=row_idx, column=1, sticky=tk.W)
    row_idx += 1

    ttk.Label(custom_result_container, text="最大回撤:", width=label_width, anchor=tk.W,
              font=("Helvetica", 9), style="TLabel").grid(row=row_idx, column=0, sticky=tk.W, padx=(0, 2))
    custom_drawdown_label_value = ttk.Label(custom_result_container, text="--", width=value_width,
              font=("Helvetica", 9), style="TLabel")
    custom_drawdown_label_value.grid(row=row_idx, column=1, sticky=tk.W)
    row_idx += 1

    button_frame = ttk.Frame(custom_result_container)
    button_frame.grid(row=row_idx, column=0, columnspan=2, pady=(5, 2), sticky=tk.W)

    btn_custom = ttk.Button(button_frame, text="区间", command=app.custom_analysis, style="TButton", width=5)
    btn_custom.pack(side=tk.LEFT, padx=(0, 5))

    btn_reset = ttk.Button(button_frame, text="全览", command=app.reset_to_full_view, state=tk.DISABLED, style="TButton", width=5)
    btn_reset.pack(side=tk.LEFT, padx=(0, 5))

    btn_reset_app = ttk.Button(button_frame, text="重置", command=app.reset_application, style="TButton", width=5)
    btn_reset_app.pack(side=tk.LEFT)

    separator = ttk.Separator(left_container, orient='horizontal')
    separator.pack(fill=tk.X, padx=5, pady=(0, 0))

    date_range_frame = ttk.Frame(left_container)
    date_range_frame.pack(fill=tk.X, padx=5, pady=5)
    date_range_frame.configure(style="TFrame")

    start_frame = ttk.Frame(date_range_frame)
    start_frame.pack(fill=tk.X, pady=(3,0))

    ttk.Label(start_frame, text="开始日期:", width=8, style="TLabel").pack(side=tk.LEFT)

    # 修改：先创建正常状态的输入框，插入文本并设置颜色，然后禁用
    start_entry = ttk.Entry(start_frame, width=12, style="TEntry", state='normal')
    start_entry.insert(0, "YYYY-MM-DD")
    start_entry.configure(foreground=app.config.colors["placeholder"])
    start_entry.config(state='disabled')  # 最后禁用
    start_entry.pack(side=tk.LEFT, padx=3)

    start_entry.bind("<FocusIn>", app.on_start_focus_in)
    start_entry.bind("<FocusOut>", app.on_start_focus_out)
    start_entry.bind("<Return>", app.on_start_return)

    end_frame = ttk.Frame(date_range_frame)
    end_frame.pack(fill=tk.X, pady=(3,0))

    ttk.Label(end_frame, text="结束日期:", width=8, style="TLabel").pack(side=tk.LEFT)

    # 修改：先创建正常状态的输入框，插入文本并设置颜色，然后禁用
    end_entry = ttk.Entry(end_frame, width=12, style="TEntry", state='normal')
    end_entry.insert(0, "YYYY-MM-DD")
    end_entry.configure(foreground=app.config.colors["placeholder"])
    end_entry.config(state='disabled')  # 最后禁用
    end_entry.pack(side=tk.LEFT, padx=3)

    end_entry.bind("<FocusIn>", app.on_end_focus_in)
    end_entry.bind("<FocusOut>", app.on_end_focus_out)
    end_entry.bind("<Return>", app.on_end_return)

    # 固定周期回测
    # 使用 place 布局，精确控制位置和大小
    fixed_width = available_width - left_width - 5  # 减去左侧容器宽度和间距
    fixed_freq_frame = ttk.LabelFrame(main_frame, text="固定周期回测")
    fixed_freq_frame.place(x=left_width + 15, y=10, width=fixed_width, height=top_height)
    fixed_freq_frame.pack_propagate(False)
    fixed_freq_frame.configure(style="TLabelframe")

    # 创建Treeview的容器框架
    tree_container = ttk.Frame(fixed_freq_frame)
    tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    columns = ("freq", "days", "return", "drawdown")
    result_tree = ttk.Treeview(
        tree_container,
        columns=columns,
        show="headings",
        height=9,
        selectmode="none"
    )

    result_tree.heading("freq", text="周期", anchor=tk.W)
    result_tree.heading("days", text="天数", anchor=tk.CENTER)
    result_tree.heading("return", text="年化收益率", anchor=tk.CENTER)
    result_tree.heading("drawdown", text="最大回撤", anchor=tk.CENTER)

    # 调整列宽以适应新的容器宽度
    col_widths = {
        "freq": 70,
        "days": 60,
        "return": 90,
        "drawdown": 80
    }
    
    result_tree.column("freq", width=col_widths["freq"], minwidth=60, stretch=False, anchor=tk.W)
    result_tree.column("days", width=col_widths["days"], minwidth=50, stretch=False, anchor=tk.CENTER)
    result_tree.column("return", width=col_widths["return"], minwidth=80, stretch=True, anchor=tk.CENTER)
    result_tree.column("drawdown", width=col_widths["drawdown"], minwidth=80, stretch=True, anchor=tk.CENTER)

    result_tree.bind('<Button-1>', lambda event: 'break')
    result_tree.bind('<Motion>', lambda e: 'break')

    result_tree.pack(fill=tk.BOTH, expand=True)

    fixed_freq_placeholders = [
        ("近1周", '/'), ("近2周", '/'), ("近3周", '/'),
        ("近1月", '/'), ("近2月", '/'), ("近3月", '/'),
        ("近6月", '/'), ("近1年", '/'), ("成立以来", '/')
    ]
    for freq, placeholder in fixed_freq_placeholders:
        result_tree.insert("", "end", values=(freq, placeholder, placeholder, placeholder))

    # 净值趋势图容器
    # 使用 place 布局，精确控制位置和大小
    chart_frame = ttk.LabelFrame(main_frame, text="净值趋势图")
    chart_frame.place(x=10, y=top_height + 20, width=available_width, height=chart_height)
    chart_frame.pack_propagate(False)
    chart_frame.configure(style="TLabelframe")

    components = {
        "main_frame": main_frame,
        "custom_range_start_label": custom_range_start_label,
        "custom_range_end_label": custom_range_end_label,
        "custom_days_label": custom_days_label,
        "custom_return_label_value": custom_return_label_value,
        "custom_drawdown_label_value": custom_drawdown_label_value,
        "start_entry": start_entry,
        "end_entry": end_entry,
        "result_tree": result_tree,
        "btn_custom": btn_custom,
        "btn_reset": btn_reset,
        "btn_reset_app": btn_reset_app,
        "chart_frame": chart_frame
    }

    return main_frame, components

def create_log_window(app, parent):
    """创建内嵌的日志窗口，使用 place 布局"""
    main_width = 300
    log_width = 280
    log_height = 520
    log_x = main_width - log_width - 10   
    log_frame = ttk.Frame(parent)
    log_frame.place(x=log_x, y=10, width=log_width, height=log_height)
    log_frame.pack_propagate(False)
    log_notebook = ttk.Notebook(log_frame)
    log_notebook.pack(fill=tk.BOTH, expand=True)

    # 设置Notebook样式
    style = ttk.Style()
    style.configure("TNotebook", background=app.config.colors["background"])
    style.configure("TNotebook.Tab", 
                   background=app.config.colors["group_box"],
                   foreground=app.config.colors["text"],
                   padding=[10, 2])
    style.map("TNotebook.Tab", 
             background=[("selected", app.config.colors["primary"])],
             foreground=[("selected", "white")])

    success_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(success_log_frame, text="成功")
    success_log_text = scrolledtext.ScrolledText(
        success_log_frame,
        wrap=tk.WORD,
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg=app.config.colors["success"],
        borderwidth=1,
        relief="solid"
    )
    success_log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    success_log_text.config(state=tk.DISABLED)

    warning_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(warning_log_frame, text="警告")
    warning_log_text = scrolledtext.ScrolledText(
        warning_log_frame,
        wrap=tk.WORD,
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg=app.config.colors["warning"],
        borderwidth=1,
        relief="solid"
    )
    warning_log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    warning_log_text.config(state=tk.DISABLED)

    info_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(info_log_frame, text="信息")
    info_log_text = scrolledtext.ScrolledText(
        info_log_frame,
        wrap=tk.WORD,
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg=app.config.colors["info"],
        borderwidth=1,
        relief="solid"
    )
    info_log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    info_log_text.config(state=tk.DISABLED)

    error_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(error_log_frame, text="错误")
    error_log_text = scrolledtext.ScrolledText(
        error_log_frame,
        wrap=tk.WORD,
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg=app.config.colors["error"],
        borderwidth=1,
        relief="solid"
    )
    error_log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    error_log_text.config(state=tk.DISABLED)

    log_notebook.select(0)

    log_texts = {
        "success": success_log_text,
        "warning": warning_log_text,
        "info": info_log_text,
        "error": error_log_text
    }

    return log_texts