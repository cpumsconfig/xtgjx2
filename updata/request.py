#导入模块
import requests
import os
#建立get函数
def get(version):
    #get到版本
    x = requests.get("https://xtgjx.komoni.xyz/version.txt")
    if int(x.content) > version: #如果获取到的不等于100000版本号
        y = requests.get("https://xtgjx.komoni.xyz/webdownload.txt") #get到下载链接
        return y.content #返回下载值
    # 如果获取到的大于获取到的版本号
    elif int(x.content) < version: #如果获取到的版本号大于
        x = "demo"
        return x #返回下载值
    else: #否则
        return False #返回否
#建立updata函数
def updata(download):
    x = requests.get(download) #get获取到的内容
    #被注释的是运行更新助手全过程，最终1.0版本会取消注释
    '''
    with open("upinstall.exe",'wb') as f:
        f.write(x.content)
    os.system("upinstall.exe")
    '''
    #测试用，最终1.0版本会加注释
    os.system("sudo python upinstall.py")