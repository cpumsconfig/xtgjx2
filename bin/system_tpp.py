import pystray
from PIL import Image
import os
import sys
import logging
import main
def resource_path(relative_path):
    """获取资源文件路径，兼容 PyInstaller 打包"""
    logging.info(f"获取资源文件路径: {relative_path}")
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
def run():
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

        def k(icon, item):
            main()

        # 创建一个系统托盘对象
        menu = (
            pystray.MenuItem("运行", lambda icon, item: k(icon, item)),
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