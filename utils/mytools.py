# ytxing: 这里用来定义不同的class，方便在dataDerver(DS)服务器和collectServer(CS)以及客户端(C)程序里面引用
# ytxing: for example
import datetime
import random
import socket
import string
from queue import Queue
import re
import threading

APP_READ_BUFFER_SIZE = 2048 * 1024 
ENCODING = 'utf-8'

def MSoMPrint(*args, **kwargs):
    # ytxing: TODO 保存这些在某个文件里
   print('[MSoM][{}] '.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")), end='')
   return print(*args, **kwargs)

def string_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class Message():
    def __init__(self, good=1, end=0, size=None, randomString=None):
        self.good: bool = good
        self.end: bool = end
        self.trunk: str = None 
        if end != 1:
            if size == None:
                self.trunk = str(self.good) + str(self.end) + str(randomString)
                self.size = len(self.trunk)
            else:
                self.size = size
                self.trunk = self.generateMsgStr()

    def generateMsgStr(self) -> str:
        msgStr = str(self.good) + str(self.end)
        ramdomStr = string_generator(min(0, size=self.size - len(msgStr) - 2), chars=string.digits)
        return '[' + msgStr + ramdomStr + ']'

def unpackMsgStr(msgStr: str) -> Message:
    if len(msgStr) < 2:
        return None
    good = int(msgStr[0])
    end = int(msgStr[1])
    randomStr = msgStr[2:]
    return Message(good=good, end=end, randomString=randomStr)

class Request():
    def __init__(self, trunk_size, round, wait_for_reply_timeout):
        self.trunk_size = trunk_size
        self.round = round
        self.wait_for_reply_timeout = wait_for_reply_timeout

    def request(self):
        return self

class TestServer():
    def __init__(self, id, connection: socket, trunkSize=10, wait4Reply=True, waitTimer=10.0):
        self.id = id
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
            bufferedStr += self.connection.recv(APP_READ_BUFFER_SIZE).decode(ENCODING)
            while len(bufferedStr) > 0:
                c = bufferedStr[0]

                if c == '[':
                    msgCheckFlag = True
                elif c == ']':
                    msgCheckFlag = False

                    msg = unpackMsgStr(currentMsgStr)
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
                self.queueLock.acquire()
                msg: Message = self.sendQueue.get(timeout=self.waitTimer)
                self.queueLock.release()
                if not msg.end:
                    trunk = msg.trunk
                    if trunk == None: # impossible
                        self.sendingThreadEnd = 1

                    MSoMPrint('ID:{} sendData send a trunk len:{}'.format(self.id, len(trunk)))
                    self.connection.sendall(trunk.encode(ENCODING))
                else:
                    self.sendingThreadEnd = 1
            except: 
                MSoMPrint('ID:{} sendData nothing to send in queue timeout, force quit'.format(self.id))
                self.forceQuit

        
        MSoMPrint('ID:{} sendData stop sending data Force:{} End:{}'.format(self.id, self.forceQuit, self.sendingThreadEnd))


    def runExp(self):
        # TODO 创建并开启两个线程，初始化queue
        self.recvingThread = threading.Thread(target=self.recvData)
        self.sendingThread = threading.Thread(target=self.sendData)
        self.sendQueue.put(Message(good=1, end=0, size=self.trunkSize)) # 初始化第一个发送的块
        self.sendingThread.start()
        self.recvingThread.start()
        self.sendingThread.join()
        self.recvingThread.join()
        MSoMPrint('ID:{} runExp stop closing the socket'.format(self.id))
        self.connection.close()


if __name__ == '__main__':
    msg = Message(1, 1, 1220)
    print(msg.msg)
    print(len(msg.msg.encode()))