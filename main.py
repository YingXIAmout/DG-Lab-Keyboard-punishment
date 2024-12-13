import subprocess
import psutil
import platform
import os
import sys
import json
import re
import webbrowser
import threading
import asyncio
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime
from pynput import keyboard
import ws_server
import ws_client
import keyborad_listen_gui
import pulse_wave_gui
import keyboard_listen
#图形化窗口
root = None
#初始服务器配置
server_ip = None
server_port = None
#客户端配置
client = None
#线程 服务端与客户端
thread_server = None
thread_client = None
thread_keybind_config_gui = None
thread_keyboard_listening = None
thread_start_pulse_wave_gui = None
error_count = 0
log_window = None
# 日志
def log(msg):
    message = "[{}] {}".format(datetime.now().strftime('%H:%M:%S'),msg)
    print(message)

#加载配置文件
def load_config(file_path):
    global server_ip,server_port
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            file_content = file.read()
            try:
                data  = json.loads(file_content)
                server_ip = data['server']['ip'] if data['server']['ip'] != '' else ws_server.get_local_ip()
                server_port = data['server']['port'] if data['server']['port'] != '' else 1145
                return True
            except json.JSONDecodeError:
                log(f"解析配置文件出错")
                return False

#启动服务端
def start_server(ip,port,mode):
    # 使用 asyncio.run() 来运行主协程
    try:
        asyncio.run(ws_server.main(ip,port,mode))
    except KeyboardInterrupt:
        # 在这里可以添加进一步的清理资源、关闭进程等操作
        ws_server.stop = True
        ws_server.log("用户手动关闭服务器，服务器已关闭")
        return
#启动客户端
def start_client():
    global client
    client_ws = root.nametowidget('client_ws')
    uri = "ws://{}:1145".format(ws_client.get_local_ip()) if client_ws.get() == "" else client_ws.get()
    client = ws_client.WebSocketClient(uri)
    client.start_receive_thread()
#打开key配置界面
def start_keybind_config_gui():
    app = keyborad_listen_gui.QApplication(sys.argv)
    ex = keyborad_listen_gui.KeyBindingGUI()
    ex.show()
    sys.exit(app.exec_())
#打开波形生成器
def start_pulse_wave_gui():
    pulse_wave_gui_app = pulse_wave_gui.WaveDataInputAndConversion()
    pulse_wave_gui_app.run()
#打开日志窗口
def start_log_capture():
    global log_window
    log_window = log_capture.LogCaptureWindow()
    log_window.start()
#启动键盘监听
def keyboard_listening():
    global error_count
    if thread_client is None:
        log('客户端未启动！')
        return
    #current_process = psutil.Process(os.getpid())
    #current_process.nice(psutil.HIGH_PRIORITY_CLASS)
    keyboard_listen_thread = keyboard_listen.KeyBindingHandler(client)
    keyboard_listen_thread.start_listening()
    log('键盘监听已启动！')
    while not keyboard_listen.stop_listen:
        pass
    keyboard_listen_thread.stop_listening()
#启动服务端与客户端线程
def start_server_threading(ip = 'localhost',port = 1145,mode = 'n-n'):
    global thread_server
    ws_server.stop = False
    thread_server = threading.Thread(target=start_server,args=(ip,port,mode))
    thread_server.start()

    btn_start_server = root.nametowidget('start_server_btn')
    btn_close_server = root.nametowidget('close_server_btn')
    btn_start_server.grid_forget()
    btn_close_server.grid(row=1, column=0)
    btn_close_server.config(state=tk.DISABLED)
def start_client_in_thread():
    global thread_client
    ws_client.stop_flag = False
    thread_client = threading.Thread(target=start_client)
    thread_client.start()

    btn = root.nametowidget('start_client_btn')
    client_ws = root.nametowidget('client_ws')
    btn_close_client = root.nametowidget('close_client_btn')
    btn.grid_forget()
    btn_close_client.grid(row=2, column=0)
    btn_close_client.config(state=tk.DISABLED)
    client_ws.config(state=tk.DISABLED)
def start_keybind_config_gui_in_thread():
    global thread_keybind_config_gui
    thread_keybind_config_gui = threading.Thread(target=start_keybind_config_gui)
    thread_keybind_config_gui.start()
def start_pulse_wave_gui_in_thread():
    global thread_start_pulse_wave_gui
    thread_start_pulse_wave_gui = threading.Thread(target=start_pulse_wave_gui)
    thread_start_pulse_wave_gui.start()
def start_keyboard_listening_in_thread():
    global thread_keyboard_listening
    keyboard_listen.stop_listening = False
    thread_keyboard_listening= threading.Thread(target=keyboard_listening)
    thread_keyboard_listening.start()

    btn_keyboard_listening = root.nametowidget('start_keyboard_listening')
    btn_keyboard_listening_stop = root.nametowidget('stop_keyboard_listening')
    btn_keyboard_listening.grid_forget()
    btn_keyboard_listening_stop.grid(row=3, column=0)
#设置强度
def set_strength(data):
    if client is not None:
        strength_A = data.get('A') if data.get('A').strip() != '' or data.get('A') is not None else '0'
        send_data_A = {
            'type': 3,
            'message': 'set channel',
            'channel': 'A',
            'strength': int(strength_A),
            'clientId': '',
            'targetId': ''
        }

        client.handle_message(send_data_A)
        strength_B = data.get('B') if data.get('B') != '' or data.get('B') is not None else '0'
        send_data_B = {
            'type': 3,
            'message': 'set channel',
            'channel': 'B',
            'strength': int(strength_B),
            'clientId': '',
            'targetId': ''
        }
        client.handle_message(send_data_B)
    else:
        log('未启动客户端！')

#启动GUI
def start_server_and_gui():
    global  root,error_count
    root = tk.Tk()
    # 启动ws_server.py
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    conf_file_path = os.path.join(base_dir, "data", "config.json")
    load_config(conf_file_path)
    #if load_config(conf_file_path):
        #start_server_threading(server_ip, server_port)
    #else:
        #log("读取配置文件失败")
        #start_server_threading()
    # 启动gui.py，这里假设gui.py是一个完整的可执行的有界面的Python脚本

    root.title("郊狼 Server&Client")
    root.geometry("800x300")
    root.resizable(False, False)
    def show_image():
        system = platform.system()
        image_path = "data/qrcode.png"
        try:
            if system == "Windows":
                # 在Windows上使用默认图片查看器打开图片，这里使用start命令
                subprocess.run(['start', '', image_path], shell=True)
            elif system == "Linux":
                # 在Linux上常见的使用xdg-open来调用默认应用打开图片
                subprocess.run(['xdg-open', image_path])
            elif system == "Darwin":
                # 在macOS上使用open命令调用默认应用打开图片
                subprocess.run(['open', image_path])
            else:
                print(f"不支持的操作系统: {system}")
        except FileNotFoundError:
            print("图片文件未找到，请检查路径是否正确。")

    def get_strength_text():
        data = {
            'A':strength_A.get(),
            'B':strength_B.get()
        }
        return data
    def thread_close(close_type):
        global thread_client, thread_server, thread_keyboard_listening,error_count
        # 客户端如果在运行关闭客户端
        if thread_client is not None and close_type == 'Client':
            ws_client.stop_flag = True
            try:
                asyncio.run(ws_server.closed_client(client.clients['clientId']))
            except RuntimeError:
                error_count += 1
            thread_client.join()
            thread_client = None
            btn_close_client.grid_forget()
            btn.grid(row=2, column=0)
            client_ws.config(state=tk.NORMAL)
        # 服务端如果在运行关闭服务端
        if thread_server is not None and close_type == 'Server':
            ws_server.stop = True
            try:
                asyncio.run(ws_server.server_closed())
            except RuntimeError:
                error_count += 1
            thread_server.join()
            thread_server = None
            btn_close_server.grid_forget()
            btn_start_server.grid(row=1, column=0)
        # 按键监听如果在运行关闭按键监听
        if thread_keyboard_listening is not None and close_type == ('Keyboard_listen' or 'Client'):
            keyboard_listen.stop_listen = True
            thread_keyboard_listening.join()
            thread_keyboard_listening = None
            btn_keyboard_listening_stop.grid_forget()
            btn_keyboard_listening.grid(row=3, column=0)
            log('键盘监听已关闭')
    frame = tk.Frame(root,bd=4,relief=tk.RIDGE)
    frame.grid(row=2, column=1, rowspan=3,columnspan=2,padx=10, pady=10, sticky="nsew")
    frame.config(bg="lightblue")
    my_font = tkfont.Font(size=12)
    # 创建功能页面标签
    label = tk.Label(root, text="郊狼按键惩罚\n功能页面",font=my_font)
    #创建客户端连接信息标签
    label_client_font = tkfont.Font(size=10)
    label_client = tk.Label(root,text="客户端连接地址：",font=label_client_font)
    # 创建文本输入框
    client_ws = tk.Entry(root,name='client_ws')
    # 创建启动服务端按钮&关闭服务端按钮并调整大小
    btn_start_server = tk.Button(root, text="启动服务端", command=lambda: start_server_threading(server_ip,server_port), width=20, height=1,name='start_server_btn')
    btn_close_server = tk.Button(root, text="关闭服务端",
                                 command=lambda: thread_close('Server'), width=20, height=1,
                                 name='close_server_btn')
    # 创建启动客户端按钮并调整大小
    btn = tk.Button(root, text="启动客户端", command=start_client_in_thread, width=20, height=1,name='start_client_btn')
    btn_close_client = tk.Button(root, text="关闭客户端", command=lambda: thread_close('Client'), width=20, height=1,
                    name='close_client_btn')
    # 创建按键监听启动按钮
    btn_keyboard_listening = tk.Button(root, text="启动键盘监听", command=start_keyboard_listening_in_thread,
                                       width=20, height=1,name="start_keyboard_listening")
    btn_keyboard_listening_stop = tk.Button(root, text="关闭键盘监听", command=lambda: thread_close('Keyboard_listen'),
                                       width=20, height=1,name="stop_keyboard_listening")
    # 创建显示二维码连接图片按钮并调整大小
    btn_image_button = tk.Button(root, text="显示二维码", command=show_image, width=20, height=1)
    # 创建打开配置按钮并调整大小
    btn_start_gui = tk.Button(root, text="打开按键配置", command=start_keybind_config_gui_in_thread, width=20, height=1)
    # 创建打开波形生成器按钮并调整大小
    btn_start_wave_data_gui = tk.Button(root, text="打开波形生成器", command=start_pulse_wave_gui_in_thread, width=20, height=1)
    # 启动日志窗口
    btn_start_log_capture = tk.Button(root, text="启动日志捕获", command=start_log_capture, width=20, height=1)
    # 创建作者标签并放在底部居中
    writer = tk.Label(root, text="By 影曦Amout")
    # 创建超链接标签并放在底部居中
    link_label = tk.Label(root, text="Github", fg="blue", cursor="hand2")
    # 创建监听输入框
    text_widget = tk.Text(root,width=45, height=350)
    #text_widget.config(state=tk.DISABLED)

    # 创建强度A值输入框
    strength_A = tk.Entry(frame)
    # 创建强度B值输入框
    strength_B = tk.Entry(frame)
    # 创建强度值设定按钮
    btn_set_strength = tk.Button(frame, text="设置初始强度", command=lambda: set_strength(get_strength_text()), width=32, height=1)
    # 创建标签
    strength_label = tk.Label(frame,text="郊狼通道强度值设置",bg="lightblue")
    strength_A_label = tk.Label(frame,text="通道A强度值：",bg="lightblue")
    strength_B_label = tk.Label(frame,text="通道B强度值：",bg="lightblue")
    #界面UI
    label.grid(row=0, column=0, sticky='nw')

    label_client.grid(row=0, column=1)
    client_ws.grid(row=0, column=2)

    btn_start_server.grid(row=1, column=0)
    #btn_close_server.grid(row=1, column=0)

    btn.grid(row=2, column=0)
    #btn_close_client.grid(row=2, column=0)

    btn_keyboard_listening.grid(row=3, column=0)
    #btn_keyboard_listening_stop.grid(row=3,column=0)

    btn_image_button.grid(row=4, column=0)
    btn_start_gui.grid(row=1, column=1)
    btn_start_wave_data_gui.grid(row=1, column=2)
    writer.grid(row=5, column=0, columnspan=2, sticky='sw')
    link_label.grid(row=5, column=2, sticky='se')
    link_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/YingXIAmout/DG-Lab-Keyboard-punishment"))

    strength_label.grid(row=0,column=0,columnspan=2)
    strength_A_label.grid(row=1,column=0)
    strength_B_label.grid(row=2,column=0)
    strength_A.grid(row=1, column=1)
    strength_B.grid(row=2, column=1)
    frame.grid_columnconfigure(1,weight=1)

    btn_set_strength.grid(row=3, column=0,columnspan=2)
    text_widget.grid(row=0, column=3, rowspan=6)
    # 设置行和列的权重，使按钮在窗口大小变化时能自动调整位置并保持居中
    for i in range(8):
        root.grid_rowconfigure(i, weight=1)
    for j in range(5):
        root.grid_columnconfigure(j, weight=1)

    root.protocol("WM_DELETE_WINDOW", on_close_window)  # 绑定窗口关闭事件处理函数

    console_redirector = ConsoleRedirector(text_widget)
    sys.stdout = console_redirector
    root.mainloop()

#窗口关闭操作
def on_close_window():
    global thread_client, thread_server, thread_keyboard_listening,error_count
    sys.stdout = None
    # 客户端如果在运行关闭客户端
    ws_client.stop_listening = True
    ws_client.stop_flag = True
    try:
        if thread_client is not None:
            thread_client.join()
            thread_client = None
        ws_server.stop = True
        # 服务端如果在运行关闭服务端
        if thread_server is not None:
            thread_server.join()
            thread_server = None
        # 按键监听如果在运行关闭按键监听
        keyboard_listen.stop_listen = True
        if thread_keyboard_listening is not None:
            thread_keyboard_listening.join()
            thread_keyboard_listening = None
    except Exception as e:
        error_count += 1
    # 销毁窗口
    if root:
        root.destroy()

#关闭程序操作 同上用法
def check_processes():
    btn = root.winfo_children()[0]
    btn.config(state=tk.NORMAL)

class ConsoleRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END,string)
        self.text_widget.see(tk.END)  # 自动滚动到最新内容处
if __name__ == "__main__":
    try:
        start_server_and_gui()
    except KeyboardInterrupt:
        log("程序被用户手动中断，正在进行清理操作...")
        # 在这里可以添加进一步的清理资源、关闭进程等操作
        if root:
            root.destroy()
