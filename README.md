## 郊狼 按键惩罚
![主程序页面](/image.png)

### 说明

通过绑定热键发送波形数据到手机客户端APP以实现按键惩罚，通过系统管理员启动可在其他应用上实现触发热键操作

### 安装
准备文件：
1. Python 3
将源代码下载好后解压，点击install.bat会帮你安装所需要的库文件

### 已知BUG

1. 服务端和客户端关闭时会卡程序
2. 某些情况下，按键互动发送波形后无法正常运作
- [x] 已修复 配置按键那个窗口有BUG，打开后关了就别开了要不然程序直接崩=-=，后面我再修

### 食用方法

1. 用管理员运行start.bat或者使用powershell运行下行命令
```bash
python main.py
```
2. 进入主界面后，点击启动服务端，接着点击启动客户端，启动完成后点击显示二维码会弹出socket控制的二维码出来
3. 然后就可以打开你的手机端app扫码连接了
>注意：
> 1. 在设计的时候服务端确实是可以通过修改/data/config.json中的ip来自定义IP的，以此可以实现公网监听，也就不需要保持同一局域网下进行扫码
> 2. 如果只是自己用的话请不要动/data/config.json的字符，程序会检测当前局域网IP自动启动，只需要保持同一局域网即可
4. 连接完成后就可以启动键盘监听了！

### 未来开发功能
- [ ] 服务端模式 
- 该功能可以实现一对多或者多对一的模式，你想要享受被十个人同时控制嘛喵（）
- [ ] 按键随机波形
- 同一个按键不同的波形，诶嘿~或者程序随机生成波形
- [ ] 强度自动增加/减少
- 解放双手，不用自己加强度了 噢耶

### 参考文档

- [郊狼情趣脉冲主机V3](https://github.com/DG-LAB-OPENSOURCE/DG-LAB-OPENSOURCE/blob/main/coyote/v3/README_V3.md)
- [郊狼 SOCKET 控制-控制端开源](https://github.com/DG-LAB-OPENSOURCE/DG-LAB-OPENSOURCE/blob/main/socket/README.md)

> 有BUG可以提交到issues或者在bilibili视频底下评论
