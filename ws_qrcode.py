#ws_qrcode.py
import qrcode
from PIL import Image, ImageTk
import threading
import tkinter as tk
import os
import sys
# 生成二维码并保存为文件
def generate_qrcode(url, file_path = 'qrcode.png'):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    # 获取可执行文件所在目录（对于cx_Freeze打包后的情况）
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    file = os.path.join(base_dir, "data", file_path)
    img.save(file)