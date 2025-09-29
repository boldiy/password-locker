# 密码管理器

一个简单的密码管理工具，使用Python和tkinter开发。

## 功能特点

- 密码加密存储
- 基于时间限制的密码查看功能
- 简洁的图形界面
- 安全的加密算法

## 安装说明

1. 确保已安装Python 3.6或更高版本
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行程序：
```bash
python main.py
```

2. 或直接运行打包后的exe文件（在dist目录下）

## 时间限制

- 周三、周五：18:00-23:00
- 周六：7:00-23:00

## 注意事项

- 请妥善保管生成的key.bin文件
- 程序需要网络连接以获取准确时间
- 密码文件(password.txt)和密钥文件(key.bin)请妥善保管 

## 打包为 Windows 可执行文件 (exe)

如果你想把程序打包成单文件的 Windows 可执行程序，可以使用 PyInstaller。下面是在 Windows 上的示例步骤：

1. 安装 PyInstaller（若尚未安装）：
```powershell
pip install pyinstaller
```

2. 在项目根目录运行下面的命令来生成单文件 GUI exe，并把 `key.bin` 一并打包到可执行文件中（注意 `--add-data` 在 Windows 上使用分号分隔目标路径）：
```powershell
C:/Python/python.exe -m PyInstaller --onefile --windowed --add-data "key.bin;." --icon icon.ico main.py
```

3. 打包完成后，生成的可执行文件位于 `dist` 目录中（例如 `dist/main.exe`）。

注意：如果你的 Python 可执行路径不同，请将命令中的 `C:/Python/python.exe` 替换为对应的 Python 可执行路径，或者直接使用 `pyinstaller` 命令（若其已在 PATH 中）。