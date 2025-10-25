import os
import tkinter as tk
from tkinter import messagebox
import winreg
import shutil
import stat
import sys
import ctypes
import time
import logging

def setup_logger():
    """配置日志记录"""
    logger = logging.getLogger('uninstaller')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 创建文件日志
    file_handler = logging.FileHandler('uninstall_log.txt')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def is_admin():
    """检查是否具有管理员权限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_file_locked(file_path):
    """检查文件是否被锁定"""
    try:
        with open(file_path, 'a'):
            pass
        return False
    except IOError:
        return True

def force_delete_file(file_path, logger):
    """强制删除文件"""
    try:
        # 确保文件可写
        if os.path.exists(file_path):
            os.chmod(file_path, stat.S_IWRITE)
            # 尝试多次删除
            for attempt in range(3):
                try:
                    os.remove(file_path)
                    logger.info(f"成功删除文件: {file_path}")
                    return True
                except Exception as e:
                    logger.warning(f"删除文件尝试 {attempt+1}: {e}")
                    time.sleep(0.5)
            logger.error(f"无法删除文件: {file_path}")
            return False
    except Exception as e:
        logger.error(f"处理文件时出错: {e}")
        return False

def uninstall():
    logger = setup_logger()
    logger.info("开始卸载过程")
    
    # 目标卸载路径
    target_dir = r"C:\Program Files (x86)\xtgjx"
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\xtgjx"
    errors = []

    # 尝试删除目录内容
    try:
        if os.path.exists(target_dir):
            logger.info(f"开始删除目录内容: {target_dir}")
            for root, dirs, files in os.walk(target_dir, topdown=False):
                # 先删除所有文件
                for file in files:
                    file_path = os.path.join(root, file)
                    if not force_delete_file(file_path, logger):
                        errors.append(f"无法删除文件: {file_path}")
                
                # 再删除所有目录
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        os.rmdir(dir_path)
                        logger.info(f"成功删除目录: {dir_path}")
                    except Exception as e:
                        logger.error(f"无法删除目录: {dir_path}, 错误: {e}")
                        errors.append(f"无法删除目录: {dir_path}")
        else:
            logger.info(f"目标目录不存在: {target_dir}")
    except Exception as e:
        logger.error(f"删除目录内容时出错: {e}")
        errors.append(f"删除目录内容失败: {e}")

    # 删除注册表项
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
        logger.info(f"成功删除注册表项: {reg_path}")
    except FileNotFoundError:
        logger.info(f"注册表项不存在: {reg_path}")
    except Exception as e:
        logger.error(f"删除注册表项失败: {e}")
        errors.append(f"删除注册表项失败: {e}")

    # 延迟删除自身目录
    try:
        if os.path.exists(target_dir):
            bat_path = os.path.join(target_dir, "uninstall.bat")
            with open(bat_path, 'w') as bat_file:
                bat_file.write(f'@echo off\n')
                bat_file.write(f'timeout /t 3 /nobreak > nul\n')  # 延长等待时间
                bat_file.write(f'rmdir /S /Q "{target_dir}"\n')
                bat_file.write(f'del /F /Q "%~f0"\n')  # 删除自身批处理文件
            os.startfile(bat_path)
            logger.info(f"已创建卸载批处理文件: {bat_path}")
    except Exception as e:
        logger.error(f"创建清理脚本失败: {e}")
        errors.append(f"创建清理脚本失败: {e}")

    # 显示卸载结果
    if errors:
        error_msg = "\n".join([f"• {err}" for err in errors[:5]])
        if len(errors) > 5:
            error_msg += "\n• ... 以及其他错误"
        messagebox.showerror("卸载过程中出现错误", 
                            f"卸载过程中遇到以下问题:\n\n{error_msg}\n\n详细信息请查看 uninstall_log.txt")
    else:
        messagebox.showinfo("完成", "卸载成功！系统工具箱已从您的计算机中移除。")
    
    logger.info(f"卸载程序退出，错误数量: {len(errors)}")
    os._exit(0)

if __name__ == "__main__":
    # 检查管理员权限
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    
    # 创建确认对话框
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    if messagebox.askyesno("确认卸载", "确定要卸载系统工具箱吗？此操作将移除所有相关文件和设置。"):
        uninstall()
    else:
        root.destroy()