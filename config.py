# config.py 完整代码（修改后）
import os
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
            "placeholder": "#AAAAAA",
            "max_color": "#E74C3C",
            "min_color": "#27AE60"
        }
        
        self.settings = {
            "show_hover_data": False,  # 默认关闭悬停数据
            "hover_date": "",
            "export_directory": os.getcwd(),
            "show_log_window": True,
            "max_min_position": "top-left",  # top-left, top-right, bottom-left, bottom-right
            "textbox_alpha": 0.9  # 提示框透明度
        }
    
    def get(self, key):
        return self.settings.get(key)
    
    def set(self, key, value):
        self.settings[key] = value