# utils.py
import pandas as pd
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import os
import sys
import psutil
from datetime import datetime
import re
from dateutil.parser import parse as dateutil_parse
import warnings
import chardet

# 全局变量跟踪打开的窗口数
OPEN_WINDOWS = 0
MAX_WINDOWS = 1

# 忽略openpyxl的样式警告
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl.styles.stylesheet")

# 辅助函数，不依赖于主应用类

def log_message(message, message_type="info"):
    """一个简单的日志函数，用于不依赖Tkinter的场景"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{message_type}] {message}")

def log_to_text_widget(text_widget, message, message_type="info"):
    """将日志信息添加到Tkinter的ScrolledText组件中"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    # 根据消息类型选择标签
    if "失败" in message or "错误" in message:
        tag = "error"
    elif "警告" in message:
        tag = "warning"
    elif "成功" in message or "完成" in message:
        tag = "success"
    else:
        tag = "info"
    
    try:
        text_widget.config(state='normal')
        text_widget.insert('end', log_entry + '\n', tag)
        text_widget.config(state='disabled')
        text_widget.see('end')
    except:
        pass

def setup_fonts():
    """配置Matplotlib以支持中文显示"""
    # 尝试使用微软雅黑
    if 'Microsoft YaHei' in fm.findfont(fm.FontProperties(family='Microsoft YaHei', weight='normal')):
        plt.rcParams['font.family'] = 'Microsoft YaHei'
    else:
        # 如果没有，则寻找系统中的任一中文字体
        font_paths = fm.findSystemFonts(fontpaths=None, fontext='ttf')
        for font_path in font_paths:
            font_prop = fm.FontProperties(fname=font_path)
            if any('\u4e00' <= char <= '\u9fff' for char in font_prop.get_name()):
                plt.rcParams['font.family'] = font_prop.get_name()
                break
    plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

def normalize_date_string(date_str, log_callback):
    """尝试将多种日期字符串格式转换为 YYYY-MM-DD 格式"""
    date_str = str(date_str).strip()
    if not date_str:
        return date_str

    try:
        # 尝试使用 dateutil.parser 智能解析
        parsed_date = dateutil_parse(date_str, fuzzy=False)
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        log_callback(f"无法使用 dateutil.parser 解析日期: '{date_str}'", "warning")
        
        # 如果智能解析失败，尝试用正则表达式和手动处理
        date_str = re.sub(r'[/\\.-]', '-', date_str)
        parts = date_str.split('-')
        
        if len(parts) == 3:
            year, month, day = parts
            if len(year) == 2:
                year = f'20{year}'
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
        
        if len(date_str) == 8 and date_str.isdigit():
            return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
        
        raise ValueError(f"无法识别的日期格式: {date_str}")
    except Exception as e:
        log_callback(f"日期规范化过程中发生未知错误: {e}", "error")
        raise ValueError(f"日期规范化失败: {date_str}")

def parse_dates(date_series, log_callback):
    """对DataFrame的日期列进行批量解析，同时记录无法解析的日期"""
    parsed_dates = pd.to_datetime(date_series, errors='coerce', format='mixed')
    
    invalid_mask = parsed_dates.isna()
    if invalid_mask.any():
        invalid_dates = date_series[invalid_mask]
        unique_invalid = invalid_dates.unique()
        for date_str in unique_invalid:
            log_callback(f"警告: 日期格式 '{date_str}' 无效，已跳过。", "warning")

    return parsed_dates

def detect_file_type(file_path, log_callback):
    """通过文件扩展名和内容检测文件类型"""
    file_path = str(file_path)
    
    # 优先检查文件内容是否为 Excel XLSX 格式
    try:
        with open(file_path, 'rb') as f:
            header = f.read(2)
            if header == b'PK':
                log_callback("警告：文件扩展名为.csv，但内容为XLSX格式。", "warning")
                return 'excel'
    except Exception as e:
        log_callback(f"文件内容类型检测失败: {e}", "warning")
        
    # 如果文件内容不是 XLSX，则回退到按扩展名判断
    if file_path.lower().endswith(('.xlsx', '.xls')):
        return 'excel'
    if file_path.lower().endswith('.csv'):
        return 'csv'
    
    return 'unknown'


def read_csv_file(file_path, log_callback):
    """读取CSV文件，自动检测编码"""
    encodings = ['utf-8', 'gbk', 'gb18030', 'iso-8859-1']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, engine='python')
            log_callback(f"成功读取CSV文件: {len(df)}行 (使用编码: {encoding})", "success")
            return df
        except UnicodeDecodeError:
            log_callback(f"尝试使用编码 {encoding} 解码失败。", "warning")
        except Exception as e:
            log_callback(f"读取CSV文件失败: {str(e)}", "error")
            return None
    log_callback("无法找到合适的编码来读取CSV文件。", "error")
    return None

def read_excel_file(file_path, log_callback):
    """读取Excel文件"""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        log_callback(f"成功读取Excel文件: {len(df)}行", "success")
        return df
        # Added to handle older excel formats
    except Exception as e:
        try:
            df = pd.read_excel(file_path, engine='xlrd')
            log_callback(f"成功读取Excel文件: {len(df)}行 (使用xlrd引擎)", "success")
            return df
        except:
            try:
                df = pd.read_excel(file_path, engine='odf')
                log_callback(f"成功读取Excel文件: {len(df)}行 (使用odf引擎)", "success")
                return df
            except:
                log_callback(f"读取Excel文件失败: {str(e)}", "error")
                return None

def cleanup_exit(root):
    """清理资源并完全退出程序"""
    global OPEN_WINDOWS
    OPEN_WINDOWS -= 1
    
    plt.close('all')
    root.destroy()
    terminate_child_processes()
    sys.exit(0)

def terminate_child_processes():
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
    except psutil.NoSuchProcess:
        pass

def clean_numeric_string(s):
    """清理字符串中的非数字字符，但保留小数点"""
    if isinstance(s, (int, float, np.int64, np.float64)):
        return s
    
    s = str(s).strip()
    # 移除所有非数字和小数点字符
    cleaned_s = re.sub(r'[^\d.]', '', s)
    
    # 确保只有一个小数点
    if '.' in cleaned_s:
        parts = cleaned_s.split('.')
        cleaned_s = parts[0] + '.' + ''.join(parts[1:])

    # 如果清理后字符串为空，则返回 NaN
    if not cleaned_s:
        return np.nan
        
    return cleaned_s