import argparse
import datetime
import random
import socket
import string
import threading
import time
from mytools import *

class TestServer(ExpNode):
    def __init__(self, id: str, connection: socket.socket, wait4Reply=True, waitTimer=10.0):
        ExpNode.__init__(self, id, connection=connection, role='s', wait4Reply=wait4Reply, waitTimer=waitTimer)

    def recvData(self):
        MSoMPrint('ID:{} start recving data'.format(self.id))
        bufferedStr = ''
        self.recvingThreadEnd = False
        while not self.forceQuit and not self.recvingThreadEnd:
            recvdStr = self.connection.recv(APP_READ_BUFFER_SIZE).decode(ENCODING)
            bufferedStr += recvdStr
            bufferedStr = self.putAllMsgInRecvQueue(bufferedStr)

        MSoMPrint('ID:{} stop recving data Force:{} End:{}'.format(self.id, self.forceQuit, self.recvingThreadEnd))

    def replyMsg(self):
        replyEnd = False
        while not replyEnd:
            msg = self.getMsgFromRecvQueue()
            if msg != None:
                self.putMsgInSendQueue(Message(good=msg.good, end=msg.end, type=msg.type, reqTrunkSize=0, size=msg.reqTrunkSize))
                print(msg.reqTrunkSize)
                replyEnd = msg.end
            

    def start(self):
        # TODO 创建并开启两个线程，初始化queue
        self.recvingThread = threading.Thread(target=self.recvData)
        self.sendingThread = threading.Thread(target=self.sendData)
        self.sendingThread.start()
        self.recvingThread.start()

        self.replyMsg()

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
server_address = ('0.0.0.0', 8001)
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
    testServer = TestServer(conn_id, connection)
    testServer.start()