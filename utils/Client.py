import argparse
import datetime
import random
import socket
import string
import time
import types
from mytools import *
class Client(ExpNode):
    def __init__(self, id: str, connection: socket.socket, reqTrunkSize, trunkSize, round, role:str, type:str, wait4Reply=True, waitTimer=10.0):
        self.id: str = id
        self.connection: socket.socket = connection
        self.reqTrunkSize = reqTrunkSize # need to be less than 0xFFFFFFFF = 4294967295 ~= 4.2GB
        self.trunkSize = trunkSize
        self.round = round
        self.wait4Reply = wait4Reply
        self.waitTimer = waitTimer
        self.role = role
        self.type = type
        self.typeCode: int = getExpType(role, type)

        
        self.sendingThread = None
        self.recvingThread = None
        self.sendQueue = Queue(0)
        self.queueLock = threading.Lock()
        self.sendingThreadEnd = False
        self.recvingThreadEnd = False
        self.forceQuit = False # 不知道有没有用，用来强行停止线程

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
            bufferedStr = self.queueAllMsg(bufferedStr)

            MSoMPrint('ID:{} bytesRecved + {} = {}'.format(self.id, len(recvdStr), bytesRecved))
            # if bytesRecved >= self.trunkSize * self.round:
            #     self.recvingThreadEnd = True
            #     break
            # ytxing: TODO 这里就可以通过处理这个trunk获得各种信息 

        MSoMPrint('ID:{} stop recving data Force:{} End:{} bytesRecved:{}'.format(self.id, self.forceQuit, self.recvingThreadEnd, bytesRecved))
    
    def sendData(self):
        MSoMPrint('ID:{} sendData start sending data'.format(self.id))
        self.sendingThreadEnd = False
        while not self.forceQuit and not self.sendingThreadEnd:
            try:
                # self.queueLock.acquire()
                msg: Message = self.sendQueue.get(timeout=self.waitTimer)
                # self.queueLock.release()
                trunk = msg.trunk
                MSoMPrint('ID:{} sendData sending a trunk len:{}'.format(self.id, len(trunk)))
                self.connection.sendall(trunk.encode(ENCODING))
                MSoMPrint('ID:{} sendData sent a trunk len:{}'.format(self.id, len(trunk)))
                if msg.end:
                    self.sendingThreadEnd = 1
            except: 
                MSoMPrint('ID:{} sendData nothing to send in queue timeout, continue'.format(self.id))

        
        MSoMPrint('ID:{} sendData stop sending data Force:{} End:{}'.format(self.id, self.forceQuit, self.sendingThreadEnd))

    def putMsgInQueue(self, msg: Message):
        # self.queueLock.acquire()
        self.sendQueue.put(msg)
        # self.queueLock.release()

    def getMsgFromQueue(self) -> Message:
        try:
            # self.queueLock.acquire()
            self.sendQueue.get(timeout=self.waitTimer)
            # self.queueLock.release()
        except:
            raise

    def start(self):
        # 首先发送初始request给服务器，如有需要继续发送其他的

        # TODO 创建并开启两个线程，初始化queue
        self.recvingThread = threading.Thread(target=self.recvData)
        self.sendingThread = threading.Thread(target=self.sendData)
        self.sendingThread.start()
        self.recvingThread.start()

        msg = Message(1, 0, self.typeCode, reqTrunkSize=100, size=self.trunkSize)
        self.putMsgInQueue(msg)
        msg = Message(1, 0, self.typeCode, reqTrunkSize=100, size=self.trunkSize)
        self.putMsgInQueue(msg)
        msg = Message(1, 1, self.typeCode, reqTrunkSize=114514, size=self.trunkSize)
        self.putMsgInQueue(msg)
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



        return self

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

client = Client('test-client', connection=sock, trunkSize=10, round=1, role='c', type='bulk', reqTrunkSize=1200)
client.start()
