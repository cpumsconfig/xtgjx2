import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import time
import base64
import hmac
import hashlib
import os
import json
import re
from urllib.parse import parse_qs, urlparse

class TOTPGenerator:
    def __init__(self, secret):
        self.secret = secret.replace(" ", "").upper()
        
    def generate_totp(self, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time())
        
        time_step = 30
        counter = int(timestamp // time_step)
        
        try:
            # 处理Base32密钥
            key = base64.b32decode(self.secret + '=' * ((8 - len(self.secret) % 8) % 8), casefold=True)
        except:
            return "Invalid Key"
        
        counter_bytes = counter.to_bytes(8, 'big')
        hmac_digest = hmac.new(key, counter_bytes, hashlib.sha1).digest()
        
        # 动态截断
        offset = hmac_digest[-1] & 0x0F
        code = int.from_bytes(hmac_digest[offset:offset+4], 'big') & 0x7FFFFFFF
        
        # 生成6位数字
        return f"{code % 10**6:06d}"
class TOTPApp:
    def __init__(self, root):
        self.root = root
        root.title("TOTP 验证器")
        root.geometry("400x400")
        root.resizable(False, False)
        
        # 账户数据 {账户名: 密钥}
        self.secrets = {}
        self.current_account = None
        self.storage_file = "totp.passwd"
        
        # 先设置UI（确保所有变量已创建）
        self.setup_ui()
        
        # 然后加载账户
        self.load_accounts()
        
        # 更新账户列表并尝试选择第一个账户
        self.update_account_list()
        if self.account_cb['values']:
            self.account_var.set(self.account_cb['values'][0])
            self.select_account()
        
        self.update_clock()
    
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 输入框
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        # 改为"网站提供的TOTP应用代码"
        ttk.Label(input_frame, text="TOTP应用代码:").pack(side=tk.LEFT)
        self.code_entry = ttk.Entry(input_frame, width=35)
        self.code_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 添加按钮
        self.add_btn = ttk.Button(input_frame, text="添加", command=self.add_account, width=6)
        self.add_btn.pack(side=tk.RIGHT)
        
        # 添加说明标签
        ttk.Label(main_frame, text="(输入网站提供的TOTP应用代码或密钥)", 
                 font=("Arial", 8), foreground="gray").pack(anchor=tk.W)
        
        # 账户管理框架
        account_frame = ttk.LabelFrame(main_frame, text="账户管理")
        account_frame.pack(fill=tk.X, pady=10)
        
        # 账户选择
        self.account_var = tk.StringVar()
        account_select_frame = ttk.Frame(account_frame)
        account_select_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(account_select_frame, text="选择账户:").pack(side=tk.LEFT)
        self.account_cb = ttk.Combobox(account_select_frame, textvariable=self.account_var, width=25, state="readonly")
        self.account_cb.pack(side=tk.LEFT, padx=5)
        self.account_cb.bind("<<ComboboxSelected>>", self.select_account)
        
        # 账户操作按钮
        btn_frame = ttk.Frame(account_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="删除", command=self.delete_account).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="手动添加", command=self.add_manual_account).pack(side=tk.LEFT, padx=2)
        
        # TOTP 显示框架
        totp_frame = ttk.LabelFrame(main_frame, text="验证码")
        totp_frame.pack(fill=tk.X, pady=10)
        
        # 账户名称显示（小字体）
        self.account_label = ttk.Label(totp_frame, text="请选择账户", font=("Arial", 10), foreground="gray")
        self.account_label.pack(pady=(10, 0))
        
        # TOTP 显示（大字体）
        self.totp_var = tk.StringVar(value="------")
        totp_display = ttk.Label(totp_frame, textvariable=self.totp_var, font=("Arial", 32, "bold"))
        totp_display.pack(pady=10)
        
        # 倒计时进度条
        self.progress = ttk.Progressbar(totp_frame, orient='horizontal', length=300, mode='determinate')
        self.progress.pack(pady=5, padx=10)
        
        # 剩余时间标签
        time_frame = ttk.Frame(totp_frame)
        time_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(time_frame, text="剩余时间:").pack(side=tk.LEFT)
        self.time_var = tk.StringVar(value="30s")
        ttk.Label(time_frame, textvariable=self.time_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        # 复制按钮
        ttk.Button(totp_frame, text="复制验证码", command=self.copy_totp).pack(pady=10)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")  # 确保在__init__中提前创建
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 更新账户列表
        self.update_account_list()
        
        # 默认选择第一个账户
        if self.account_cb['values']:
            self.account_var.set(self.account_cb['values'][0])
            self.select_account()
    
    def load_accounts(self):
        """从加密文件中加载账户"""
        if not os.path.exists(self.storage_file):
            self.status_var.set("没有账户文件")
            return
            
        try:
            with open(self.storage_file, "rb") as f:
                encrypted_data = f.read()
            
            # Base64 解码
            decoded_data = base64.b64decode(encrypted_data).decode('utf-8')
            self.secrets = json.loads(decoded_data)
            self.status_var.set(f"已加载 {len(self.secrets)} 个账户")
        except Exception as e:
            messagebox.showerror("错误", f"加载账户失败: {str(e)}")
            self.status_var.set("账户加载失败")
    
    def save_accounts(self):
        """保存账户到加密文件"""
        try:
            # 转换为JSON并Base64编码
            json_data = json.dumps(self.secrets)
            encoded_data = base64.b64encode(json_data.encode('utf-8'))
            
            with open(self.storage_file, "wb") as f:
                f.write(encoded_data)
            
            self.status_var.set(f"账户已保存 ({len(self.secrets)}个)")
            return True
        except Exception as e:
            messagebox.showerror("错误", f"保存账户失败: {str(e)}")
            self.status_var.set("保存失败")
            return False
    
    def update_account_list(self):
        """更新账户下拉列表"""
        accounts = list(self.secrets.keys())
        self.account_cb['values'] = accounts
    
    def add_account(self):
        """通过TOTP应用代码添加账户"""
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showerror("错误", "请输入TOTP应用代码")
            return
        
        # 尝试解析为URI格式
        if code.lower().startswith("otpauth://"):
            # 解析URI
            try:
                parsed = urlparse(code)
                if parsed.scheme != "otpauth" or parsed.netloc != "totp":
                    raise ValueError("无效的URI协议")
                    
                # 获取账户名
                account = parsed.path.lstrip('/')
                
                # 获取参数
                query_params = parse_qs(parsed.query)
                secret = query_params.get('secret', [''])[0]
                
                if not secret:
                    raise ValueError("未找到密钥")
                    
                # 验证密钥格式
                if not re.match(r"^[A-Z2-7]+=*$", secret, re.I):
                    raise ValueError("无效的密钥格式")
                    
                # 添加到账户列表
                self.secrets[account] = secret
                self.save_accounts()
                self.update_account_list()
                
                # 选择新添加的账户
                self.account_var.set(account)
                self.select_account()
                
                self.code_entry.delete(0, tk.END)
                self.status_var.set(f"已添加账户: {account}")
                return
            except Exception as e:
                # 如果不是有效的URI，尝试作为纯密钥处理
                pass
        
        # 如果不是URI格式，则作为纯密钥处理
        account = simpledialog.askstring("输入账户名", "请输入账户名称:", parent=self.root)
        if not account:
            return
            
        # 清理密钥（去除空格）
        clean_secret = code.replace(" ", "").upper()
        
        # 验证密钥格式
        if not re.match(r"^[A-Z2-7]+=*$", clean_secret, re.I):
            messagebox.showerror("错误", "无效的密钥格式")
            return
            
        self.secrets[account] = clean_secret
        self.save_accounts()
        self.update_account_list()
        
        # 选择新添加的账户
        self.account_var.set(account)
        self.select_account()
        self.code_entry.delete(0, tk.END)
        self.status_var.set(f"已添加账户: {account}")
    
    def add_manual_account(self):
        """手动添加账户"""
        account = simpledialog.askstring("手动添加", "请输入账户名称:")
        if not account:
            return
            
        secret = simpledialog.askstring("手动添加", "请输入密钥:", show='*')
        if not secret:
            return
            
        # 验证密钥格式
        clean_secret = secret.replace(" ", "").upper()
        if not re.match(r"^[A-Z2-7]+=*$", clean_secret, re.I):
            messagebox.showerror("错误", "无效的密钥格式")
            return
            
        self.secrets[account] = clean_secret
        self.save_accounts()
        self.update_account_list()
        
        # 选择新添加的账户
        self.account_var.set(account)
        self.select_account()
        self.status_var.set(f"手动添加账户: {account}")
    
    def delete_account(self):
        """删除当前账户"""
        account = self.account_var.get()
        if not account or account not in self.secrets:
            return
            
        if messagebox.askyesno("确认删除", f"确定要删除账户 '{account}' 吗?"):
            del self.secrets[account]
            self.save_accounts()
            self.update_account_list()
            
            # 选择其他账户或清空
            if self.account_cb['values']:
                self.account_var.set(self.account_cb['values'][0])
                self.select_account()
            else:
                self.account_var.set('')
                self.current_account = None
                self.account_label.config(text="请选择账户")
                self.totp_var.set("------")
            
            self.status_var.set(f"已删除账户: {account}")
    
    def select_account(self, event=None):
        """选择账户"""
        account = self.account_var.get()
        if account in self.secrets:
            self.current_account = account
            self.account_label.config(text=account)
            self.status_var.set(f"已选择账户: {account}")
    
    def update_clock(self):
        """更新TOTP和倒计时"""
        if self.current_account and self.current_account in self.secrets:
            timestamp = time.time()
            secret = self.secrets[self.current_account]
            totp = TOTPGenerator(secret).generate_totp(timestamp)
            self.totp_var.set(totp)
            
            # 计算剩余时间
            remaining = 30 - (timestamp % 30)
            self.time_var.set(f"{int(remaining)}秒")
            self.progress['value'] = (30 - remaining) * (100/30)
        else:
            self.totp_var.set("------")
            self.time_var.set("0秒")
            self.progress['value'] = 0
        
        # 每秒更新一次
        self.root.after(1000, self.update_clock)
    
    def copy_totp(self):
        """复制TOTP到剪贴板"""
        if self.current_account and self.totp_var.get() != "------":
            self.root.clipboard_clear()
            self.root.clipboard_append(self.totp_var.get())
            self.status_var.set("验证码已复制")
        else:
            messagebox.showinfo("提示", "没有可复制的验证码")

if __name__ == "__main__":
    root = tk.Tk()
    app = TOTPApp(root)
    root.mainloop()	