# 导入模块（同上，省略重复部分）
import os
import sys
import traceback
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QUrl, QTimer, QThread, Signal
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader
from pathlib import Path
import requests
import zipfile
import win32com.client
import threading
import shutil
import concurrent.futures
from functools import partial
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class InstallThread(QThread):
    # 自定义信号：用于在主线程更新进度和日志（避免线程安全问题）
    update_progress_signal = Signal(int, str)
    log_signal = Signal(str)
    install_complete_signal = Signal(bool)  # 安装完成信号（True=成功，False=失败）

    def __init__(self, install_zip):
        super().__init__()
        self.install_zip = install_zip
        self.install_dir = "C:\\Program Files (x86)\\xtgjx"
        self.kjzqd_checked = False  # 后续从主线程传入开机自启动状态

    def set_kjzqd(self, checked):
        self.kjzqd_checked = checked

    def log(self, message):
        self.log_signal.emit(message)

    def run(self):
        try:
            # 第一步：读取安装文件（立即发送进度更新，覆盖初始状态）
            self.log("开始读取本地安装文件...")
            self.update_progress_signal.emit(5, "准备安装文件...")

            # 解压文件
            self.log("开始解压文件...")
            with zipfile.ZipFile(self.install_zip, "r") as zip_ref:
                file_list = zip_ref.namelist()
                self.log(f"发现 {len(file_list)} 个文件")
                for file in file_list:
                    if not file.endswith('/'):
                        try:
                            zip_ref.extract(file, "web")
                            self.log(f"解压文件: {file}")
                        except Exception as e:
                            self.log(f"解压文件 {file} 失败: {str(e)}")

            self.update_progress_signal.emit(20, "验证安装文件...")

            # 检查解压结果
            if not os.path.exists("web"):
                raise Exception("解压安装文件失败")

            # 获取所有待复制文件
            all_files = []
            for root, dirs, files in os.walk("web"):
                for file in files:
                    all_files.append(os.path.join(root, file))

            required_files = ["main.exe", "uninstall.exe"]
            missing_files = [f for f in required_files if not any(f in path for path in all_files)]
            if missing_files:
                raise Exception(f"安装包中缺少必要文件: {', '.join(missing_files)}")

            # 按文件大小计算复制进度（修复核心）
            files_to_copy = []
            for file_path in all_files:
                rel_path = os.path.relpath(file_path, "web")
                dst_path = os.path.join(self.install_dir, rel_path)
                files_to_copy.append((file_path, dst_path))

            # 计算总大小
            total_size = 0
            for src, _ in files_to_copy:
                total_size += os.path.getsize(src)
            copied_size = 0

            self.update_progress_signal.emit(30, "安装应用程序...")

            # 创建目录
            for src, dst in files_to_copy:
                dst_dir = os.path.dirname(dst)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)

            # 复制文件（按大小更新进度）
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_file = {
                    executor.submit(shutil.copy2, src, dst): (src, dst)
                    for src, dst in files_to_copy
                }
                for future in concurrent.futures.as_completed(future_to_file):
                    src, dst = future_to_file[future]
                    try:
                        future.result()
                        self.log(f"复制文件: {src} -> {dst}")
                        # 更新已复制大小和进度
                        file_size = os.path.getsize(src)
                        copied_size += file_size
                        if total_size > 0:
                            progress = 30 + int(40 * (copied_size / total_size))
                            self.update_progress_signal.emit(progress, f"安装中: {os.path.basename(src)}")
                    except Exception as e:
                        self.log(f"复制文件失败 {src}: {str(e)}")
                        raise

            self.update_progress_signal.emit(70, "配置应用程序...")

            # 注册表操作
            self.log("创建注册表项...")
            import winreg
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\xtgjx")
                winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "系统工具箱")
                winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, os.path.join(self.install_dir, "main.exe"))
                winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, os.path.join(self.install_dir, "uninstall.exe"))
                winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0")
                winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "komoni")
                winreg.CloseKey(key)
            except Exception as e:
                self.log(f"创建注册表项时出错: {str(e)}")

            # 开机自启动
            if self.kjzqd_checked:
                self.log("设置开机自启动...")
                try:
                    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
                    winreg.SetValueEx(key, "xtgjx", 0, winreg.REG_SZ, os.path.join(self.install_dir, "main.exe"))
                    winreg.CloseKey(key)
                except Exception as e:
                    self.log(f"设置开机自启动时出错: {str(e)}")

            # 桌面快捷方式
            self.log("创建桌面快捷方式...")
            try:
                desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
                shortcut_path = os.path.join(desktop, "系统工具箱.lnk")
                target = os.path.join(self.install_dir, "main.exe")
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.TargetPath = target
                shortcut.WorkingDirectory = os.path.dirname(target)
                shortcut.IconLocation = target
                shortcut.save()
            except Exception as e:
                self.log(f"创建桌面快捷方式时出错: {str(e)}")

            self.update_progress_signal.emit(90, "清理临时文件...")

            # 清理临时目录
            self.log("清理临时目录...")
            try:
                shutil.rmtree("web", ignore_errors=True)
            except Exception as e:
                self.log(f"清理临时目录时出错: {str(e)}")

            self.update_progress_signal.emit(100, "安装完成!")
            self.log("安装成功!")
            self.install_complete_signal.emit(True)

            # 启动应用
            try:
                os.startfile(os.path.join(self.install_dir, "main.exe"))
            except Exception as e:
                self.log(f"启动应用程序时出错: {str(e)}")

        except Exception as e:
            self.log(f"安装错误: {str(e)}")
            self.log(traceback.format_exc())
            self.update_progress_signal.emit(0, "安装失败")
            self.install_complete_signal.emit(False)


class start:
    def __init__(self):
        current_dir = Path(__file__).parent
        ui_file = current_dir / "install.ui"
        loader = QUiLoader()
        if not ui_file.exists():
            QMessageBox.critical(None, "错误", f"找不到UI文件: {ui_file}")
            exit(1)
        
        self.install_zip = current_dir / "install.zip"
        if not self.install_zip.exists():
            QMessageBox.critical(None, "错误", f"找不到安装文件: {self.install_zip}")
            exit(1)
            
        self.window = loader.load(ui_file, None)
        self.window.setAttribute(Qt.WA_DeleteOnClose)
        
        pixmap = QtGui.QPixmap(resource_path("icon.ico"))
        if pixmap.isNull():
            QMessageBox.critical(None, "错误", "找不到图标文件: icon.ico")
            exit(1)
        self.window.label.setPixmap(pixmap)
        self.window.show()
        self.window.setWindowTitle("系统工具箱安装程序")
        self.window.setWindowIcon(QtGui.QIcon(resource_path("icon.ico")))
        self.window.install.clicked.connect(self.install)
        self.window.install_bar.setRange(0, 100)
        self.window.install_bar.setValue(0)
        
        # 初始化安装线程
        self.install_thread = None

    def update_progress(self, value, message):
        """在主线程更新进度（通过信号槽确保线程安全）"""
        self.window.install_bar.setValue(value)
        self.window.label_3.setText(message)
        self.window.label_3.setAlignment(Qt.AlignCenter)
        self.window.label_3.setStyleSheet("color: green; font-size: 16px;")
        self.window.label_3.setWordWrap(True)
        # 强制刷新UI
        self.window.update()
        QApplication.processEvents()

    def log(self, message):
        """记录日志（主线程执行）"""
        log_file = "install_log.txt"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')}] {message}\n")

    def on_install_complete(self, success):
        """安装完成回调（主线程执行）"""
        if success:
            QMessageBox.information(self.window, "安装完成", "系统工具箱安装完成！")
            self.window.close()
        else:
            QMessageBox.critical(self.window, "安装失败", "安装过程中出现错误，请查看日志。")
        # 恢复按钮状态
        self.window.install.setEnabled(True)
        self.window.install.setText("重新安装")
        self.window.install.setStyleSheet("background-color: #4CAF50; color: white;")
        self.window.install.setCursor(QtCore.Qt.ArrowCursor)

    def install(self):
        if not (self.window.one.isChecked() and self.window.two.isChecked()):
            QMessageBox.warning(self.window, "警告", "请同意用户协议和隐私协议。")
            return
        
        # 禁用安装按钮
        self.window.install.setEnabled(False)
        self.window.install.setText("安装中...")
        self.window.install.setStyleSheet("background-color: gray; color: white;")
        self.window.install.setCursor(QtCore.Qt.WaitCursor)
        
        # 初始化并启动安装线程（使用QThread替代普通线程，确保信号槽可靠）
        self.install_thread = InstallThread(self.install_zip)
        self.install_thread.set_kjzqd(self.window.kjzqd.isChecked())
        # 绑定信号到主线程方法
        self.install_thread.update_progress_signal.connect(self.update_progress)
        self.install_thread.log_signal.connect(self.log)
        self.install_thread.install_complete_signal.connect(self.on_install_complete)
        # 启动线程
        self.install_thread.start()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    try:
        start_window = start()
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "错误", f"程序启动失败:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()