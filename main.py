import tkinter as tk
from tkinter import messagebox
import datetime
import os
import base64
import hashlib
from cryptography.fernet import Fernet
import requests
from time import localtime

PASSWORD_FILE = "password.txt"
SALT_SIZE = 16  # 盐长度
KEY_FILE = "key.bin"

# 生成密钥并保存
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    return key

# 读取密钥
def load_key():
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, "rb") as f:
        return f.read()

# 加密密码
def encrypt_password(pwd, key):
    f = Fernet(key)
    return f.encrypt(pwd.encode('utf-8')).decode('utf-8')

# 解密密码
def decrypt_password(token, key):
    f = Fernet(key)
    return f.decrypt(token.encode('utf-8')).decode('utf-8')

# 加密密码（加盐+hash）
def encrypt_password_old(pwd, salt=None):
    if salt is None:
        salt = os.urandom(SALT_SIZE)
    pwd_bytes = pwd.encode('utf-8')
    hash_bytes = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt, 100000)
    return base64.b64encode(salt + hash_bytes).decode('utf-8')

# 解密（校验）密码
# 这里只做存储和显示，不做明文还原
# 如果需要明文显示，建议用对称加密算法（如Fernet），这里按hash存储安全性更高

# 通过API获取北京时间
def get_network_time():
    try:
        resp = requests.get('https://cn.apihz.cn/api/time/getapi.php?key=1c2ead8e97cfe03a162c436a92bf294d&id=10004464&type=2', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('code') == 200:
                dt = datetime.datetime.strptime(data['msg'], '%Y-%m-%d %H:%M:%S')
                return dt
    except Exception as e:
        print(f"获取网络时间失败: {e}")
    return None

def can_view_password():
    now = get_network_time()
    if now is None:
        messagebox.showerror("错误", "无法获取网络时间，禁止查看密码")
        return False
    day = now.weekday()  # 0:周一, 1:周二, 2:周三, 3:周四, 4:周五, 5:周六, 6:周日
    hour = now.hour
    # 周三、周五 18-23点
    if day in [2, 4] and 18 <= hour <= 23:
        return True
    # 周六 7-23点
    if day == 5 and 7 <= hour <= 23:
        return True
    return False

# 在界面初始化时禁用保存按钮
save_btn = None

def save_password():
    pwd = entry_pwd.get()
    if not pwd:
        messagebox.showwarning("提示", "请输入密码")
        return
    key = load_key()
    encrypted = encrypt_password(pwd, key)
    with open(PASSWORD_FILE, "w") as f:
        f.write(encrypted)
    messagebox.showinfo("成功", "密码已加密保存")
    # 保存后再次禁用保存按钮，防止重复保存
    save_btn.config(state=tk.DISABLED)
    # 清空输入框
    entry_pwd.delete(0, tk.END)

def view_password():
    if not os.path.exists(PASSWORD_FILE):
        messagebox.showwarning("提示", "还没有保存密码")
        return
    if not can_view_password():
        messagebox.showerror("禁止", "只能在指定时间段查看密码")
        return
    key = load_key()
    with open(PASSWORD_FILE, "r") as f:
        encrypted = f.read()
    try:
        pwd = decrypt_password(encrypted, key)
        messagebox.showinfo("密码", f"您的密码是：{pwd}")
        # 查看密码成功后，启用保存按钮
        save_btn.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("错误", f"解密失败：{e}")

root = tk.Tk()
root.title("密码管理器")
root.geometry("300x180")

tk.Label(root, text="输入密码：").pack(pady=10)
entry_pwd = tk.Entry(root, show="*")
entry_pwd.pack()

# 初始化界面时，根据密码文件是否存在决定保存按钮状态
save_btn = tk.Button(root, text="保存密码", command=save_password, state=tk.NORMAL if not os.path.exists(PASSWORD_FILE) else tk.DISABLED)
save_btn.pack(pady=10)
tk.Button(root, text="查看密码", command=view_password).pack(pady=10)

root.mainloop() 