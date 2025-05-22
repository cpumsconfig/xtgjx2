import pystray
from PIL import Image
import os
import sys
import logging
import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QUrl, Signal, QObject, QTimer, QDateTime, QMetaObject
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader
from pathlib import Path
import requests
import zipfile
import win32com.client
import re
import webbrowser


def resource_path(relative_path):
    """获取资源文件路径，兼容 PyInstaller 打包"""
    logging.info(f"获取资源文件路径: {relative_path}")
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class UpdateChecker(QObject):
    """更新检查器，在单独线程中运行"""
    update_checked = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

    def check_update(self, version):
        try:
            from updata import updata
            result = updata.start(version)
            print(result)
            if result is False:
                logging.info("当前已是最新版本")
            elif result == "demo":
                logging.info("当前版本为测试版本")
            else:
                logging.info("有新版本可用！")
            self.update_checked.emit(result)
        except Exception as e:
            logging.error(f"更新检查失败: {str(e)}")
            self.update_checked.emit(None)


class SettingWindow:
    def __init__(self):
        # 初始化设置窗口
        current_dir = Path(__file__).parent
        ui_file = current_dir / "setting.ui"
        loader = QUiLoader()

        # 调试信息
        logging.info(f"尝试加载设置UI文件: {ui_file}")
        logging.info(f"文件是否存在: {ui_file.exists()}")

        if not ui_file.exists():
            logging.error(f"找不到UI文件: {ui_file}")
            QMessageBox.critical(None, "错误", f"设置窗口UI文件不存在: {ui_file}")
            raise FileNotFoundError(f"UI文件不存在: {ui_file}")

        self.settingwindow = loader.load(ui_file, None)

        if not self.settingwindow:
            logging.error("设置窗口加载失败")
            QMessageBox.critical(None, "错误", "设置窗口加载失败，请检查UI文件格式")
            raise RuntimeError("设置窗口加载失败")

        self.settingwindow.setWindowTitle("设置")

        # 设置窗口图标
        icon_path = str(resource_path("icon.ico"))
        self.settingwindow.setWindowIcon(QtGui.QIcon(icon_path))

        logging.info("设置窗口加载成功")

        # 创建更新检查器
        self.update_checker = UpdateChecker()
        self.update_checker.update_checked.connect(self.on_update_checked)
        # 获取setting.txt文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        setting_file = 'setting.txt'
        # 打开文件
        with open(setting_file, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                yesnozip = bool(int(lines[0].strip()))
                developers = bool(int(lines[1].strip()))
            else:
                logging.error("设置文件格式错误，使用默认值")
                yesnozip = False
                developers = False
        # 设置checkbox状态
        self.settingwindow.yesnozip.setChecked(yesnozip)
        self.settingwindow.developers.setChecked(developers)
        # 在单独线程中检查更新
        thread = threading.Thread(target=self.update_checker.check_update, args=(110000,))
        thread.daemon = True
        thread.start()
        logging.info("更新检查线程已启动")
        self.settingwindow.zp.clicked.connect(self.zp)
        self.settingwindow.save.clicked.connect(self.save)
        # 显示加载状态
        if hasattr(self.settingwindow, 'label'):
            self.settingwindow.label.setText("检查更新中...")

    def on_update_checked(self, result):
        """处理更新检查结果"""
        if hasattr(self.settingwindow, 'label'):
            if result is False:
                logging.info("当前已是最新版本")
                self.settingwindow.label.setText("当前已是最新版本")
            elif result == "demo":
                logging.info("当前版本为测试版本")
                self.settingwindow.label.setText("当前版本为测试版本,请使用测试版")
            else:
                self.settingwindow.label.setText("有新版本可用！")

    def show(self):
        """显示设置窗口"""
        if self.settingwindow:
            self.settingwindow.show()

    def zp(self):
        video_url = "https://www.bilibili.com/video/BV1UT42167xb"
        try:
            webbrowser.open(video_url)
            logging.info(f"已打开视频链接：{video_url}")
        except Exception as e:
            logging.error(f"打开链接失败：{str(e)}")

    def save(self):
        # 保存设置
        try:
            # 获取yesnozip和developers的checkbox状态
            yesnozip = self.settingwindow.yesnozip.isChecked()
            developers = self.settingwindow.developers.isChecked()
            # 获取当前路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 获取当前路径下的setting.txt文件
            setting_file = "setting.txt"
            # 打开文件
            with open(setting_file, 'w') as f:
                # 写入yesnozip和developers的checkbox状态
                f.write(f"{int(yesnozip)}\n")
                f.write(f"{int(developers)}\n")
            logging.info("设置已保存")
            QMessageBox.information(None, "成功", "设置已保存，将会在下次启动时生效")
        except PermissionError:
            logging.error("没有权限保存设置文件")
            QMessageBox.critical(None, "错误", "没有权限保存设置文件，请检查权限")

        except FileNotFoundError:
            logging.error("找不到设置文件")
            QMessageBox.critical(None, "错误", "找不到设置文件，请检查路径")
        except Exception as e:
            logging.error(f"保存设置失败: {str(e)}")
            QMessageBox.critical(None, "错误", f"保存设置失败: {str(e)}")


class MainWindow:
    def __init__(self, yesnozip, developers):
        current_dir = Path(__file__).parent
        ui_file = current_dir / "main.ui"
        loader = QUiLoader()

        if not ui_file.exists():
            logging.error(f"找不到主窗口UI文件: {ui_file}")
            QMessageBox.critical(None, "错误", f"主窗口UI文件不存在: {ui_file}")
            sys.exit(1)

        logging.info("主窗口UI文件加载成功")

        # 加载UI文件
        self.window = loader.load(ui_file, None)
        self.window.show()
        self.window.setWindowTitle("系统工具箱")

        # 设置窗口图标
        icon_path = str(resource_path("icon.ico"))
        self.window.setWindowIcon(QtGui.QIcon(icon_path))

        # 初始化定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每秒更新一次

        # 存储设置窗口引用
        self.setting_window = None
        # 放大窗口按钮禁用
        # self.window.setWindowFlags(self.window.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        if developers:
            # 如果开发者选项被选中，显示开发者按钮
            QMessageBox.warning(None, "警告", "开发者选项已启用，请谨慎使用！")

        elif yesnozip:
            # 如果压缩包选项被选中，显示压缩包按钮
            QMessageBox.warning(None, "警告", "请谨慎安装不明来源的模块，否则可能会导致系统崩溃！")
            self.window.zipfile.setEnabled(True)
        else:
            # 如果压缩包选项未选中，禁用压缩包按钮
            self.window.zipfile.setEnabled(False)
            logging.info("压缩包选项未选中，禁用压缩包按钮")

        # 连接按钮事件
        self.window.qexit.clicked.connect(self.close)
        self.window.setting.clicked.connect(self.open_setting_window)
        self.window.settings.clicked.connect(self.show_not_implemented)
        self.window.jhwindows.clicked.connect(self.activate_windows)
        self.window.official_zipfile.clicked.connect(self.official_zipfile)
        self.window.zipfile.clicked.connect(self.show_not_implemented)

    def close(self):
        logging.info("程序已关闭")
        # 关闭窗口
        self.window.close()
        sys.exit(0)

    def open_setting_window(self):
        try:
            logging.info("尝试打开设置窗口")

            # 如果设置窗口已存在，则显示它
            if self.setting_window and hasattr(self.setting_window, 'settingwindow'):
                self.setting_window.settingwindow.show()
                self.setting_window.settingwindow.raise_()
                return

            # 创建新的设置窗口
            self.setting_window = SettingWindow()

            # 显示设置窗口
            if hasattr(self.setting_window, 'show'):
                self.setting_window.show()
            elif hasattr(self.setting_window, 'settingwindow'):
                self.setting_window.settingwindow.show()

            logging.info("设置窗口已打开")

        except Exception as e:
            logging.error(f"打开设置窗口时出错: {str(e)}")
            QMessageBox.critical(None, "错误", f"无法打开设置窗口: {str(e)}")

    def activate_windows(self):
        def thread_func():
            # 激活windows
            os.system("slmgr /ipk 6F4BB-YCB3T-2QFXY-9Y8QG-2PR2R")
            logging.info("激活密钥已安装")
            os.system("slmgr /skms kms8.msguides.com")
            logging.info("KMS服务器已设置")
            os.system("slmgr /ato")
            logging.info("Windows已激活")
            # 检查激活状态
            result = os.popen("slmgr /xpr").read()
            logging.info(f"激活状态: {result}")
            # 在主线程中弹出消息框
            QMetaObject.invokeMethod(
                self.window,
                lambda: QMessageBox.information(None, "激活", f"Windows 激活成功！\n{result}"),
                Qt.QueuedConnection
            )

        thread = threading.Thread(target=thread_func)
        thread.start()

    def show_not_implemented(self):
        # 弹出未制作窗口
        QMessageBox.information(None, "设置", "该功能尚未制作！")
        logging.info("该功能尚未制作！")

    def update_time(self):
        current_time = QDateTime.currentDateTime().toString("HH:mm:ss")
        current_day = QDateTime.currentDateTime().toString("yyyy-MM-dd")

        # 确保time和day控件存在
        if hasattr(self.window, 'time'):
            self.window.time.setText(current_time)
        if hasattr(self.window, 'day'):
            self.window.day.setText(current_day)

    def official_zipfile(self):
        # 打开官方压缩包下载链接
        url = "https://xtgjx.komoni.xyz/modules"
        try:
            webbrowser.open(url)
            logging.info(f"已打开链接：{url}")
        except Exception as e:
            logging.error(f"打开链接失败：{str(e)}")
            QMessageBox.critical(None, "错误", f"无法打开链接: {str(e)}")


def run(main_window):
    try:
        # 定义托盘图标
        icon = Image.open(resource_path("icon.ico"))
        logging.basicConfig(
            filename='log.txt',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # 定义托盘图标被点击时的响应函数
        def on_click(icon, item):
            logging.info("Icon clicked!")

        def show_main_window(icon, item):
            if main_window and hasattr(main_window, 'window'):
                QTimer.singleShot(0, lambda: main_window.window.show())
                QTimer.singleShot(0, lambda: main_window.window.raise_())

        # 创建一个系统托盘对象
        menu = (
            pystray.MenuItem("显示窗口", lambda icon, item: show_main_window(icon, item)),
            pystray.MenuItem("测试", lambda icon, item: logging.info("测试选中")),
            pystray.MenuItem("Exit", lambda icon, item: icon.stop())
        )

        # 定义 setup 函数，用于在图标启动时执行初始化操作
        def setup(icon):
            icon.visible = True

        # 将托盘图标、菜单和点击响应函数传给系统托盘对象并启动
        pystray.Icon("name", icon, "Title", menu).run(setup)
    except KeyboardInterrupt:
        icon.stop()


def tuopan(main_window):
    # 托盘程序
    try:
        run(main_window)
    except Exception as e:
        logging.error(f"启动托盘程序失败: {str(e)}")
        QMessageBox.critical(None, "错误", f"无法启动托盘程序: {str(e)}")
        sys.exit(1)


def main():
    # 设置日志
    logging.basicConfig(
        filename='log.txt',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("------系统工具箱1.0------ \n        由xiaotbl制作      \n更多信息请访问:\"https://xigjx.komoni.xyz/updata_module\"")
    logging.info("尝试获取setting的设置文件")
    try:
        with open('setting.txt', 'r') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                yesnozip = bool(int(lines[0].strip()))
                developers = bool(int(lines[1].strip()))
                logging.info(f"读取设置文件成功: yesnozip={yesnozip}, developers={developers}")
            else:
                logging.error("设置文件格式错误，使用默认值")
                yesnozip = False
                developers = False
    except FileNotFoundError:
        # 如果文件不存在，创建一个新的文件
        logging.error("找不到设置文件，创建新的文件")
        with open('setting.txt', 'w') as f:
            f.write("0\n0\n")
            logging.info("已创建新的设置文件")
        yesnozip = False
        developers = False
    except Exception as e:
        logging.error(f"读取设置文件时出错: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    logging.info("程序已启动")
    app = QApplication(sys.argv)
    main_window = MainWindow(yesnozip, developers)

    logging.info("尝试启动托盘程序")
    thread_tuopan = threading.Thread(target=tuopan, args=(main_window,))
    thread_tuopan.start()
    logging.info("托盘程序已启动")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()