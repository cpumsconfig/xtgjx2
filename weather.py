import tkinter as tk
from tkinter import messagebox
import requests
import json

class WeatherApp:
    def __init__(self, master):
        self.master = master
        master.title("城市天气查询")
        master.geometry("500x320")
        master.configure(bg="#F0F0F0")

        # 界面组件布局
        self.create_widgets()

    def create_widgets(self):
        # 输入区域
        self.input_frame = tk.Frame(self.master, bg="#F0F0F0")
        self.input_frame.pack(pady=15)

        self.city_label = tk.Label(self.input_frame, text="输入城市编号:", 
                                 font=("微软雅黑", 12), bg="#F0F0F0")
        self.city_label.grid(row=0, column=0, padx=5)

        self.city_entry = tk.Entry(self.input_frame, width=25, 
                                 font=("微软雅黑", 12), relief="groove")
        self.city_entry.grid(row=0, column=1, padx=5)

        self.query_btn = tk.Button(self.input_frame, text="查询天气", 
                                 command=self.fetch_weather, bg="#4CAF50",
                                 fg="white", font=("微软雅黑", 10))
        self.query_btn.grid(row=0, column=2, padx=10)

        # 结果显示区域
        self.result_text = tk.Text(self.master, width=50, height=10, 
                                 font=("宋体", 11), wrap=tk.WORD)
        self.result_text.pack(pady=10)

    def fetch_weather(self):
        city_code = self.city_entry.get().strip()
        if not city_code:
            messagebox.showwarning("输入错误", "城市编号不能为空")
            return

        try:
            # 调用新的天气接口
            url = f"http://t.weather.itboy.net/api/weather/city/{city_code}"
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == 403:  # 根据新接口返回的状态码调整
                self.update_result(f"【{data.get('city_name', '未知城市')}】\n{data.get('message', '查询失败')}")
            else:
                # 解析核心数据
                current = data["data"]
                result = (
                    f"【{current['city_name']}天气预报】\n"
                    f"当前温度：{current['wendu']}℃\n"
                    f"天气状况：{current['forecast']['type']}\n"
                    f"风力等级：{current['forecast']['fl']}\n"
                    f"最高温度：{current['forecast']['high']}℃\n"
                    f"最低温度：{current['forecast']['low']}℃\n"
                    f"AQI：{current['aqi']}\n"
                    f"日出时间：{current['sunrise']}\n"
                    f"日落时间：{current['sunset']}"
                )
                self.update_result(result)

        except requests.exceptions.RequestException as e:
            messagebox.showerror("网络错误", f"请求失败：{str(e)}")
        except (KeyError, json.JSONDecodeError):
            messagebox.showerror("数据错误", "接口返回数据格式异常")

    def update_result(self, text):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.tag_add("title", "1.0", "1.end")
        self.result_text.tag_config("title", foreground="blue", font=("微软雅黑", 12, "bold"))

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
