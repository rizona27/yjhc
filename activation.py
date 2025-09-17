# activation.py
import json
import os
import hashlib
from datetime import datetime, timedelta
import uuid
import secrets
import time
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import binascii

class ActivationManager:
    def __init__(self):
        # 激活文件1：位于用户家目录
        self.activation_file = os.path.join(os.path.expanduser("~"), ".performance_tool_activation")
        # 激活文件2：位于用户家目录，但使用不同的隐藏文件名
        self.activation_file2 = os.path.join(os.path.expanduser("~"), ".system_config_data")
        self.temp_code = "0315"  # 临时激活码
        self.permanent_salt = "rizona"  # 用于生成永久激活码的盐值
        self.start_time = time.time()  # 记录程序启动时间
        
        # 修复：将密钥长度修改为32字节，符合AES-256标准
        self.encryption_key = b'my_super_secure_key_for_encryp23'  # 32字节密钥

    def encrypt_data(self, data):
        """加密数据"""
        try:
            cipher = AES.new(self.encryption_key, AES.MODE_CBC)
            ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
            iv = cipher.iv
            return base64.b64encode(iv + ct_bytes).decode()
        except Exception as e:
            # 打印出具体的错误信息
            print(f"加密数据时发生错误: {e}")
            return None

    def decrypt_data(self, enc_data):
        """解密数据"""
        try:
            enc_data = base64.b64decode(enc_data)
            iv = enc_data[:AES.block_size]
            ct = enc_data[AES.block_size:]
            cipher = AES.new(self.encryption_key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode()
        except (ValueError, KeyError, binascii.Error):
            return None

    def get_device_id(self):
        """生成设备唯一标识"""
        try:
            mac = uuid.getnode()
            return str(mac)
        except:
            return "default_device_id"

    def generate_permanent_code(self, device_id):
        """根据设备ID生成永久激活码"""
        data = f"{device_id}{self.permanent_salt}".encode('utf-8')
        hash_result = hashlib.sha256(data).hexdigest()
        code = f"{hash_result[:4]}-{hash_result[4:8]}-{hash_result[8:12]}-{hash_result[12:16]}"
        return code.upper()

    def validate_permanent_code(self, code):
        """验证永久激活码"""
        current_device_id = self.get_device_id()
        correct_code = self.generate_permanent_code(current_device_id)
        return code.replace("-", "").strip().upper() == correct_code.replace("-", "").strip().upper()
        
    def activate_product(self, code):
        """激活产品"""
        if self.check_activation():
            return True
            
        clean_code = code.strip().upper()
        if clean_code == self.temp_code:
            return self.activate_temporary()
        elif self.validate_permanent_code(clean_code):
            return self.activate_permanent()
        else:
            return False

    def activate_temporary(self):
        """临时激活"""
        activation_info = self.load_activation_info(self.activation_file)
        if activation_info and activation_info.get("temporary_used", False):
            return False
            
        activation_info = {
            "activation_type": "temporary",
            "activate_timestamp": time.time(),
            "expire_hours": 7 * 24,
            "temporary_used": True,
            "device_id": self.get_device_id()
        }
        
        result1 = self.save_activation_info(activation_info, self.activation_file)
        result2 = self.save_activation_info(activation_info, self.activation_file2)
        
        return result1 and result2

    def activate_permanent(self):
        """永久激活"""
        activation_info = {
            "activation_type": "permanent",
            "activate_timestamp": time.time(),
            "device_id": self.get_device_id()
        }
        
        result1 = self.save_activation_info(activation_info, self.activation_file)
        result2 = self.save_activation_info(activation_info, self.activation_file2)
        
        return result1 and result2

    def check_activation(self):
        """检查是否已激活"""
        file1_exists = os.path.exists(self.activation_file)
        file2_exists = os.path.exists(self.activation_file2)
        
        if not file1_exists or not file2_exists:
            return False
            
        activation_info1 = self.load_activation_info(self.activation_file)
        activation_info2 = self.load_activation_info(self.activation_file2)
        
        if not activation_info1 or not activation_info2:
            return False
            
        # 增强验证：检查两个文件的所有关键信息是否一致，防止篡改
        if (activation_info1.get("device_id") != activation_info2.get("device_id") or
            activation_info1.get("activation_type") != activation_info2.get("activation_type")):
            return False
            
        current_device_id = self.get_device_id()
        if activation_info1.get("device_id") != current_device_id:
            return False
            
        activation_type = activation_info1.get("activation_type")
        
        if activation_type == "permanent":
            return True
            
        if activation_type == "temporary":
            activate_timestamp = activation_info1.get("activate_timestamp", 0)
            expire_hours = activation_info1.get("expire_hours", 0)
            
            elapsed_hours = (time.time() - activate_timestamp) / 3600
            
            if elapsed_hours <= expire_hours:
                return True
                
        return False

    def get_activation_info(self):
        """获取激活信息"""
        info1 = self.load_activation_info(self.activation_file)
        info2 = self.load_activation_info(self.activation_file2)
        
        # 返回任一文件的信息，因为我们已经在 check_activation 中确保了它们的一致性
        return info1 or {}

    def get_remaining_time(self):
        """获取剩余时间（基于激活时间而非程序启动时间）"""
        activation_info = self.get_activation_info()
        if not activation_info or activation_info.get("activation_type") != "temporary":
            return 0, 0, 0, 0
            
        activate_timestamp = activation_info.get("activate_timestamp", 0)
        expire_hours = activation_info.get("expire_hours", 0)
        
        elapsed_seconds = time.time() - activate_timestamp
        elapsed_hours = elapsed_seconds / 3600
        
        if elapsed_hours >= expire_hours:
            return 0, 0, 0, 0
            
        remaining_hours = expire_hours - elapsed_hours
        days = int(remaining_hours // 24)
        hours = int(remaining_hours % 24)
        minutes = int((remaining_hours * 60) % 60)
        seconds = int((remaining_hours * 3600) % 60)
        
        return days, hours, minutes, seconds

    def load_activation_info(self, file_path=None):
        """从文件加载激活信息"""
        if file_path is None:
            file_path = self.activation_file
            
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    encrypted_data = f.read()
                    decrypted_data = self.decrypt_data(encrypted_data)
                    if decrypted_data:
                        return json.loads(decrypted_data)
            except (IOError, json.JSONDecodeError):
                return None
        return None
        
    def save_activation_info(self, info, file_path=None):
        """将激活信息保存到文件"""
        if file_path is None:
            file_path = self.activation_file
            
        try:
            json_data = json.dumps(info)
            # 检查加密数据是否为None
            encrypted_data = self.encrypt_data(json_data)
            if encrypted_data is None:
                print("加密失败，无法保存激活信息。")
                return False
                
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(encrypted_data)
            return True
        except IOError:
            print("保存文件时发生IO错误。")
            return False