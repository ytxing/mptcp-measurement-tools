import argparse
import datetime
import random
import socket
import string
import threading
import time
from mytools import *

class TestServer():
    def __init__(self, id: str, connection: socket.socket, trunkSize=10, wait4Reply=True, waitTimer=10.0):
        self.id: str = id
        self.connection: socket.socket = connection
        self.trunkSize = trunkSize
        self.wait4Reply = wait4Reply
        self.waitTimer: float = waitTimer

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
        currentMsgStr = ''
        msgCheckFlag = False
        self.recvingThreadEnd = False
        while not self.forceQuit and not self.recvingThreadEnd:
            recvdStr = self.connection.recv(APP_READ_BUFFER_SIZE).decode(ENCODING)
            if recvdStr == '':
                continue
            bufferedStr += recvdStr
            while len(bufferedStr) > 0:
                c = bufferedStr[0]

                if c == '[':
                    msgCheckFlag = True
                    currentMsgStr += c
                elif c == ']':
                    msgCheckFlag = False
                    currentMsgStr += c

                    msg = unpackMsgStr(currentMsgStr)
                    MSoMPrint('ID:{} recv a msg ctrl:{:08b} len:{}'.format(self.id, msg.ctrl, len(currentMsgStr)))
                    if msg.end == 1:
                        self.recvingThreadEnd = True
                    self.queueLock.acquire()
                    self.sendQueue.put(Message(good=1, end=msg.end, size=self.trunkSize))
                    self.queueLock.release()
                    currentMsgStr = ''
                elif msgCheckFlag == True:
                    currentMsgStr += c

                bufferedStr = bufferedStr[1:]
        
        MSoMPrint('ID:{} stop recving data Force:{} End:{}'.format(self.id, self.forceQuit, self.recvingThreadEnd))

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
                MSoMPrint('ID:{} sendData nothing to send in queue timeout, force quit'.format(self.id))
                self.forceQuit = 1
                # self.queueLock.release()

        
        MSoMPrint('ID:{} sendData stop sending data Force:{} End:{}'.format(self.id, self.forceQuit, int(self.sendingThreadEnd)))

    def putMsgInQueue(self, msg: Message):
        self.queueLock.acquire()
        self.sendQueue.put(msg)
        self.queueLock.release()

    def getMsgFromQueue(self) -> Message:
        try:
            self.queueLock.acquire()
            self.sendQueue.get(timeout=self.waitTimer)
            self.queueLock.release()
        except:
            raise

    def start(self):
        # TODO 创建并开启两个线程，初始化queue
        self.recvingThread = threading.Thread(target=self.recvData)
        self.sendingThread = threading.Thread(target=self.sendData)
        self.sendingThread.start()
        self.recvingThread.start()
        self.sendingThread.join()
        self.recvingThread.join()
        MSoMPrint('ID:{} runExp stop closing the socket'.format(self.id))
        self.connection.close()


parser = argparse.ArgumentParser(description="Msg server")
parser.add_argument("-s", "--sleep", type=float, help="sleep time between reception and sending", default=5.0)
parser.add_argument("-b", "--bytes", type=int, help="number of bytes to send and receive", default=1200)

args = parser.parse_args()

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Handle reusing the same 5-tuple if the previous one is still in TIME_WAIT
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 0)

# Bind the socket to the port
server_address = ('0.0.0.0', 8000)
MSoMPrint("Stating the server on %s port %s" % server_address)
sock.bind(server_address)

# Listen for incoming connections
sock.listen(4)

# Connection identifier

while True:
    # Wait for a connection
    MSoMPrint("Waiting for a connection on %s port %s\n" % server_address)
    connection, client_address = sock.accept()
    
    # 这里先用这个connection传输一些用于初始化TestServer的信息，用这些信息来创建下面的testServer
    conn_id = 'time-ip-note'
    testServer = TestServer(conn_id, connection, trunkSize=1200)
    testServer.start()