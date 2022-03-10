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

# 获取本'地主机名
# host = '192.168.5.136'
host = '127.0.0.1'

# 设置端口号
port = 9999

# 连接服务，指定主机和端口
s.connect((host, port))
l = 0
start = time.time()
while True:

    recvdStr = s.recv(1024*1024*10).decode()
    l += len(recvdStr)
    print(l)
    if len(recvdStr) == 0:
        end = time.time()
        print(end - start)
        break


# print(s.getsockopt(socket.SOL_TCP, socket.TCP_MAXSEG))
# read_t = readingThread(s)
# send_t = sendingThread(s)
# read_t.start()
# send_t.start()
# read_t.join()
# send_t.join()

