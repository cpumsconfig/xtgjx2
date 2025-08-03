#导入模块
import os
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QUrl
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader
from pathlib import Path
import requests
import zipfile
import win32com.client
import threading
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
        web_zipfile = requests.get("https://xtgjx.komoni.xyz/webdownload.txt")
        webdownloadzip = requests.get(web_zipfile.content.decode("utf-8").strip())
        #设置install_bar进度条的value为10
        self.window.install_bar.setValue(10)
        with open("web.zip", "wb") as f:
            f.write(webdownloadzip.content)
            #解压缩
        with zipfile.ZipFile("web.zip", "r") as zip_ref:
            zip_ref.extractall("web")
            #删除zip文件
        #设置install_bar进度条的value为20
        self.window.install_bar.setValue(20)
        #删除zip文件
        os.remove("web.zip")
        #将所有文件移动到C:\Program Files (x86)\xtgjx目录下
        #设置install_bar进度条的value为30
        self.window.install_bar.setValue(30)
        if not os.path.exists("C:\\Program Files (x86)\\xtgjx"):
             os.makedirs("C:\\Program Files (x86)\\xtgjx")
        for file in os.listdir("web"):
            if file.endswith(".exe"):
                os.rename(os.path.join("web", file), os.path.join("C:\\Program Files (x86)\\xtgjx", file))
        #设置install_bar进度条的value为50
        self.window.install_bar.setValue(50)

            #删除web文件夹
        os.rmdir("web")
            #创建注册表项
        #设置install_bar进度条的value为70
        self.window.install_bar.setValue(70)
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "DisplayName" /t REG_SZ /d "系统工具箱" /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "DisplayIcon" /t REG_SZ /d "C:\\Program Files (x86)\\xtgjx\\xtgjx.exe" /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "UninstallString" /t REG_SZ /d "C:\\Program Files (x86)\\xtgjx\\uninstall.exe" /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "DisplayVersion" /t REG_SZ /d "1.0" /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "Publisher" /t REG_SZ /d "komoni" /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "URLInfoAbout" /t REG_SZ /d "https://xtgjx.komoni.xyz" /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "HelpLink" /t REG_SZ /d "https://xtgjx.komoni.xyz" /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "NoModify" /t REG_DWORD /d 1 /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "NoRepair" /t REG_DWORD /d 1 /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "NoRemove" /t REG_DWORD /d 1 /f')
        os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\xtgjx" /v "NoModify" /t REG_DWORD /d 1 /f')
            #判断kjzqd是否勾选，勾选则往注册表添加开机自启动
        #设置install_bar进度条的value为99
        self.window.install_bar.setValue(99)
        if self.window.kjzqd.isChecked():
            os.system('reg add "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "xtgjx" /t REG_SZ /d "C:\\Program Files (x86)\\xtgjx\\main.exe" /f')
            #创建快捷方式
            
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        shortcut_path = os.path.join(desktop, "系统工具箱.lnk")
        target = os.path.join("C:\\Program Files (x86)\\xtgjx", "xtgjx.exe")
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.IconLocation = target
        shortcut.save()
        #设置install_bar进度条的value为100
        self.window.install_bar.setValue(100)

            #提示安装完成
        QMessageBox.information(self.window, "安装完成", "系统工具箱安装完成！")
            #退出程序
        self.window.close()
            #运行xtgjx.exe
        os.startfile("C:\\Program Files (x86)\\xtgjx\\xtgjx.exe")
    def install(self):
        #假如没有勾选one和two
        if not (self.window.one.isChecked() and self.window.two.isChecked()):
            QMessageBox.warning(self.window, "警告", "请同意用户协议和隐私协议。")
            return
        #有则安装
        if self.window.one.isChecked() and self.window.two.isChecked():
            self.window.label_3.setText("正在安装，请稍等...")
            self.window.label_3.setAlignment(Qt.AlignCenter)
            self.window.label_3.setStyleSheet("color: green; font-size: 16px;")
            self.window.label_3.setWordWrap(True)
            #调用install_ps1函数
            install_thread = threading.Thread(target=self.install_ps1)
            install_thread.start()
            #禁用按钮
            self.window.install.setEnabled(False)
            self.window.install.setText("安装中...")
            self.window.install.setStyleSheet("background-color: gray; color: white;")
            self.window.install.setCursor(QtCore.Qt.WaitCursor)

            
        #假如只勾选one
        elif self.window.one.isChecked() and not self.window.two.isChecked():
           QMessageBox.warning(self.window, "警告", "请同意用户协议！")
           return

        elif not self.window.one.isChecked() and self.window.two.isChecked():
           QMessageBox.warning(self.window, "警告", "请同意隐私协议！")
           return
        #假如都没有勾选
        elif not self.window.one.isChecked() and not self.window.two.isChecked():
           QMessageBox.warning(self.window, "警告", "请同意用户协议和隐私协议！")
           return
        #假如只勾选kjzqd
        elif self.window.kjzqd.isChecked() and not self.window.one.isChecked() and not self.window.two.isChecked():
            QMessageBox.warning(self.window, "警告", "请同意用户协议和隐私协议！")
            return
        #假如只勾选one和kjzqd
        elif self.window.one.isChecked() and not self.window.two.isChecked() and self.window.kjzqd.isChecked():
            QMessageBox.warning(self.window, "警告", "请同意隐私协议！")
            return
        #假如只勾选two和kjzqd
        elif not self.window.one.isChecked() and self.window.two.isChecked() and self.window.kjzqd.isChecked():
            QMessageBox.warning(self.window, "警告", "请同意用户协议！")
            return
        
def main():
    app = QApplication(sys.argv)
    start_window = start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()