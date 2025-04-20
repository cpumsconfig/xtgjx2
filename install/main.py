#导入模块
import zipfile
import requests
import os
def main():
    m = input("是否安装？(Y/N):")
    if m == "y" or m == "Y":
        download()
    else:
        exit()
def download():
#get版本号
    x = requests.get("https://xtgjx.komoni.xyz/version.txt")
#测试用
    #print(x.content)
#get到下载网址
    y = requests.get("https://xtgjx.komoni.xyz/webdownload.txt")
#反向操作再次get
    z = requests.get(y.content)
#保存到1.zip文件里
    with open("1.zip",'wb') as f:
        f.write(z.content)
# 目标路径（注意空格需要转义）
    target_path = r"C:\Program Files (x86)\xtgjx"

# 检查目标路径是否存在
    if not os.path.exists(target_path):
        os.makedirs(target_path)

#解压文件
    try:
        with zipfile.ZipFile("1.zip", 'r') as zip_ref:
            zip_ref.extractall(target_path)
        print("解压成功！")
    except PermissionError:
        print("权限不足！请以管理员身份运行程序")
    except FileNotFoundError:
        print("ZIP 文件不存在！")
    except Exception as e:
        print(f"解压失败: {str(e)}")
    os.remove("1.zip")
#运行文件
    os.system("pause")
    run = f'start "" "{os.path.join(target_path, "1.exe")}"'
    os.system(run)
if __name__ == "__main__":
    main()