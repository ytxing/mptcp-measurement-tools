#!/usr/bin/python3
# 文件名：server.py

# 导入 socket、sys 模块
import socket
import sys
import threading

class readingThread (threading.Thread):
    def __init__(self, connection: socket):
        threading.Thread.__init__(self)
        self.connection = connection
    def run(self):
        while True:
            msg = self.connection.recv(2).decode('utf-8')
            print('read:', msg)
            if msg == '\\end' or msg == '':
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
serversocket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM) 

# 获取本地主机名
host = socket.gethostname()

port = 9999

# 绑定端口号
serversocket.bind(('127.0.0.1', port))

# 设置最大连接数，超过后排队
serversocket.listen(5)
print(host, port)
while True:
    clientsocket,addr = serversocket.accept()

    print("连接地址: %s" % str(addr))

    with open('/home/ytxing/mptcpwireless-measurement/test/test1000m', 'r') as f:
        trunk = f.read()
    clientsocket.sendall(trunk.encode())
    clientsocket.close()
# read_t = readingThread(clientsocket)
# send_t = sendingThread(clientsocket)
# read_t.start()
# send_t.start()
# read_t.join()
# send_t.join()