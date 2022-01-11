import argparse
import datetime
import random
import socket
import string
import time
import types
from mytools import *
class Client(ExpNode):
    def __init__(self, id: str, connection: socket.socket, type:str, wait4Reply=True, waitTimer=10.0):
        ExpNode.__init__(self, id, connection=connection, role='c', type=type, wait4Reply=wait4Reply, waitTimer=waitTimer)

    def recvData(self):
        # Message格式: [(good) (end) (random string)]
        MSoMPrint('ID:{} start recving data'.format(self.id))
        bufferedStr = ''
        bytesRecved = 0
        self.recvingThreadEnd = False
        while not self.forceQuit and not self.recvingThreadEnd:
            recvdStr = self.connection.recv(APP_READ_BUFFER_SIZE).decode(ENCODING)
            bufferedStr += recvdStr
            bytesRecved += len(recvdStr)
            bufferedStr = self.putAllMsgInRecvQueue(bufferedStr)

            MSoMPrint('ID:{} bytesRecved + {} = {}'.format(self.id, len(recvdStr), bytesRecved))
            # if bytesRecved >= self.trunkSize * self.round:
            #     self.recvingThreadEnd = True
            #     break
            # ytxing: TODO 这里就可以通过处理这个trunk获得各种信息 

        MSoMPrint('ID:{} stop recving data Force:{} End:{} bytesRecved:{}'.format(self.id, self.forceQuit, self.recvingThreadEnd, bytesRecved))


    def start(self):
        '''
        对于每一种Application，继承Client类并重写start函数，按照应用的要求使用putMsgInQueue()和getMsgFromQueue()来控制数据的发送和接收。
        '''
        self.recvingThread = threading.Thread(target=self.recvData)
        self.sendingThread = threading.Thread(target=self.sendData)
        self.sendingThread.start()
        self.recvingThread.start()

        # msg = Message(1, 0, self.typeCode, reqTrunkSize=100, size=1)
        # print(msg.trunk)
        # self.putMsgInSendQueue(msg)
        # msg = Message(1, 0, self.typeCode, reqTrunkSize=100, size=1)
        # print(msg.trunk)
        # self.putMsgInSendQueue(msg)
        msg = Message(1, 1, self.typeCode, reqTrunkSize=114514, size=1)
        print(msg.trunk)
        self.putMsgInSendQueue(msg)
        MSoMPrint(self.id, 'putting msg in queue type:{} ctrl:{:08b}'.format(bin(msg.type), msg.ctrl))
        time.sleep(1)

        # ytxing: TODO 实验结束时
        expDone = True
        if expDone:
            self.sendingThreadEnd = 1
            self.recvingThreadEnd = 1

        self.sendingThread.join()
        self.recvingThread.join()
        MSoMPrint('ID:{} runExp stop closing the socket'.format(self.id))
        self.connection.close()

parser = argparse.ArgumentParser(description="Msg client")
parser.add_argument("-s", "--size", type=float, help="trunk size to send for each request", default=10)
parser.add_argument("-r", "--round", type=int, help="the number of requests", default=1)
parser.add_argument("-p", "--pattern", help="traffic pattern (bulk, streaming, ping, siri)", default='bulk')

args = parser.parse_args()

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Handle reusing the same 5-tuple if the previous one is still in TIME_WAIT
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 0)

# Bind the socket to the port
server_address = ('0.0.0.0', 8001)
print("Try to connect to %s port %s" % server_address)
sock.connect(server_address)

# ytxing: TODO 这里客户端从collect_server获得当次实验的参数

client = Client('test-client', connection=sock, type='bulk')
client.start()
