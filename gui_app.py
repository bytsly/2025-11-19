"""投票抽奖系统 - GUI窗口版本
"""
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
# Python 3.13兼容性修复 - 直接导入messagebox
import tkinter.messagebox as messagebox
import threading
import webbrowser
import os
import sys
import signal
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import socket

# 打包环境兼容性修复 - 动态导入backend模块
if getattr(sys, 'frozen', False):
    # 打包环境
    import backend.app
    create_app = backend.app.create_app
    socketio = backend.app.socketio
else:
    # 开发环境
    from backend.app import create_app, socketio

# 加载环境变量
load_dotenv()

# 定义版本信息
VERSION = "v1.0.0"


class VotingLotteryGUI:
    """投票抽奖系统GUI窗口"""
    
    def __init__(self, root):
        try:
            print("开始初始化GUI...")
            self.root = root
            self.root.title(f"投票抽奖系统 {VERSION}")
            self.root.geometry("900x650")
            self.root.resizable(True, True)
            print("窗口配置完成")
            
            # 设置窗口图标(如果有的话)
            try:
                self.root.iconbitmap("icon.ico")
            except:
                pass
            
            # 应用和服务器状态
            self.app = None
            self.server_thread = None
            self.server_process = None  # 用于跟踪服务器进程
            self.is_running = False
            self.host = "0.0.0.0"
            self.port = 5000
            print("变量初始化完成")
            
            # 创建UI
            print("开始创建UI组件...")
            self.create_widgets()
            print("UI组件创建完成")
            
            # 绑定窗口关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            print("事件绑定完成")
            
            print("初始化完成！")
            
            # 日志重定向 - 放到最后，在mainloop之后
            # self.redirect_output()
        except Exception as e:
            print(f"初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
        
    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # ========== 标题区域 ==========
        title_frame = ttk.LabelFrame(main_frame, text="系统信息", padding="10")
        title_frame.grid(row=0, column=0, sticky=tk.W + tk.E, pady=(0, 10))
        title_frame.columnconfigure(1, weight=1)
        
        ttk.Label(title_frame, text="系统名称:", font=('Arial', 10, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Label(title_frame, text="投票抽奖系统", font=('Arial', 10)).grid(
            row=0, column=1, sticky=tk.W)
        
        ttk.Label(title_frame, text="版本信息:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Label(title_frame, text=VERSION, font=('Arial', 10)).grid(
            row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(title_frame, text="服务器地址:", font=('Arial', 10, 'bold')).grid(
            row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.address_label = ttk.Label(title_frame, text="未启动", 
                                       font=('Arial', 10), foreground='gray')
        self.address_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(title_frame, text="运行状态:", font=('Arial', 10, 'bold')).grid(
            row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.status_label = ttk.Label(title_frame, text="● 已停止", 
                                      font=('Arial', 10), foreground='red')
        self.status_label.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        
        # ========== 控制面板 ==========
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_frame.grid(row=1, column=0, sticky=tk.W + tk.E, pady=(0, 10))
        
        # 第一行按钮
        button_frame1 = ttk.Frame(control_frame)
        button_frame1.pack(fill=tk.X, pady=(0, 5))
        
        self.start_btn = ttk.Button(button_frame1, text="▶ 启动服务", 
                                    command=self.start_server, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame1, text="■ 停止服务", 
                                   command=self.stop_server, width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.restart_btn = ttk.Button(button_frame1, text="↻ 重启服务", 
                                      command=self.restart_server, width=15, state=tk.DISABLED)
        self.restart_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 第二行按钮 - 首页、投票、抽奖
        button_frame2 = ttk.Frame(control_frame)
        button_frame2.pack(fill=tk.X, pady=(0, 5))
        
        self.open_home_btn = ttk.Button(button_frame2, text="🏠 打开首页", 
                                        command=lambda: self.open_browser('/'), 
                                        width=15, state=tk.DISABLED)
        self.open_home_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.open_vote_btn = ttk.Button(button_frame2, text="📊 投票页面", 
                                        command=lambda: self.open_browser('/vote'), 
                                        width=15, state=tk.DISABLED)
        self.open_vote_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.open_lottery_btn = ttk.Button(button_frame2, text="🎰 抽奖页面", 
                                           command=lambda: self.open_browser('/lottery'), 
                                           width=15, state=tk.DISABLED)
        self.open_lottery_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 第三行按钮 - 管理后台
        button_frame3 = ttk.Frame(control_frame)
        button_frame3.pack(fill=tk.X)
        
        self.open_admin_btn = ttk.Button(button_frame3, text="⚙ 管理后台", 
                                         command=lambda: self.open_browser('/admin'), 
                                         width=15, state=tk.DISABLED)
        self.open_admin_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # ========== 日志区域 ==========
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=2, column=0, sticky=tk.W + tk.E + tk.N + tk.S)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                   height=20, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=tk.W + tk.E + tk.N + tk.S)
        
        # 日志工具栏
        log_toolbar = ttk.Frame(log_frame)
        log_toolbar.grid(row=1, column=0, sticky=tk.W + tk.E, pady=(5, 0))
        
        ttk.Button(log_toolbar, text="清空日志", command=self.clear_log, 
                   width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_toolbar, text="导出日志", command=self.export_log, 
                   width=12).pack(side=tk.LEFT)
        
        # 添加版权信息
        ttk.Label(log_toolbar, text="© 2025 赵宏宇版权所有", 
                 font=('Arial', 9), foreground='gray').pack(side=tk.RIGHT, padx=(10, 0))
        
        # 添加欢迎信息
        self.log_message("=" * 80)
        self.log_message("欢迎使用由赵宏宇开发的投票抽奖系统")
        self.log_message("=" * 80)
        self.log_message("提示：点击'启动服务'按钮开始使用系统")
        self.log_message("")
        
    def log_message(self, message, level="INFO"):
        """记录日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 根据级别设置颜色
        if level == "ERROR":
            self.log_text.tag_add("error", f"end-{len(log_entry)+1}c", "end-1c")
            self.log_text.tag_config("error", foreground="red")
        elif level == "SUCCESS":
            self.log_text.tag_add("success", f"end-{len(log_entry)+1}c", "end-1c")
            self.log_text.tag_config("success", foreground="green")
        elif level == "WARNING":
            self.log_text.tag_add("warning", f"end-{len(log_entry)+1}c", "end-1c")
            self.log_text.tag_config("warning", foreground="orange")
    
    def redirect_output(self):
        """重定向标准输出到日志窗口"""
        class TextRedirector:
            def __init__(self, gui, level="INFO"):
                self.gui = gui
                self.level = level
                
            def write(self, text):
                if text.strip():
                    self.gui.log_message(text.strip(), self.level)
                    
            def flush(self):
                pass
        
        sys.stdout = TextRedirector(self, "INFO")
        sys.stderr = TextRedirector(self, "ERROR")
    
    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start_server(self):
        """启动服务器"""
        if self.is_running:
            messagebox.showwarning("警告", "服务器已经在运行中")
            return
        
        # 检查端口是否可用
        if not self._check_port_available():
            error_msg = f"端口 {self.port} 已被占用，无法启动服务器\n\n解决方法：\n1. 等待几秒后重试\n2. 关闭其他占用该端口的程序\n3. 修改配置文件更改端口"
            self.log_message(f"端口 {self.port} 已被占用", "ERROR")
            messagebox.showerror("端口被占用", error_msg)
            return
        
        try:
            self.log_message("=" * 80)
            self.log_message("正在启动服务器...", "INFO")
            
            # 创建Flask应用
            config_name = os.getenv('FLASK_ENV', 'development')
            self.app = create_app(config_name)
            
            # 获取配置
            self.host = self.app.config.get('HOST', '0.0.0.0')
            self.port = self.app.config.get('PORT', 5000)
            
            # 获取本机IP
            local_ip = self.get_local_ip()
            
            # 在新线程中启动服务器
            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()
            
            # 更新UI状态
            self.is_running = True
            self.update_ui_state()
            
            # 更新地址显示
            addresses = f"http://localhost:{self.port}  |  http://{local_ip}:{self.port}"
            self.address_label.config(text=addresses, foreground='blue')
            
            self.log_message("服务器启动成功！", "SUCCESS")
            self.log_message(f"本地访问: http://localhost:{self.port}", "SUCCESS")
            self.log_message(f"局域网访问: http://{local_ip}:{self.port}", "SUCCESS")
            self.log_message(f"管理后台: http://localhost:{self.port}/admin", "INFO")
            self.log_message(f"投票页面: http://localhost:{self.port}/vote", "INFO")
            self.log_message(f"抽奖页面: http://localhost:{self.port}/lottery", "INFO")
            self.log_message("=" * 80)
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.log_message(f"启动失败: {str(e)}", "ERROR")
            # 同时记录完整回溯，便于远程诊断
            for line in tb.splitlines():
                self.log_message(line, "ERROR")
            messagebox.showerror("启动失败", f"服务器启动失败：\n{str(e)}")
            self.is_running = False
            self.update_ui_state()
    
    def _run_server(self):
        """运行服务器(在独立线程中)"""
        try:
            # 在打包环境中，使用更兼容的SocketIO配置
            # 避免异步模式检测错误
            socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.log_message(f"服务器运行错误: {str(e)}", "ERROR")
            for line in tb.splitlines():
                self.log_message(line, "ERROR")
            self.is_running = False
            self.root.after(0, self.update_ui_state)
    
    def stop_server(self):
        """停止服务器"""
        if not self.is_running:
            messagebox.showwarning("警告", "服务器未运行")
            return
        
        try:
            self.log_message("正在停止服务器...", "WARNING")
            
            # 标记为停止状态
            self.is_running = False
            
            # 主动终止占用端口的进程
            killed_count = self._kill_process_by_port()
            if killed_count > 0:
                self.log_message(f"已终止 {killed_count} 个占用端口 {self.port} 的进程", "SUCCESS")
            
            # 清空应用实例
            self.app = None
            self.server_process = None
            
            self.log_message("服务器已停止", "WARNING")
            self.log_message("端口已释放，可以立即重启", "INFO")
            
            self.address_label.config(text="未启动", foreground='gray')
            self.update_ui_state()
            
        except Exception as e:
            self.log_message(f"停止失败: {str(e)}", "ERROR")
            messagebox.showerror("停止失败", f"服务器停止失败：\n{str(e)}")
    
    def restart_server(self):
        """重启服务器"""
        self.log_message("正在重启服务器...", "INFO")
        self.stop_server()
        # 由于主动杀进程，端口会立即释放，减少等待时间
        self.root.after(1500, self._delayed_start)
    
    def _delayed_start(self):
        """延迟启动服务器(用于重启)"""
        if self._check_port_available():
            self.start_server()
        else:
            # 如果端口仍被占用，再次尝试杀进程
            self.log_message("端口仍被占用，正在清理...", "WARNING")
            killed = self._kill_process_by_port()
            if killed > 0:
                self.log_message(f"已清理 {killed} 个残留进程", "INFO")
            self.root.after(1000, self._delayed_start)
    
    def _check_port_available(self):
        """检查端口是否可用"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            test_socket.bind((self.host, self.port))
            test_socket.close()
            return True
        except OSError:
            return False
    
    def _kill_process_by_port(self):
        """终止占用指定端口的进程"""
        killed_count = 0
        try:
            if sys.platform == 'win32':
                # Windows系统使用netstat和taskkill
                # 查找占用端口的进程
                cmd = f'netstat -ano | findstr :{self.port}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    # 提取PID
                    pids = set()
                    for line in result.stdout.strip().split('\n'):
                        if f':{self.port}' in line:
                            parts = line.strip().split()
                            if len(parts) >= 5:
                                pid = parts[-1]
                                if pid.isdigit() and pid != '0':
                                    pids.add(pid)
                    
                    # 终止进程
                    for pid in pids:
                        try:
                            subprocess.run(f'taskkill /F /PID {pid}', 
                                         shell=True, capture_output=True)
                            killed_count += 1
                            self.log_message(f"已终止进程 PID: {pid}", "INFO")
                        except Exception as e:
                            self.log_message(f"终止进程 {pid} 失败: {str(e)}", "WARNING")
            else:
                # Linux/Mac系统使用lsof和kill
                cmd = f'lsof -ti:{self.port}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid:
                            try:
                                os.kill(int(pid), signal.SIGTERM)
                                killed_count += 1
                                self.log_message(f"已终止进程 PID: {pid}", "INFO")
                            except Exception as e:
                                self.log_message(f"终止进程 {pid} 失败: {str(e)}", "WARNING")
        except Exception as e:
            self.log_message(f"清理端口进程失败: {str(e)}", "WARNING")
        
        return killed_count
    
    def open_browser(self, path='/'):
        """打开浏览器"""
        if not self.is_running:
            messagebox.showwarning("警告", "请先启动服务器")
            return
        
        url = f"http://localhost:{self.port}{path}"
        self.log_message(f"正在打开浏览器: {url}", "INFO")
        webbrowser.open(url)
    
    def update_ui_state(self):
        """更新UI状态"""
        if self.is_running:
            # 服务运行中
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.restart_btn.config(state=tk.NORMAL)
            self.open_home_btn.config(state=tk.NORMAL)
            self.open_admin_btn.config(state=tk.NORMAL)
            self.open_vote_btn.config(state=tk.NORMAL)
            self.open_lottery_btn.config(state=tk.NORMAL)
            self.status_label.config(text="● 运行中", foreground='green')
        else:
            # 服务已停止
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.restart_btn.config(state=tk.DISABLED)
            self.open_home_btn.config(state=tk.DISABLED)
            self.open_admin_btn.config(state=tk.DISABLED)
            self.open_vote_btn.config(state=tk.DISABLED)
            self.open_lottery_btn.config(state=tk.DISABLED)
            self.status_label.config(text="● 已停止", foreground='red')
    
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("日志已清空", "INFO")
    
    def export_log(self):
        """导出日志"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialfile=f"system_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"日志已导出: {filename}", "SUCCESS")
                messagebox.showinfo("成功", "日志导出成功")
        except Exception as e:
            self.log_message(f"导出失败: {str(e)}", "ERROR")
            messagebox.showerror("导出失败", f"日志导出失败：\n{str(e)}")
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            if messagebox.askokcancel("退出确认", "服务器正在运行，确定要退出吗？"):
                self.log_message("正在关闭程序...", "WARNING")
                self.is_running = False
                # 主动杀掉占用端口的进程
                killed = self._kill_process_by_port()
                if killed > 0:
                    self.log_message(f"已清理 {killed} 个进程", "SUCCESS")
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主函数"""
    try:
        print("正在启动GUI窗口...")
        root = tk.Tk()
        print("Tkinter主窗口创建成功")
        app = VotingLotteryGUI(root)
        print("VotingLotteryGUI实例化成功")
        print("进入主循环...")
        root.mainloop()
    except Exception as e:
        print(f"程序启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        input("按任意键退出...")


if __name__ == '__main__':
    main()
