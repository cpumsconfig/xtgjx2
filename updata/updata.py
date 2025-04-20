from updata import request
from updata import _init_
def start():
    x = request.get()
    if x == False:
        print("当前已是最新版本")
    else:
        request.updata(x)