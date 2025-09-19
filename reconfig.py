# reset_config.py
import os
import sys

def get_config_path():
    """
    获取配置文件的绝对路径。
    此函数会检查用户主目录。
    """
    config_file_name = ".performance_tool_config"
    config_path = os.path.join(os.path.expanduser("~"), config_file_name)
    return config_path

def reset_config_with_log():
    """
    删除配置文件，并提供详细的日志输出。
    """
    print("--- 开始重置配置 ---")
    
    config_path = get_config_path()
    print(f"正在查找配置文件，预期路径为：{config_path}")
    
    if os.path.exists(config_path):
        print("》》文件已找到！正在尝试删除...")
        try:
            os.remove(config_path)
            print("》》成功删除！")
            print("--- 配置已重置为默认值。下次运行应用程序时将使用默认设置。---")
        except OSError as e:
            print(f"!!! 错误：删除文件时出错: {e}")
            print("!!! 请确保应用程序已完全关闭，并且您有权限删除此文件。")
    else:
        print("》》未找到文件。")
        print("--- 配置已经是默认值，无需重置。---")
        
    print("--- 重置过程结束 ---")

if __name__ == "__main__":
    reset_config_with_log()