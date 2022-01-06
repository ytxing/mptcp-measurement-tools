#!/usr/bin/python3
# 文件名：client.py

# 导入 socket、sys 模块
import socket
import sys
import threading
import time

class readingThread (threading.Thread):
    def __init__(self, connection: socket):
        threading.Thread.__init__(self)
        self.connection = connection
    def run(self):
        while True:
            msg = self.connection.recv(2048).decode('utf-8')
            print('read:', msg)
            if msg == '\\end':
                break
        self.connection.close()

class sendingThread (threading.Thread):
    def __init__(self, connection: socket):
        threading.Thread.__init__(self)
        self.connection = connection
    def run(self):
        while True:
            msg = input('input: ')
            self.connection.sendall(msg.encode('utf-8'))
            if msg == '\\end':
                break
        self.connection.close()


# 创建 socket 对象
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

# 获取本地主机名
host = socket.gethostname() 

# 设置端口号
port = 9999

# 连接服务，指定主机和端口
s.connect((host, port))

read_t = readingThread(s)
send_t = sendingThread(s)
read_t.start()
send_t.start()
read_t.join()
send_t.join()

