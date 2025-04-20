import os
import sys
import threading
from updata import updata

def ts():
    os.system("title 系统工具箱 -- xiaotbl")
    print("1.更新软件 \n0.退出")

def ts1():
    print("updata --更新软件\nhelp --帮助")
def ts2():
    print("关重启程序 --shutdown命令\npoweroff      --关机命令\nreboot        --重启命令")
    print("")
def start_update():
    updata_thread = threading.Thread(target=updata.start)
    updata_thread.start()
    updata_thread.join()  # 等待线程完成

def main():
    while True:
        ts()
        x = input("请输入序号:")
        if x == "1":
            start_update()
        elif x == "0":
            print("感谢使用，再见！")
            os.system("pause")
            sys.exit()

if __name__ == "__main__":
    if len(sys.argv) == 1:  # 如果没有传递参数，则启动主程序
        main()
    else:
        # 检查传递的命令行参数
        if sys.argv[1] == "updata":  # 如果命令是 'updata'，启动更新
            start_update()
        elif sys.argv[1] == "help":  # 如果命令是 'help'，显示帮助信息
            ts1()
        elif sys.argv[1] == "xiaotbl":
            print(":)")
            print("https://space.bilibili.com/1916471385")
            os.system("pause")
        elif sys.argv[1] == "shutdown poweroff":
            os.system("shutdown /s")
        elif sys.argv[1] == "shutdown reboot":
            os.system("shutdown /r")
        elif sys.argv[1] == "shutdown help":
            ts2()
        else:
            print("无效命令")  # 如果命令无效，提示无效命令