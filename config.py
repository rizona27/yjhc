# config.py
import os
import json
import tkinter as tk

class Config:
    def __init__(self):
        # 更新为更明亮、更鲜明的配色方案
        self.colors = {
            "background": "#F5F8FA",
            "card": "#FFFFFF",
            "primary": "#2C3E50",
            "primary_hover": "#34495E",
            "secondary": "#7F8C8D",
            "accent": "#5B9BD5",
            "text": "#2C3E50",
            "text_light": "#7F8C8D",
            "chart_line": "#2980B9",
            # 新增悬停十字线颜色
            "chart_hover": "#FFA500",
            "chart_grid": "#D5DBDB",
            "chart_bg": "#FFFFFF",
            "button": "#5B9BD5",
            "button_hover": "#4A8BC5",
            "highlight": "#4682B4",
            "status_bar": "#E0E8F0",
            "group_box": "#E6F0F8",
            "border": "#A0C0E0",
            "input_bg": "#FFFFFF",
            "success": "#28A745",
            "warning": "#FFC107",
            "error": "#DC3545",
            "info": "#17A2B8",
            "placeholder": "#AAAAAA",
            "max_color": "#E74C3C",
            "min_color": "#27AE60"
        }
        
        self.settings = {
            "show_hover_data": False,  # 默认关闭悬停数据
            "hover_date": "",
            "export_directory": os.getcwd(),
            "show_log_window": False,  # 修改为默认关闭日志窗口
            "show_textbox": False,  # 添加默认关闭提示框
            "max_min_position": "top-left",  # top-left, top-right, bottom-left, bottom-right
            "textbox_alpha": 0.5  # 提示框透明度
        }
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.expanduser("~"), ".performance_tool_config")
        
        # 加载配置文件
        self.load_config()
    
    def get(self, key, default=None):
        return self.settings.get(key, default)
    
    def set(self, key, value):
        self.settings[key] = value
        # 保存配置到文件
        self.save_config()
        
    def load_config(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except (IOError, json.JSONDecodeError):
                # 如果加载失败，使用默认配置
                pass
                
    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except IOError:
            pass