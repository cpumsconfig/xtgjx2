# 一般用的模块
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QUrl, Signal, QObject, QTimer, QDateTime, QMetaObject
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtUiTools import QUiLoader
import logging
import threading
# 关键模块
import os
import sys
import requests
from pathlib import Path
import json
import configparser
import time

# IP查询API
IP_API_URL = "https://whois.pconline.com.cn/ipJson.jsp?ip=&json=true"

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def resource_path(relative_path):
    """获取资源文件路径，兼容 PyInstaller 打包"""
    logging.info("获取资源文件路径")
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def init_config():
    """初始化配置文件"""
    config_dir = os.path.join(os.path.expanduser('~'), '.weather_app')
    config_file = os.path.join(config_dir, 'config.ini')
    
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    if not os.path.exists(config_file):
        config = configparser.ConfigParser()
        config['DEFAULT'] = {
            'default_city': 'Beijing',
            'update_interval': '30',
            'theme': 'light'
        }
        with open(config_file, 'w') as f:
            config.write(f)
    
    return config_file

class MainWindow(QObject):
    weather_signal = Signal(dict)
    ip_location_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        logging.info("初始化主窗口")
        
        # 初始化配置文件
        self.config_file = init_config()
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
        
        # 获取程序运行目录
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        ui_file = os.path.join(base_path, "main.ui")
        default_img = os.path.join(base_path, "weather", "无.png")
        loader = QUiLoader()
        icon_path = resource_path("icon.ico")
        
        if not os.path.exists(icon_path):
            logging.warning(f"警告: 找不到图标文件 {icon_path}")
        if not os.path.exists(ui_file):
            logging.error(f"找不到主窗口UI文件: {ui_file}")
            QMessageBox.critical(None, "错误", f"主窗口UI文件不存在: {ui_file}")
            sys.exit(1)

        logging.info("主窗口UI文件加载成功")

        # 加载UI文件
        self.window = loader.load(ui_file, None)
        self.window.show()
        self.window.setWindowTitle("天气查询")
        logging.info("主窗口显示成功")

        # 设置默认天气图片
        if os.path.exists(default_img):
            pixmap = QtGui.QPixmap(default_img)
            self.window.labelwe.setPixmap(pixmap)
            self.window.labelwe.setScaledContents(True)
            logging.info(f"成功加载默认天气图片: {default_img}")
        else:
            logging.warning(f"找不到默认天气图片: {default_img}")

        # 设置窗口图标
        icon_path = str(resource_path("icon.ico"))
        self.window.setWindowIcon(QtGui.QIcon(icon_path))
        logging.info(f"主窗口图标设置成功: {icon_path}")

        # 设置默认值
        self.window.qexit.clicked.connect(self.close)
        self.window.update_weather.clicked.connect(self.update_weather)
        self.window.update_ip_weather.clicked.connect(self.update_ip_weather)
        
        # 连接信号
        self.weather_signal.connect(self.show_weather_info)
        self.ip_location_signal.connect(self.handle_ip_location)
        
        # 设置默认城市
        default_city = self.config['DEFAULT'].get('default_city', 'Beijing')
        self.window.city_edit.setPlainText(default_city)
        
        logging.info("主窗口初始化完成")

    def close(self):
        logging.info("用户点击退出按钮")
        # 保存当前配置
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        self.window.close()
        sys.exit()

    def weather(self, city, day, retry=3):
        logging.info(f"开始获取天气信息 - 城市: {city}, 日期: {day}")
        for i in range(retry):
            try:
                city_get = requests.get(
                    "https://komoni.xyz/?key=5byg5LiJIA==&ukey=MTgwMDE0NzE1ODE=&name=weather&scanf="+city+"&day="+day,
                    timeout=5
                )
                city_get = city_get.content.decode("utf-8")
                city_get = json.loads(city_get)
                logging.info(f"成功获取天气信息 - 响应代码: {city_get.get('code')}")
                return city_get
            except requests.RequestException as e:
                if i == retry - 1:
                    logging.error(f"获取天气信息失败（重试{retry}次后）: {str(e)}")
                    return None
                logging.warning(f"获取天气信息失败，正在重试（{i+1}/{retry}）: {str(e)}")
                time.sleep(1)

    def show_weather_info(self, weather_data):
        if weather_data and weather_data.get("code") == 200:
            weather_info = weather_data["weather"]
            logging.info(f"成功显示天气信息 - 城市: {weather_info['city']}, 温度: {weather_info['temperature']}°C")
            
            # 判断当前时间
            current_time = QDateTime.currentDateTime()
            hour = current_time.time().hour()
            time_period = "日间" if 6 <= hour < 18 else "夜间"
            logging.info(f"当前时间段: {time_period}")
            
            # 更新天气状况标签
            weather_text = f"{time_period} {weather_info['description']}"
            self.window.label_wt.setText(weather_text)
            logging.info(f"更新天气状况标签: {weather_text}")
            
            # 更新城市位置标签
            location = f"{weather_info['country']}/{weather_info['city']}"
            self.window.label_ct.setText(location)
            logging.info(f"更新城市位置标签: {location}")
            
            # 设置天气图片
            weather_desc = weather_info['description']
            # 先尝试加载带时间段的图片
            weather_img_path = resource_path(f"weather/{time_period}{weather_desc}.png")
            if os.path.exists(weather_img_path):
                pixmap = QtGui.QPixmap(weather_img_path)
                self.window.labelwe.setPixmap(pixmap)
                self.window.labelwe.setScaledContents(True)
                logging.info(f"成功加载天气图片: {weather_img_path}")
            else:
                # 如果带时间段的图片不存在，尝试加载不带时间段的图片
                weather_img_path = resource_path(f"weather/{weather_desc}.png")
                if os.path.exists(weather_img_path):
                    pixmap = QtGui.QPixmap(weather_img_path)
                    self.window.labelwe.setPixmap(pixmap)
                    self.window.labelwe.setScaledContents(True)
                    logging.info(f"成功加载默认天气图片: {weather_img_path}")
                else:
                    # 如果都不存在，使用默认图片
                    default_img_path = resource_path("weather/无.png")
                    if os.path.exists(default_img_path):
                        pixmap = QtGui.QPixmap(default_img_path)
                        self.window.labelwe.setPixmap(pixmap)
                        self.window.labelwe.setScaledContents(True)
                        logging.info(f"使用默认天气图片: {default_img_path}")
                    else:
                        logging.warning("未找到任何可用图片，清空显示")
                        self.window.labelwe.clear()
            
            info = f"""
城市: {weather_info['city']}
国家: {weather_info['country']}
日期: {weather_info['date']}
温度: {weather_info['temperature']}°C
体感温度: {weather_info['feels_like']}°C
湿度: {weather_info['humidity']}%
气压: {weather_info['pressure']}hPa
天气状况: {weather_info['description']}
风速: {weather_info['wind_speed']}m/s
风向: {weather_info['wind_dir']}
能见度: {weather_info['visibility']}km
紫外线指数: {weather_info['uv_index']}
"""
            QMessageBox.information(self.window, "天气信息", info)
        else:
            logging.warning("显示天气信息失败 - 数据无效或获取失败")
            self.window.label_wt.clear()
            self.window.label_ct.clear()
            default_img_path = resource_path("weather/无.png")
            if os.path.exists(default_img_path):
                pixmap = QtGui.QPixmap(default_img_path)
                self.window.labelwe.setPixmap(pixmap)
                self.window.labelwe.setScaledContents(True)
            else:
                self.window.labelwe.clear()
            QMessageBox.warning(self.window, "错误", "获取天气信息失败，请检查城市名称或稍后重试")

    def get_weather_thread(self, city):
        logging.info(f"在新线程中获取天气信息 - 城市: {city}")
        weather_data = self.weather(city, "1")
        # 使用信号发送数据
        self.weather_signal.emit(weather_data)

    def update_weather(self):
        city = self.window.city_edit.toPlainText()  # 使用toPlainText()替代text()
        logging.info(f"用户点击更新按钮 - 输入城市: {city}")
        
        if not city:
            city = self.config['DEFAULT'].get('default_city', 'Beijing')
            self.window.city_edit.setPlainText(city)
            logging.info(f"城市名为空，使用默认城市: {city}")
        
        # 更新配置文件中的默认城市
        self.config['DEFAULT']['default_city'] = city
        
        logging.info("创建新线程获取天气信息")
        thread = threading.Thread(target=self.get_weather_thread, args=(city,))
        thread.daemon = True  # 设置为守护线程
        thread.start()

    def get_location_by_ip_thread(self):
        """在新线程中获取IP位置"""
        logging.info("在新线程中获取IP位置信息")
        try:
            response = requests.get(IP_API_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and 'city' in data:
                    city = data['city']
                    # 移除城市名中的"市"字
                    city = city.replace('市', '')
                    logging.info(f"成功获取IP位置 - 城市: {city}")
                    self.ip_location_signal.emit(city)
                    return
            logging.warning("获取IP位置失败")
            self.ip_location_signal.emit("")
        except Exception as e:
            logging.error(f"获取IP位置异常: {str(e)}")
            self.ip_location_signal.emit("")

    def handle_ip_location(self, city):
        """处理IP位置结果"""
        if city:
            logging.info(f"获取到IP所在城市: {city}")
            self.window.city_edit.setPlainText(city)
            self.update_weather()
        else:
            logging.warning("无法获取IP位置信息")
            QMessageBox.warning(self.window, "错误", "无法获取当前位置信息，请检查网络连接")

    def update_ip_weather(self):
        """根据IP位置查询天气"""
        logging.info("用户点击IP天气查询按钮")
        thread = threading.Thread(target=self.get_location_by_ip_thread)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    logging.info("程序启动")
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
