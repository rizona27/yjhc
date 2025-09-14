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
    
    # 导出图表设置子菜单
    export_settings_menu = tk.Menu(settings_menu, tearoff=0)
    settings_menu.add_cascade(label="导出图表设置", menu=export_settings_menu)
    export_settings_menu.add_command(
        label="设置导出图表选项", 
        command=app.set_export_chart_settings
    )
    
    # 导出目录设置
    settings_menu.add_command(
        label="导出目录设置", 
        command=app.set_export_directory
    )
    
    # 日志窗口设置
    settings_menu.add_command(
        label="日志窗口设置", 
        command=app.set_log_window
    )
    
    # 提示框设置
    settings_menu.add_command(
        label="提示框设置", 
        command=app.set_textbox_settings
    )
    
    # 关于菜单
    about_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="关于", menu=about_menu)
    about_menu.add_command(label="说明", command=app.show_readme)
    
    return menubar

def create_main_interface(app):
    """创建主界面"""
    main_frame = ttk.Frame(app.root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    main_frame.configure(style="TFrame")
    
    top_frame = ttk.Frame(main_frame)
    top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
    top_frame.configure(style="TFrame")
    
    # 左侧容器 - 自定义周期回测
    left_container = ttk.LabelFrame(top_frame, text="自定义周期回测", width=250, height=250)  # 增加宽度和高度
    left_container.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
    left_container.pack_propagate(False)  # 固定高度
    left_container.configure(style="TLabelframe")
    
    # 自定义周期回测结果
    custom_result_container = ttk.Frame(left_container)
    custom_result_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    custom_result_container.configure(style="TFrame")
    
    custom_range_label = ttk.Label(
        custom_result_container, 
        text="日期范围: --",
        font=("Helvetica", 9),
        style="TLabel"
    )
    custom_range_label.pack(anchor=tk.W, pady=3)
    
    custom_days_label = ttk.Label(
        custom_result_container, 
        text="周期天数: --",
        font=("Helvetica", 9),
        style="TLabel"
    )
    custom_days_label.pack(anchor=tk.W, pady=3)

    # 优化显示，将标签和数值放在同一行
    return_frame = ttk.Frame(custom_result_container, style="TFrame")
    return_frame.pack(anchor=tk.W, pady=3)
    
    custom_return_label_text = ttk.Label(
        return_frame, 
        text="年化收益率: ",
        font=("Helvetica", 9),
        style="TLabel"
    )
    custom_return_label_text.pack(side=tk.LEFT)
    
    custom_return_label_value = ttk.Label(
        return_frame, 
        text="--",
        font=("Helvetica", 9),
        style="TLabel"
    )
    custom_return_label_value.pack(side=tk.LEFT)
    
    drawdown_frame = ttk.Frame(custom_result_container, style="TFrame")
    drawdown_frame.pack(anchor=tk.W, pady=3)

    custom_drawdown_label_text = ttk.Label(
        drawdown_frame, 
        text="最大回撤: ",
        font=("Helvetica", 9),
        style="TLabel"
    )
    custom_drawdown_label_text.pack(side=tk.LEFT)
    
    custom_drawdown_label_value = ttk.Label(
        drawdown_frame, 
        text="--",
        font=("Helvetica", 9),
        style="TLabel"
    )
    custom_drawdown_label_value.pack(side=tk.LEFT)
    
    # 自定义日期区间
    date_range_frame = ttk.Frame(custom_result_container)
    date_range_frame.pack(fill=tk.X, pady=(15, 0))  # 增加上边距
    date_range_frame.configure(style="TFrame")
    
    start_frame = ttk.Frame(date_range_frame)
    start_frame.pack(fill=tk.X, padx=3, pady=3)
    start_frame.configure(style="TFrame")
    
    ttk.Label(start_frame, text="开始日期:", width=8, 
             style="TLabel").pack(side=tk.LEFT)
    
    start_entry = ttk.Entry(start_frame, width=12, style="TEntry")
    start_entry.pack(side=tk.LEFT, padx=3)
    start_entry.insert(0, "YYYY-MM-DD")
    start_entry.configure(foreground=app.config.colors["placeholder"])
    
    start_entry.bind("<FocusIn>", app.on_start_focus_in)
    start_entry.bind("<FocusOut>", app.on_start_focus_out)
    start_entry.bind("<Return>", app.on_start_return)
    
    end_frame = ttk.Frame(date_range_frame)
    end_frame.pack(fill=tk.X, padx=3, pady=3)
    end_frame.configure(style="TFrame")
    
    ttk.Label(end_frame, text="结束日期:", width=8, 
             style="TLabel").pack(side=tk.LEFT)
    
    end_entry = ttk.Entry(end_frame, width=12, style="TEntry")
    end_entry.pack(side=tk.LEFT, padx=3)
    end_entry.insert(0, "YYYY-MM-DD")
    end_entry.configure(foreground=app.config.colors["placeholder"])
    
    end_entry.bind("<FocusIn>", app.on_end_focus_in)
    end_entry.bind("<FocusOut>", app.on_end_focus_out)
    end_entry.bind("<Return>", app.on_end_return)
    
    analysis_frame = ttk.Frame(top_frame)
    analysis_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
    analysis_frame.configure(style="TFrame")
    
    analysis_horizontal_frame = ttk.Frame(analysis_frame)
    analysis_horizontal_frame.pack(fill=tk.BOTH, expand=True)
    analysis_horizontal_frame.configure(style="TFrame")
    
    fixed_freq_frame = ttk.LabelFrame(analysis_horizontal_frame, text="固定周期回测", width=280)
    fixed_freq_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
    fixed_freq_frame.configure(style="TLabelframe")
    fixed_freq_frame.pack_propagate(False)  # 固定宽度
    
    # 创建Treeview的容器框架，去除多余的边框
    tree_container = ttk.Frame(fixed_freq_frame)
    tree_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
    
    columns = ("freq", "days", "return", "drawdown")
    result_tree = ttk.Treeview(
        tree_container, 
        columns=columns, 
        show="headings",
        height=8,
        selectmode="none"
    )
    
    result_tree.heading("freq", text="周期", anchor=tk.W)
    result_tree.heading("days", text="天数", anchor=tk.CENTER)
    result_tree.heading("return", text="年化收益率", anchor=tk.CENTER)
    result_tree.heading("drawdown", text="最大回撤", anchor=tk.CENTER)
    
    # 调整列宽使其更紧凑，去除右侧空白
    result_tree.column("freq", width=60, anchor=tk.W, stretch=False)
    result_tree.column("days", width=40, anchor=tk.CENTER, stretch=False)
    result_tree.column("return", width=70, anchor=tk.CENTER, stretch=False)
    result_tree.column("drawdown", width=70, anchor=tk.CENTER, stretch=False)
    
    # 添加垂直滚动条
    vsb = ttk.Scrollbar(tree_container, orient="vertical", command=result_tree.yview)
    result_tree.configure(yscrollcommand=vsb.set)
    
    result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    
    # 修正1: 默认显示固定周期指标，用 / 占位
    fixed_freq_placeholders = [
        ("近1周", '/'), ("近2周", '/'), ("近3周", '/'),
        ("近1月", '/'), ("近2月", '/'), ("近3月", '/'),
        ("近6月", '/'), ("近1年", '/'), ("成立以来", '/')
    ]
    for freq, placeholder in fixed_freq_placeholders:
        result_tree.insert("", "end", values=(freq, placeholder, placeholder, placeholder))

    right_container = ttk.Frame(analysis_horizontal_frame)
    right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(5, 0))
    right_container.configure(style="TFrame")
    right_container.pack_propagate(False)  # 防止按钮改变容器大小
    right_container.configure(width=100)  # 固定宽度
    
    # 添加按钮框架到右侧 - 移除标题
    btn_container = ttk.Frame(right_container)
    btn_container.pack(fill=tk.BOTH, expand=True, pady=(0, 0))  # 移除上边距，使按钮与左侧对齐
    
    # 固定按钮宽度
    btn_custom = ttk.Button(
        btn_container, 
        text="分析区间", 
        command=app.custom_analysis,
        style="TButton",
        width=10  # 固定宽度
    )
    btn_custom.pack(fill=tk.X, padx=5, pady=(0, 5))  # 调整上边距为0
    
    btn_reset = ttk.Button(
        btn_container, 
        text="恢复全览", 
        command=app.reset_to_full_view,
        state=tk.DISABLED,
        style="TButton",
        width=10  # 固定宽度
    )
    btn_reset.pack(fill=tk.X, padx=5, pady=5)
    
    btn_reset_app = ttk.Button(
        btn_container, 
        text="重置数据",  # 改为重置数据
        command=app.reset_application,
        style="TButton",
        width=10  # 固定宽度
    )
    btn_reset_app.pack(fill=tk.X, padx=5, pady=5)
    
    chart_frame = ttk.LabelFrame(main_frame, text="净值趋势图")
    chart_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
    chart_frame.configure(style="TLabelframe")
    
    components = {
        "main_frame": main_frame,
        "custom_range_label": custom_range_label,
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

def create_log_window(app):
    """创建独立的日志窗口"""
    # 创建独立的日志窗口
    log_window = tk.Toplevel(app.root)
    log_window.title("系统日志")
    log_window.geometry("400x520")
    log_window.resizable(False, False)
    log_window.transient(app.root)  # 设置为主窗口的附属窗口
    log_window.protocol("WM_DELETE_WINDOW", app.hide_log_window)  # 关闭时隐藏而不是销毁
    
    # 设置窗口位置在主窗口右侧
    app.root.update_idletasks()
    root_x = app.root.winfo_x()
    root_y = app.root.winfo_y()
    root_width = app.root.winfo_width()
    
    log_window.geometry(f"+{root_x + root_width + 10}+{root_y}")
    
    # 创建不同类别的日志标签页
    log_notebook = ttk.Notebook(log_window)
    log_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 所有日志标签页
    all_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(all_log_frame, text="所有日志")
    
    log_text = scrolledtext.ScrolledText(
        all_log_frame, 
        wrap=tk.WORD, 
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg=app.config.colors["text"],
        borderwidth=1,
        relief="solid"
    )
    log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    log_text.config(state=tk.DISABLED)

    # 为日志窗口添加颜色标签
    log_text.tag_configure("info", foreground=app.config.colors["text"])
    log_text.tag_configure("success", foreground="#27AE60")
    log_text.tag_configure("warning", foreground="#E74C3C")
    log_text.tag_configure("error", foreground="#C0392B")
    
    # 信息日志标签页
    info_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(info_log_frame, text="信息")
    
    info_log_text = scrolledtext.ScrolledText(
        info_log_frame, 
        wrap=tk.WORD, 
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg=app.config.colors["text"],
        borderwidth=1,
        relief="solid"
    )
    info_log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    info_log_text.config(state=tk.DISABLED)
    
    # 成功日志标签页
    success_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(success_log_frame, text="成功")
    
    success_log_text = scrolledtext.ScrolledText(
        success_log_frame, 
        wrap=tk.WORD, 
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg="#27AE60",
        borderwidth=1,
        relief="solid"
    )
    success_log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    success_log_text.config(state=tk.DISABLED)
    
    # 警告日志标签页
    warning_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(warning_log_frame, text="警告")
    
    warning_log_text = scrolledtext.ScrolledText(
        warning_log_frame, 
        wrap=tk.WORD, 
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg="#E74C3C",
        borderwidth=1,
        relief="solid"
    )
    warning_log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    warning_log_text.config(state=tk.DISABLED)
    
    # 错误日志标签页
    error_log_frame = ttk.Frame(log_notebook)
    log_notebook.add(error_log_frame, text="错误")
    
    error_log_text = scrolledtext.ScrolledText(
        error_log_frame, 
        wrap=tk.WORD, 
        font=("Courier", 8),
        bg=app.config.colors["card"],
        fg="#C0392B",
        borderwidth=1,
        relief="solid"
    )
    error_log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
    error_log_text.config(state=tk.DISABLED)
    
    # 存储所有日志文本框引用
    log_texts = {
        "all": log_text,
        "info": info_log_text,
        "success": success_log_text,
        "warning": warning_log_text,
        "error": error_log_text
    }
    
    # 默认显示日志窗口
    if app.config.get("show_log_window"):
        log_window.deiconify()
    else:
        log_window.withdraw()
    
    app.log_window = log_window
    
    return log_texts