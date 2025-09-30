import tkinter as tk
from tkinter import messagebox
import datetime
import os
import base64
import hashlib
from cryptography.fernet import Fernet
import requests
from time import localtime
import sys
import traceback

SALT_SIZE = 16  # 盐长度

# Store runtime data (password file and key) in a user-writeable folder so
# macOS .app bundles (which may be read-only) or other packaging don't block writes.
HOME = os.path.expanduser('~')
# Use a hidden folder in the user's home directory
DATA_DIR = os.path.join(HOME, '.password_locker')
os.makedirs(DATA_DIR, exist_ok=True)
PASSWORD_FILE = os.path.join(DATA_DIR, 'password.txt')
KEY_FILE = os.path.join(DATA_DIR, 'key.bin')

# Diagnostic log path (in user's home) to capture events when the app is launched from Finder
DIAG_LOG = os.path.join(HOME, 'pw_app.log')


def diag_log(msg):
    try:
        with open(DIAG_LOG, 'a', encoding='utf-8') as lf:
            lf.write(msg + '\n')
    except Exception:
        pass


def write_startup_info():
    try:
        diag_log('--- app startup ---')
        diag_log(f'time: {datetime.datetime.now().isoformat()}')
        diag_log(f'user: {os.environ.get("USER")}, home: {HOME}')
        diag_log(f'cwd: {os.getcwd()}')
        diag_log(f'sys.executable: {sys.executable}')
        diag_log(f'sys.argv: {sys.argv}')
        diag_log(f'frozen: {getattr(sys, "frozen", False)}')
        if getattr(sys, 'frozen', False):
            diag_log(f'_MEIPASS: {getattr(sys, "_MEIPASS", None)}')
        # DATA_DIR info
        try:
            st = os.stat(DATA_DIR)
            diag_log(f'DATA_DIR exists: {DATA_DIR} mode: {oct(st.st_mode)} uid: {st.st_uid} gid: {st.st_gid}')
        except Exception as e:
            diag_log(f'DATA_DIR stat failed: {e}')
        diag_log('--- end startup ---')
    except Exception:
        pass

# 生成密钥并保存
def generate_key():
    key = Fernet.generate_key()
    try:
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    except Exception as e:
        # If writing fails, bubble up so caller can show a message
        raise
    return key

# 读取密钥
def load_key():
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(KEY_FILE):
        return generate_key()
    try:
        with open(KEY_FILE, "rb") as f:
            return f.read()
    except Exception:
        # If reading fails, attempt to regenerate the key (avoid crashing)
        return generate_key()

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
    # 如果已有密码文件，询问是否覆盖
    if os.path.exists(PASSWORD_FILE):
        if not messagebox.askyesno("覆盖确认", "已存在密码，是否覆盖？"):
            return
    try:
        diag_log(f"save_password: attempt at {datetime.datetime.now().isoformat()}")
        key = load_key()
        encrypted = encrypt_password(pwd, key)
        # Ensure directory exists and write the password file
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PASSWORD_FILE, "w") as f:
            f.write(encrypted)
        messagebox.showinfo("成功", f"密码已加密保存到：{PASSWORD_FILE}")
        # 清空输入框
        entry_pwd.delete(0, tk.END)
        diag_log(f"save_password: success, wrote {len(encrypted)} bytes to {PASSWORD_FILE}")
    except Exception as e:
        diag_log(f"save_password: exception: {e}")
        diag_log(traceback.format_exc())
        messagebox.showerror("写入失败", f"无法保存密码：{e}")

def view_password():
    if not os.path.exists(PASSWORD_FILE):
        messagebox.showwarning("提示", "还没有保存密码")
        return
    if not can_view_password():
        messagebox.showerror("禁止", "只能在指定时间段查看密码")
        return
    try:
        key = load_key()
        with open(PASSWORD_FILE, "r") as f:
            encrypted = f.read()
        pwd = decrypt_password(encrypted, key)
        # 尝试将密码复制到剪贴板（并在提示中注明）
        copied = False
        try:
            root.clipboard_clear()
            root.clipboard_append(pwd)
            root.update()  # 将剪贴板内容刷新到系统
            copied = True
        except Exception:
            copied = False

        msg = f"您的密码是：{pwd}"
        if copied:
            msg += "\n\n（已复制到剪贴板）"
        messagebox.showinfo("密码", msg)
        # 查看密码成功后，启用保存按钮
        save_btn.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("错误", f"解密或读取失败：{e}")

root = tk.Tk()
root.title("密码管理器")
root.geometry("300x180")

# 尝试设置窗口图标（支持 PyInstaller onefile，使用 sys._MEIPASS 查找打包时的资源）
try:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath('.')
    icon_path = os.path.join(base_path, 'icon.ico')
    if os.path.exists(icon_path):
        # Windows 下使用 .ico
        root.iconbitmap(icon_path)
except Exception:
    pass

tk.Label(root, text="输入密码：").pack(pady=10)
entry_pwd = tk.Entry(root, show="*")
entry_pwd.pack()

# 初始化界面时，总是允许保存（允许在任意时间保存新密码）
save_btn = tk.Button(root, text="保存密码", command=save_password, state=tk.NORMAL)
save_btn.pack(pady=10)
tk.Button(root, text="查看密码", command=view_password).pack(pady=10)

root.mainloop() 