import keyboard
import json
import os
import sys

stop_listen = False
class KeyBindingHandler:
    def __init__(self, client):
        self.client = client
        self.listener_running = False
        self.load_and_bind_key_bindings()

    def load_and_bind_key_bindings(self):
        """
        从配置文件加载键绑定信息，并进行热键绑定
        """
        # 获取可执行文件所在目录（对于cx_Freeze打包后的情况）
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(base_dir, "data", "key_bindings.json")
         # 可根据实际情况修改文件路径
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                data_list = json.loads(file.read())
                if isinstance(data_list, list):
                    for item in data_list:
                        if isinstance(item, dict):
                            hotkey_str = item.get('key')
                            data = item.get('data')
                            self.bind_hotkey(hotkey_str, data)
    def bind_hotkey(self, hotkey_str, data):
        """
        使用keyboard库的add_hotkey方法绑定单个热键，当热键触发时调用client.handle_message并传递对应数据
        """
        keyboard.add_hotkey(hotkey_str, lambda: self.client.handle_message(data))
    def start_listening(self):
        """
        启动键盘监听
        """
        keyboard.hook(self._keyboard_event_handler)

    def stop_listening(self):
        """
        停止键盘监听
        """
        keyboard.unhook_all()

    def _keyboard_event_handler(self, event):
        """
        键盘事件处理函数，目前为空实现，可根据需要添加额外的键盘事件处理逻辑
        """
        pass