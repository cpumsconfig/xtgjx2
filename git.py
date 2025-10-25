import os

def user():
    username = input("请输入用户名：")
    email = input("请输入邮箱：")
    os.system(f"git config --global user.name \"{username}\"")
    os.system(f"git config --global user.email \"{email}\"")
    print("设置成功！")
    os.system("cls")

def ssl():
    email1 = input("请输入邮箱：")
    os.system(f"ssh-keygen -t rsa -b 4096 -C \"{email1}\"")
    print("可以了，以上是你的密钥，请保管好")
    os.system("cat ~/.ssh/id_rsa.pub")
    os.system("pause")
    os.system("cls")

def ssh_connent():
    username1 = input("请输入用户名：")
    repository = input("请输入你的仓库：")
    os.system(f"git remote add origin git@github.com:{username1}/{repository}.git")
    print("已完成连接")
    os.system("cls")

def download():
    url = input("请输入你克隆仓库的地址：")
    os.system(f"git clone {url}")

def pull():
    x = input("请输入你的文件或文件夹（全部文件请输入'.'）：")
    y = input("请输入你提交的说明：")
    os.system(f"git add {x}")
    os.system(f"git commit -m \"{y}\"")
    os.system("git pull -f origin main")



while True:
    print("""__________git管理系统__________
    1.登录账户
    2.获取密钥
    3.连接仓库
    4.克隆仓库
    5.提交文件
    6.启动git
    7.查看版本号
    8.退出
    """)
    z = input("请输入序列号：")
    if z == '1':
        user()
    elif z == '2':
        ssl()
    elif z == '3':
        ssh_connent()
    elif z == '4':
        download()
    elif z == '5':
        pull()
    elif z == '6':
        os.system("git init")
    elif z == '7':
        print("版本号: 1.0.0")
    elif z == '8':
        break
    elif z == '9':
       os.system("git branch -m master main")
    elif z == '10':
       os.system("git config pull.rebase true")
       os.system("git config pull.ff only")
    else:
        print("不是这个")
