#导入模块
import os
import sys
import traceback
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QUrl
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader
from pathlib import Path
import requests
import zipfile
import win32com.client
import threading
import shutil

def resource_path(relative_path):
    """获取资源文件路径，兼容 PyInstaller 打包"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

#导入main.ui文件

class start:
    def __init__(self):
        current_dir = Path(__file__).parent
        ui_file = current_dir / "install.ui"
        loader = QUiLoader()
        if not ui_file.exists():
            QMessageBox.critical(None, "错误", f"找不到UI文件: {ui_file}")
            exit(1)
        self.window = loader.load(ui_file, None)
        pixmap = QtGui.QPixmap(resource_path("icon.ico"))
        if pixmap.isNull():
            QMessageBox.critical(None, "错误", "找不到图标文件: icon.ico")
            exit(1)
        self.window.label.setPixmap(pixmap)
        self.window.show()
        self.window.setWindowTitle("系统工具箱安装程序")
        self.window.setWindowIcon(QtGui.QIcon(resource_path("icon.ico")))
        self.window.install.clicked.connect(self.install)
        #设置install_bar进度条的value范围为0
        self.window.install_bar.setRange(0, 100)
        self.window.install_bar.setValue(0)
        
    def install_ps1(self):
        try:
            # 下载web.zip文件
            self.log("开始下载安装文件...")
            web_zipfile = requests.get("https://xtgjx.komoni.xyz/webdownload.txt")
            webdownloadzip = requests.get(web_zipfile.content.decode("utf-8").strip())
            
            # 更新进度条到10%
            self.update_progress(10, "下载中...")
            
            # 保存zip文件
            with open("web.zip", "wb") as f:
                f.write(webdownloadzip.content)
            
            # 解压缩文件
            self.log("开始解压文件...")
            with zipfile.ZipFile("web.zip", "r") as zip_ref:
                zip_ref.extractall("web")
            
            # 删除zip文件
            self.update_progress(20, "清理临时文件...")
            os.remove("web.zip")
            
            # 移动exe文件到安装目录
            self.update_progress(30, "安装应用程序...")
            install_dir = "C:\\Program Files (x86)\\xtgjx"
            
            # 确保安装目录存在
            if not os.path.exists(install_dir):
                os.makedirs(install_dir)
            
            # 获取所有文件
            exe_files = [f for f in os.listdir("web") if f.endswith(".exe")]
            if not exe_files:
                raise Exception("未找到可执行文件(.exe)")
            
            # 移动每个exe文件并更新进度
            file_count = len(exe_files)
            for i, file in enumerate(exe_files):
                src = os.path.join("web", file)
                dst = os.path.join(install_dir, file)
                shutil.move(src, dst)
                progress = 30 + int(20 * (i + 1) / file_count)
                self.update_progress(progress, f"安装文件: {file}")
            
            # 清理web目录
            self.log("清理临时目录...")
            shutil.rmtree("web", ignore_errors=True)
            self.update_progress(50, "配置应用程序...")
            
            # 创建注册表项
            self.log("创建注册表项...")
            
            
            # 使用更安全的方式创建注册表项
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Uninstall\xtgjx")
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "系统工具箱")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, os.path.join(install_dir, "xtgjx.exe"))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, os.path.join(install_dir, "uninstall.exe"))
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "komoni")
            winreg.SetValueEx(key, "URLInfoAbout", 0, winreg.REG_SZ, "https://xtgjx.komoni.xyz")
            winreg.SetValueEx(key, "HelpLink", 0, winreg.REG_SZ, "https://xtgjx.komoni.xyz")
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRemove", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            
            self.update_progress(70, "配置系统设置...")
            
            # 判断是否勾选开机自启动
            if self.window.kjzqd.isChecked():
                self.log("设置开机自启动...")
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                      r"Software\Microsoft\Windows\CurrentVersion\Run")
                winreg.SetValueEx(key, "xtgjx", 0, winreg.REG_SZ, os.path.join(install_dir, "xtgjx.exe"))
                winreg.CloseKey(key)
            
            # 创建桌面快捷方式
            self.log("创建桌面快捷方式...")
            desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            shortcut_path = os.path.join(desktop, "系统工具箱.lnk")
            target = os.path.join(install_dir, "main.exe")
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = target
            shortcut.WorkingDirectory = os.path.dirname(target)
            shortcut.IconLocation = target
            shortcut.save()
            
            self.update_progress(99, "完成最后设置...")
            
            # 安装完成
            self.update_progress(100, "安装完成!")
            self.log("安装成功!")
            QMessageBox.information(self.window, "安装完成", "系统工具箱安装完成！")
            
            # 关闭安装窗口
            self.window.close()
            
            # 启动应用程序
            self.log("启动应用程序...")
            os.startfile(target)
            
        except Exception as e:
            # 错误处理
            self.log(f"安装错误: {str(e)}")
            self.log(traceback.format_exc())  # 记录详细的错误堆栈
            self.update_progress(0, "安装失败")
            self.window.label_3.setText(f"安装失败: {str(e)}")
            self.window.label_3.setStyleSheet("color: red; font-size: 16px;")
            QMessageBox.critical(self.window, "安装错误", f"安装过程中出现错误:\n{str(e)}\n\n请查看日志获取更多信息。")
            
            # 恢复按钮状态
            self.window.install.setEnabled(True)
            self.window.install.setText("重新安装")
            self.window.install.setStyleSheet("background-color: #4CAF50; color: white;")
            self.window.install.setCursor(QtCore.Qt.ArrowCursor)
    
    def update_progress(self, value, message):
        """更新进度条和状态消息"""
        self.window.install_bar.setValue(value)
        self.window.label_3.setText(message)
        self.window.label_3.setAlignment(Qt.AlignCenter)
        self.window.label_3.setStyleSheet("color: green; font-size: 16px;")
        self.window.label_3.setWordWrap(True)
    
    def log(self, message):
        """记录安装日志"""
        log_file = "install_log.txt"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')}] {message}\n")
    
    def install(self):
        # 检查是否同意用户协议和隐私协议
        if not (self.window.one.isChecked() and self.window.two.isChecked()):
            QMessageBox.warning(self.window, "警告", "请同意用户协议和隐私协议。")
            return
        
        # 开始安装
        self.window.label_3.setText("正在准备安装...")
        self.window.label_3.setAlignment(Qt.AlignCenter)
        self.window.label_3.setStyleSheet("color: green; font-size: 16px;")
        self.window.label_3.setWordWrap(True)
        
        # 清空日志文件
        with open("install_log.txt", "w", encoding="utf-8") as f:
            f.write(f"[{QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')}] 开始安装...\n")
        
        # 在新线程中执行安装过程
        install_thread = threading.Thread(target=self.install_ps1)
        install_thread.start()
        
        # 禁用安装按钮
        self.window.install.setEnabled(False)
        self.window.install.setText("安装中...")
        self.window.install.setStyleSheet("background-color: gray; color: white;")
        self.window.install.setCursor(QtCore.Qt.WaitCursor)

def main():
    app = QApplication(sys.argv)
    start_window = start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()