# activation.py
import json
import os
import hashlib
from datetime import datetime, timedelta
import uuid
import secrets
import time

class ActivationManager:
    def __init__(self):
        self.activation_file = os.path.join(os.path.expanduser("~"), ".performance_tool_activation")
        self.temp_code = "0315"  # 临时激活码
        self.permanent_salt = "rizona"  # 用于生成永久激活码的盐值，已更正
        self.start_time = time.time()  # 记录程序启动时间

    def get_device_id(self):
        """生成设备唯一标识"""
        try:
            # 尝试获取MAC地址作为设备标识
            mac = uuid.getnode()
            return str(mac)
        except:
            # 如果获取失败，使用固定值（简单实现）
            return "default_device_id"

    def generate_permanent_code(self, device_id):
        """根据设备ID生成永久激活码"""
        # 使用设备ID和秘密盐值进行哈希
        data = f"{device_id}{self.permanent_salt}".encode('utf-8')
        hash_result = hashlib.sha256(data).hexdigest()
        
        # 取前16位作为激活码，每4位用-分隔
        code = f"{hash_result[:4]}-{hash_result[4:8]}-{hash_result[8:12]}-{hash_result[12:16]}"
        return code.upper()

    def validate_permanent_code(self, code):
        """验证永久激活码"""
        # 获取当前设备的ID
        current_device_id = self.get_device_id()
        # 根据当前设备ID生成正确的激活码
        correct_code = self.generate_permanent_code(current_device_id)
        
        # 移除连字符，然后进行比较
        return code.replace("-", "").strip().upper() == correct_code.replace("-", "").strip().upper()
        
    def activate_product(self, code):
        """激活产品"""
        # 检查是否已激活
        if self.check_activation():
            return True
            
        # 验证激活码
        clean_code = code.strip().upper()
        if clean_code == self.temp_code:
            # 临时激活码
            return self.activate_temporary()
        elif self.validate_permanent_code(clean_code):
            # 永久激活码
            return self.activate_permanent()
        else:
            return False

    def activate_temporary(self):
        """临时激活"""
        activation_info = self.load_activation_info()
        if activation_info and activation_info.get("temporary_used", False):
            return False
        activation_info = {
            "activation_type": "temporary",
            "activate_timestamp": time.time(),
            "expire_hours": 7 * 24,
            "temporary_used": True
        }
        self.save_activation_info(activation_info)
        return True

    def activate_permanent(self):
        """永久激活"""
        activation_info = {
            "activation_type": "permanent",
            "activate_timestamp": time.time()
        }
        self.save_activation_info(activation_info)
        return True

    def check_activation(self):
        """检查是否已激活"""
        activation_info = self.load_activation_info()
        if not activation_info:
            return False
            
        activation_type = activation_info.get("activation_type")
        
        if activation_type == "permanent":
            return True
            
        if activation_type == "temporary":
            activate_timestamp = activation_info.get("activate_timestamp", 0)
            expire_hours = activation_info.get("expire_hours", 0)
            
            elapsed_hours = (time.time() - self.start_time) / 3600
            
            if elapsed_hours <= expire_hours:
                return True
                
        return False

    def get_activation_info(self):
        """获取激活信息"""
        return self.load_activation_info() or {}

    def get_remaining_time(self):
        """获取剩余时间（仅对临时激活有效，基于使用时间而非系统时间）"""
        activation_info = self.load_activation_info()
        if not activation_info or activation_info.get("activation_type") != "temporary":
            return 0, 0, 0, 0
            
        activate_timestamp = activation_info.get("activate_timestamp", 0)
        expire_hours = activation_info.get("expire_hours", 0)
        
        elapsed_seconds = time.time() - self.start_time
        elapsed_hours = elapsed_seconds / 3600
        
        if elapsed_hours >= expire_hours:
            return 0, 0, 0, 0
            
        remaining_hours = expire_hours - elapsed_hours
        days = int(remaining_hours // 24)
        hours = int(remaining_hours % 24)
        minutes = int((remaining_hours * 60) % 60)
        seconds = int((remaining_hours * 3600) % 60)
        
        return days, hours, minutes, seconds

    def load_activation_info(self):
        """从文件加载激活信息"""
        if os.path.exists(self.activation_file):
            try:
                with open(self.activation_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError):
                return None
        return None
        
    def save_activation_info(self, info):
        """将激活信息保存到文件"""
        try:
            with open(self.activation_file, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=4)
            return True
        except IOError:
            return False