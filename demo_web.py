import sys
import os
import webbrowser
import subprocess

def handle_command(cmd):
    """处理xtgjx:协议后的命令"""
    if cmd == "open-app":
        # 示例：打开计算器（替换为你的应用路径）
        subprocess.Popen("calc.exe")
    elif cmd.startswith("open-url="):
        # 示例：打开URL
        url = cmd.split("=", 1)[1]
        webbrowser.open(url)
    else:
        print(f"未知命令: {cmd}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 获取完整协议字符串（如 xtgjx:open-app）
        uri = sys.argv[1]
        # 提取冒号后的命令部分
        command = uri.split(":", 1)[1] if ":" in uri else ""
        handle_command(command)