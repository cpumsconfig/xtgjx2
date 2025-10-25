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
import shutil
import json
import subprocess
import tempfile

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
            if len(lines) >= 3:  # 确保有3行内容
                yesnozip = bool(int(lines[0].strip()))
                developers = bool(int(lines[1].strip()))
                run_as_system = bool(int(lines[2].strip()))
            else:
                logging.error("设置文件格式错误，使用默认值")
                yesnozip = False
                developers = False
                run_as_system = False
        # 设置checkbox状态
        self.settingwindow.yesnozip.setChecked(yesnozip)
        self.settingwindow.developers.setChecked(developers)
        self.settingwindow.check_run_system.setChecked(run_as_system)
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
            run_as_system = self.settingwindow.check_run_system.isChecked()
            # 获取当前路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 获取当前路径下的setting.txt文件
            setting_file = "setting.txt"
            # 打开文件
            with open(setting_file, 'w') as f:
                # 写入yesnozip和developers的checkbox状态
                f.write(f"{int(yesnozip)}\n")
                f.write(f"{int(developers)}\n")
                f.write(f"{int(run_as_system)}\n")
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
    def __init__(self, yesnozip, developers, run_as_system):
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
        # 保存运行系统权限设置
        self.run_as_system = run_as_system
        
        # 开发者选项警告
        if developers:
            QMessageBox.warning(None, "警告", "开发者选项已启用，请谨慎使用！")

        # 压缩包选项处理
        if yesnozip:
            QMessageBox.warning(None, "警告", "请谨慎安装不明来源的模块，否则可能会导致系统崩溃！")
            self.window.zipfile.setEnabled(True)
        else:
            self.window.zipfile.setEnabled(False)
            logging.info("压缩包选项未选中，禁用压缩包按钮")

        # 连接按钮事件
        self.window.qexit.clicked.connect(self.close)
        self.window.setting.clicked.connect(self.open_setting_window)
        self.window.settings.clicked.connect(self.show_not_implemented)
        self.window.jhwindows.clicked.connect(self.activate_windows)
        self.window.official_zipfile.clicked.connect(self.official_zipfile)
        self.window.zipfile.clicked.connect(self.import_module)  # 修复：连接到新方法
        self.window.totp_start.clicked.connect(self.totp)
        self.window.run.clicked.connect(self.run_command)  # 修复：连接到新方法
        self.window.weather.clicked.connect(self.show_weather)
        #修改log_test的文字
        self.window.log_test.setText("准备就绪")


    def close(self):
        self.window.log_test.setText("正在关闭程序")
        logging.info("程序已关闭")
        # 关闭窗口
        self.window.close()
        sys.exit(0)
    
    def run_command(self):
        """执行命令按钮处理"""
        run_bas = self.window.run_bas.toPlainText()
        if run_bas == "":
            self.window.log_test.setText("请输入要执行的命令")
            QMessageBox.warning(self.window, "警告", "请输入要执行的命令")
            return
            
        try:
            if self.run_as_system:
                # 使用管理员权限运行
                subprocess.run(f'start bin\pstool\psexec.exe -i -s cmd /c "{run_bas}"', check=True, shell=True)
            else:
                subprocess.run(run_bas, shell=True)
        except Exception as e:
            logging.error(f"运行代码时出错: {str(e)}")
            QMessageBox.critical(self.window, "错误", f"运行代码时出错: {str(e)}")

    def totp(self):
        totp_thread = threading.Thread(target=self.totp_thread)
        totp_thread.start()

    def totp_thread(self):
        try:
            os.system("start bin/totp/totp.exe")
        except Exception as e:
            self.window.log_test.setText("启动TOTP失败")
            logging.error(f"启动TOTP失败: {str(e)}")
            QMessageBox.critical(self.window, "错误", f"启动TOTP失败: {str(e)}")
    def show_weather_thread(self):
        try:
            os.system("start bin/weather/weathers.exe")
        except Exception as e:
            self.window.log_test.setText("启动天气失败")
            logging.error(f"启动天气失败: {str(e)}")
            QMessageBox.critical(self.window, "错误", f"启动天气失败: {str(e)}")
    def show_weather(self):
        weather_thread = threading.Thread(target=self.show_weather_thread)
        weather_thread.start()
    def open_setting_window(self):
        try:
            logging.info("尝试打开设置窗口")

            def show_setting_window():
                if self.setting_window and hasattr(self.setting_window, 'settingwindow'):
                    self.setting_window.settingwindow.show()
                    self.setting_window.settingwindow.raise_()
                    self.setting_window.settingwindow.activateWindow()
                    return

                # 创建新的设置窗口
                self.setting_window = SettingWindow()

                # 显示设置窗口
                if hasattr(self.setting_window, 'show'):
                    self.setting_window.show()
                elif hasattr(self.setting_window, 'settingwindow'):
                    self.setting_window.settingwindow.show()

                logging.info("设置窗口已打开")

            # 使用 QTimer.singleShot 替代 QMetaObject.invokeMethod
            QTimer.singleShot(0, show_setting_window)

        except Exception as e:
            logging.error(f"打开设置窗口时出错: {str(e)}")
            QMessageBox.critical(None, "错误", f"无法打开设置窗口: {str(e)}")

    def activate_windows(self):
        def thread_func():
            # 激活windows
            self.window.log_test.setText("正在激活Windows")
            os.system("slmgr /ipk 6F4BB-YCB3T-2QFXY-9Y8QG-2PR2R")
            self.window.log_test.setText("激活密钥已安装")
            logging.info("激活密钥已安装")
            os.system("slmgr /skms kms8.msguides.com")
            self.window.log_test.setText("KMS服务器已设置")
            logging.info("KMS服务器已设置")
            os.system("slmgr /ato")
            self.window.log_test.setText("Windows已激活")
            logging.info("Windows已激活")
            # 检查激活状态
            result = os.popen("slmgr /xpr").read()
            logging.info(f"激活状态: {result}")
            # 在主线程中弹出消息框
            QTimer.singleShot(0, lambda: QMessageBox.information(None, "激活", f"Windows 激活成功！\n{result}"))

        thread = threading.Thread(target=thread_func)
        thread.start()

    def import_module(self):
        """导入模块文件功能（修复后的实现）"""
        try:
            self.window.log_test.setText("请选择模块文件")
            # 获取文件路径
            file_path, _ = QFileDialog.getOpenFileName(
                self.window,
                "选择模块文件",
                "",
                "ZIP Files (*.zip)"
            )
            
            if not file_path:
                self.window.log_test.setText("用户取消了文件选择")
                logging.info("用户取消了文件选择")
                return
            
            logging.info(f"用户选择了模块文件: {file_path}")
            self.window.log_test.setText("正在导入模块文件")
            # 创建临时目录
            temp_dir = os.path.join(tempfile.gettempdir(), "module_temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 解压ZIP文件
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 检查about.m文件是否存在
            about_path = os.path.join(temp_dir, "about.m")
            if not os.path.exists(about_path):
                raise FileNotFoundError("about.m文件不存在")
                self.window.log_test.setText("该模块文件无效！")
            
            # 读取about.m文件
            with open(about_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 解析模块信息
            version_module = re.search(r"version\s*=\s*'(.+?)'", content).group(1)
            id_module = re.search(r"id\s*=\s*'(.+?)'", content).group(1)
            name_module = re.search(r"name\s*=\s*'(.+?)'", content).group(1)
            
            # 可选字段处理
            try:
                author_module = re.search(r"author\s*=\s*'(.+?)'", content).group(1)
            except:
                author_module = "未知"
            
            try:
                introduce_module = re.search(r"introduce\s*=\s*'(.+?)'", content).group(1)
            except:
                introduce_module = "无介绍"
            
            try:
                address_web_module = re.search(r"address_web\s*=\s*'(.+?)'", content).group(1)
            except:
                address_web_module = "无网站"
            
            try:
                code_module = re.search(r"code\s*=\s*'(.+?)'", content).group(1)
            except:
                code_module = "python"
            
            # 显示确认对话框
            reply = QMessageBox.question(
                self.window, 
                '确认安装',
                f'是否安装以下模块?\n\n名称: {name_module}\n版本: {version_module}\n作者: {author_module}\n\n简介: {introduce_module}',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 创建模块目录
                module_dir = os.path.join("data", id_module)
                if os.path.exists(module_dir):
                    shutil.rmtree(module_dir)
                os.makedirs(module_dir)
                
                # 复制文件
                for item in os.listdir(temp_dir):
                    s = os.path.join(temp_dir, item)
                    d = os.path.join(module_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
                
                # 更新模块清单
                modules_file = "modules.json"
                if os.path.exists(modules_file):
                    with open(modules_file, "r", encoding="utf-8") as f:
                        modules = json.load(f)
                else:
                    modules = []
                
                # 检查是否已存在相同ID的模块
                for i, module in enumerate(modules):
                    if module.get("id") == id_module:
                        modules[i] = {
                            "id": id_module,
                            "name": name_module,
                            "version": version_module,
                            "author": author_module,
                            "introduce": introduce_module,
                            "address_web": address_web_module,
                            "code": code_module
                        }
                        break
                else:
                    # 添加新模块
                    modules.append({
                        "id": id_module,
                        "name": name_module,
                        "version": version_module,
                        "author": author_module,
                        "introduce": introduce_module,
                        "address_web": address_web_module,
                        "code": code_module
                    })
                
                with open(modules_file, "w", encoding="utf-8") as f:
                    json.dump(modules, f, ensure_ascii=False, indent=4)
                
                # 更新UI显示
                self.window.version.setText(f"版本: {version_module}")
                self.window.name.setText(f"名称: {name_module}")
                
                QMessageBox.information(self.window, '成功', '模块安装完成!')
                logging.info(f"模块安装成功: {name_module} v{version_module}")
            else:
                QMessageBox.information(self.window, '取消', '安装已取消')
                logging.info("用户取消了模块安装")
        
        except Exception as e:
            logging.error(f"模块安装失败: {str(e)}", exc_info=True)
            QMessageBox.critical(self.window, "错误", f"模块安装失败: {str(e)}")
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logging.error(f"清理临时文件失败: {str(e)}")

    def uninstall(self):
        #获取id
        id_module = self.window.id.text()
        #获取name
        name_module = self.window.name.text()
        #弹出确认框
        reply = QMessageBox.question(self.window, '提示', '确定卸载该模块吗？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        #如果确认
        if reply == QMessageBox.Yes:
            #删除文件夹
            shutil.rmtree("data\\"+id_module)
            #打开文件modules.json文件
            with open("modules.json", "r", encoding="utf-8") as f:
                #往data里面写入信息
                data = json.load(f)
                #删除data里面的信息
                data = [i for i in data if i["id"] != id_module]
            with open("modules.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            #弹出卸载成功
            QMessageBox.information(self.window, '提示', '卸载成功！')
        else:
            #弹出卸载取消
            QMessageBox.information(self.window, '提示', '卸载取消！')


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
    
    def show_not_implemented(self):
        """参数按钮功能（暂未实现）"""
        QMessageBox.information(self.window, "提示", "参数设置功能正在开发中，敬请期待！")

    def module_func(self):
        # 获取所有的模块，并显示在主窗口的模块页面
        modules = self.get_modules()
        for module in modules:
            self.window.module_list.addItem(module)
            #假如什么都没有，就显示“暂无模块”
        if len(modules) == 0:
            self.window.module_list.addItem("暂无模块")
        
    def get_modules(self):
        # 获取所有的模块
        try:
            if os.path.exists("modules.json"):
                with open("modules.json", "r", encoding="utf-8") as f:
                    modules = json.load(f)
                    return modules
            else:
                # 创建初始模块文件
                with open("modules.json", "w", encoding="utf-8") as f:
                    modules = {"data": [], "version": "1.0"}
                    json.dump(modules, f, ensure_ascii=False, indent=4)
                return modules
        except Exception as e:
            logging.error(f"获取模块失败：{str(e)}")
            QMessageBox.critical(None, "错误", f"无法获取模块: {str(e)}")
            return []


def main():
    # 设置日志
    logging.basicConfig(
        filename='log.txt',
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    logging.info("------系统工具箱1.0------ \n        由xiaotbl制作      \n更多信息请访问:\"https://xigjx.komoni.xyz/updata_module\"")
    logging.info("尝试获取setting的设置文件")
    
    # 默认设置值
    yesnozip = False
    developers = False
    run_as_system = False
    
    try:
        if os.path.exists('setting.txt'):
            with open('setting.txt', 'r') as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    yesnozip = bool(int(lines[0].strip()))
                    developers = bool(int(lines[1].strip()))
                    run_as_system = bool(int(lines[2].strip()))
                    logging.info(f"读取设置文件成功: yesnozip={yesnozip}, developers={developers}, run_as_system={run_as_system}")
                else:
                    logging.error("设置文件行数不足，使用默认值并修复文件")
                    # 修复文件内容
                    with open('setting.txt', 'w') as f:
                        f.write("0\n0\n0\n")  # 写入3行默认值
        else:
            # 创建新的设置文件
            logging.error("找不到设置文件，创建新的文件")
            with open('setting.txt', 'w') as f:
                f.write("0\n0\n0\n")  # 写入3行默认值
    except Exception as e:
        logging.error(f"读取设置文件时出错: {str(e)}")
        # 出错时使用默认值
        yesnozip = False
        developers = False
        run_as_system = False
        
    logging.info("程序已启动")
    app = QApplication(sys.argv)
    main_window = MainWindow(yesnozip, developers, run_as_system)
    
    if "--no-tuopan" in sys.argv:
        logging.info("检测到--no-tuopan参数，跳过系统托盘")
        main_window.window.show()
        sys.exit(app.exec())
    else:
        logging.info("尝试运行系统托盘")
        try:
            # 创建系统托盘
            icon = Image.open(resource_path("icon.ico"))
            menu = (
                pystray.MenuItem("显示窗口", lambda icon, item: main_window.window.show()),
                pystray.MenuItem("退出", lambda icon, item: sys.exit(0))
            )
            tray = pystray.Icon("name", icon, "系统工具箱", menu)
            
            # 在单独线程中运行系统托盘
            def run_tray():
                tray.run()
                
            tray_thread = threading.Thread(target=run_tray)
            tray_thread.daemon = True
            tray_thread.start()
            logging.info("系统托盘运行成功")
        except Exception as e:
            logging.error(f"系统托盘运行失败: {str(e)}")
            QMessageBox.critical(None, "错误", "系统托盘运行失败，请检查程序是否正常运行")
        
        # 显示主窗口
        main_window.window.show()
        # 运行应用程序
        logging.info("主窗口已显示")
        sys.exit(app.exec())


if __name__ == "__main__":
    main()