#ws_client.py
import asyncio
import websockets
import threading
import time
import json
import ws_qrcode
import socket
from datetime import datetime
from pynput import keyboard
import os
import sys
import re
import argparse
import psutil
from PyQt5.QtWidgets import QApplication, QWidget
stop_flag  = False
class WebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.receive_task = None
        self.loop = asyncio.new_event_loop()
        #self.stop_flag = False
        self.clients = {
            'clientId':'',
            'targetId':''
        }
        self.channel = {
            'A':[0,100],
            'B':[0,100]
        }
        self.thread = None
        asyncio.set_event_loop(self.loop)

    async def close(self):
        global stop_flag
        self.uri = None
        stop_flag = True
        self.loop.stop()
        self.loop = None
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.receive_task = None
        self.thread = None
        self.log('数据清除完毕')
        return
    def _receive_messages_helper(self):#该方法弃用
        """辅助函数，在单独线程中执行接收消息及相关处理逻辑"""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.connect_and_receive())
        except RuntimeError as e:
            if stop_flag:
                self.log("接收到关闭指令，正在关闭..,")
                return
            self.log("任务终止，循环结束")
            return
        except Exception as e:
            if stop_flag:
                self.log("接收到关闭指令，正在关闭..,")
                return
            self.log(f"接收消息线程出现异常: {e}")
    def start(self):
        try:
            asyncio.run(self.connect_and_receive())
        except Exception as e:
            if stop_flag:
                self.log("接收到关闭指令，正在关闭..,")
                return
            self.log(f"Error: {e}")
    def start_receive_thread(self):
        """启动接收消息的线程"""
        self.thread = threading.Thread(target=self._receive_messages_helper)
        self.thread.start()
        self.log("客户端正在连接：{}".format(self.uri))
    async def receive_messages(self):
        while not stop_flag:
            try:
                try:
                    #接受信息 3s后超时重新接收
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=3)
                    #self.log(message)
                except asyncio.TimeoutError:
                    #self.log("接收消息超时，准备重启接收...")
                    if stop_flag:
                        self.log("接收到关闭指令，正在关闭..,")
                        return
                    else:
                        continue
                except RuntimeError as e:
                    if stop_flag:
                        self.log("接收到关闭指令，正在关闭..,")
                        return
                    self.log("任务终止，循环结束")
                    return
                #self.log(f"从服务端接收到消息: {message}")
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    #log("接收到的消息无法解析为JSON格式")
                    continue
                if data.get('type') == 'bind' and data.get('targetId') == '':
                    self.clients['clientId'] = data.get('clientId')
                    # 假设ws_qrcode模块已正确定义，这里需要根据实际情况调整
                    ws_qrcode.generate_qrcode(
                        f"https://www.dungeon-lab.com/app-download.php#DGLAB-SOCKET#{self.uri}/{data.get('clientId')}")
                elif data.get('type') == 'bind' and data.get('targetId')!= '':
                    self.clients['targetId'] = data.get('targetId')
                elif data.get('type') == 'msg' and 'strength' in data.get('message'):
                    strength = data.get('message')
                    strength = strength.split('-')[1].split('+')
                    self.channel['A'] = [int(strength[0]), int(strength[2])]
                    self.channel['B'] = [int(strength[1]), int(strength[3])]
                    for key, value in self.channel.items():
                        channel_name = key
                        msg = '当前{}通道强度：{},强度上限：{}'.format(channel_name, self.channel[key][0], self.channel[key][1])
                        self.log(msg)
                elif data.get('type') == 'heartbeat':
                    self.log('收到心跳包')
            except websockets.ConnectionClosed:
                if stop_flag:
                    self.log("接收到关闭指令，正在关闭..,")
                    return
                # 修改此处引用异常的方式
                self.log("与服务端的WebSocket连接已关闭，尝试重新连接...")

                if await self.reconnect():
                    continue
                else:
                    return
            except websockets.ConnectionClosedOK:
                if stop_flag:
                    self.log("接收到关闭指令，正在关闭..,")
                    return
                self.log("与服务端的WebSocket连接已关闭，尝试重新连接...")
                if await self.reconnect():
                    continue
                else:
                    return
            except websockets.exceptions.ConnectionClosed:
                if stop_flag:
                    self.log("接收到关闭指令，正在关闭..,")
                    return
                self.log("与服务端的WebSocket连接已关闭，尝试重新连接...")
                if await self.reconnect():
                    continue
                else:
                    return
            except RuntimeError as e:
                self.log("任务终止，循环结束")
                return
            except Exception as e:
                self.log(f"接收消息出现异常: {e}")
                break

    async def reconnect(self):
        consecutive_failures = 0  # 记录连续连接失败次数
        max_consecutive_failures = 5  # 最大连续失败次数，可根据实际情况调整
        while True:
            try:
                self.websocket = await websockets.connect(self.uri)
                self.log("重新连接成功，继续接收消息...")
                consecutive_failures = 0  # 重置连续失败次数
                return True
            except websockets.exceptions.ConnectionClosedError as e:
                self.log("无法连接到服务器,正在尝试重新连接...")
                consecutive_failures += 1
                if stop_flag:
                    self.log("接收到关闭指令，正在关闭..,")
                    return False
                if consecutive_failures == max_consecutive_failures:
                    self.log('重连次数上限，程序退出')
                    return False
            except websockets.ConnectionClosedError:  # 修改此处引用异常的方式
                self.log("重新连接失败，3秒后再次尝试...")
                consecutive_failures += 1
                if stop_flag:
                    self.log("接收到关闭指令，正在关闭..,")
                    return False
                if consecutive_failures == max_consecutive_failures:
                    self.log('重连次数上限，程序退出')
                    return False
            except Exception as e:
                self.log(f"重新连接出现异常: {e}")
                consecutive_failures += 1
                if stop_flag:
                    self.log("接收到关闭指令，正在关闭..,")
                    return False
                if consecutive_failures == max_consecutive_failures:
                    self.log('重连次数上限，程序退出')
                    return False

    async def connect_and_receive(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            self.log("已连接到服务端，开始接收消息...")
            self.receive_task = asyncio.create_task(self.receive_messages())
            await self.receive_task
            return
        except websockets.ConnectionClosedError:  # 修改此处引用异常的方式
            self.log("初始连接失败，尝试重新连接...")
            await self.reconnect()
        except Exception as e:
            self.log(f"初始连接出现其他异常: {e}")
            await self.reconnect()

    def send_message(self,message):
        try:
            asyncio.run_coroutine_threadsafe(self.websocket.send(message), self.loop).result()
            #self.log(f"已向服务端发送消息: {message}")
        except websockets.ConnectionClosedError:
            self.log("与服务端的连接已关闭，无法发送消息，尝试重新连接...")
            asyncio.run_coroutine_threadsafe(self.reconnect(), self.loop)
        except Exception as e:
            self.log(f"发送消息出现异常: {e}")

    def handle_message(self,data):
        try:
            send_data_l = data
            send_data_l['clientId'] = self.clients['clientId']
            send_data_l['targetId'] = self.clients['targetId']

            if send_data_l['clientId'] == '' or send_data_l['targetId'] == '':
                self.log('未连接到APP终端!')
                return
            elif send_data_l['channel'] not in self.channel:
                self.log('无该通道')
                return
            if send_data_l.get('strength') is not None and send_data_l['type'] in [1,2,3]:
                new_strength = send_data_l['strength'] + self.channel[send_data_l['channel']][0] if send_data_l['type'] == 3 else send_data_l['strength']
                if send_data_l['strength'] > self.channel[send_data_l['channel']][1] or new_strength > \
                        self.channel[send_data_l['channel']][1]:
                    self.log('超出APP终端软上限！')
                else:
                    if send_data_l['channel'] == 'A':
                        send_data_l['channel'] = 1
                    elif send_data_l['channel'] == 'B':
                        send_data_l['channel'] = 2
                    else:
                        send_data_l['channel'] = 1
                    self.send_message(json.dumps(send_data_l))
            elif send_data_l['type'] == 'clientMsg':
                self.send_message(json.dumps(send_data_l))
            else:
                self.send_message(json.dumps(send_data_l))
        except json.JSONDecodeError:
            self.log('解析数据出错')

    @staticmethod
    def log(msg_a):
        message = '[{}] Client: {}'.format(datetime.now().strftime('%H:%M:%S'), msg_a)
        print(message)

# 定义全局变量用于保存钩子句柄
keyboard_hook = None
#获取本地IP
def get_local_ip():
    try:
        # 创建一个UDP套接字
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # 连接到一个不存在的地址，这样不会真正发送数据
        s.connect(('8.8.8.8', 80))

        # 获取本地IP地址
        local_ip = s.getsockname()

        # 关闭套接字
        s.close()
    except Exception as e:
        print(f"Error occurred: {e}")
        local_ip = None

    return local_ip[0]

if __name__ == "__main__":
    uri = "ws://{}:1145".format(get_local_ip())
    parser = argparse.ArgumentParser(description='WebSocket客户端启动参数说明')
    parser.add_argument('-w', '--ws', type=str, help='客户端连接地址', required=False, default=uri)
    args = parser.parse_args()

     # 替换为实际的WebSocket服务端地址
    client = WebSocketClient(args.ws)
    client.start_receive_thread()

    #提升优先级至高优先
    current_process = psutil.Process(os.getpid())
    current_process.nice(psutil.HIGH_PRIORITY_CLASS)
    #listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    #listener.start()
    #try:
        #while listener.is_alive():
            #if stop_listening:
                #listener.stop()
                #break
    #except KeyboardInterrupt:
        # 在这里可以添加进一步的清理资源、关闭进程等操作
        #client.stop_flag = True
        #client.log("用户手动关闭，3s后与服务器断开连接")
        #listener.stop()
