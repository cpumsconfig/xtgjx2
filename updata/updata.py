from updata import request
from updata import _init_
import logging
def start(version):
    x = request.get(version)
    if x == False:
        print("当前已是最新版本")
        return False
    elif x == "demo":
        print("当前版本为测试版本")
        m = "demo"
        return m
    else:
        request.updata(x)
        return True
if __name__ == "__main__":
    logging.basicConfig(
            filename='web_log.txt',
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    logging.info("------检查更新程序1.0------ \n        由xiaotbl制作      \n更多信息请访问:\"https://xigjx.komoni.xyz/updata_module\"")
    version = int(input("请输入当前版本号："))
    x = start(version)
    if x == False:
        logging.info("当前已是最新版本")
    elif x == "demo":
        logging.info("当前版本为测试版本")
    else:
        logging.info("更新完成")
    logging.info(f"更新结果: {x}")