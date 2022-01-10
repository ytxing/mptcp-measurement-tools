# ytxing: 这里用来定义不同的class，方便在dataDerver(DS)服务器和collectServer(CS)以及客户端(C)程序里面引用
# ytxing: for example
import datetime
import random
import socket
import string
from queue import Queue
import re
import threading
from typing import Tuple

APP_READ_BUFFER_SIZE = 2048 * 1024 
ENCODING = 'utf-8'

def int2HexStr(i) -> str:
    return format(int(i), 'x')

def MSoMPrint(*args, **kwargs):
    # ytxing: TODO 保存这些在某个文件里
   print('[MSoM][{}] '.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")), end='')
   return print(*args, **kwargs)

def string_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def getExpType(role: str, type: str) -> int:
    t = 0
    if role == 'c':
        t += 0 << 2
    elif role == 's':
        t += 1 << 2
    else:
        print('getExpType: invalid role')
        return None
    
    if type == 'ping':
        t += 0
    elif type == 'bulk':
        t += 1
    elif type == 'stream':
        t += 2
    elif type == 'siri':
        t += 3
    else:
        print('getExpType: invalid type')
        return None

    return t

class Message():
    '''
    structure:

    |   0   |   0   |  0 0 0   |  0 0 0  | 0 ~ 255 (0xff)

    |  good |  end  |   type   |  unused |

    |  type: server:1/client:0 + Ping:00 / Bulk:01 / Streaming: 10 / Siri:11
    '''
    def __init__(self, good=1, end=0, type=0b000, reqTrunkSize=0x00000000, size=10, copyString=None):
        self.good: bool = good
        self.end: bool = end
        self.type = type
        self.ctrl = self.generateCtrl()
        self.reqTrunkSize: int = reqTrunkSize
        self.trunk: str = None
        if copyString != None:
            self.trunk = '[{:02x}'.format(self.ctrl) + copyString + ']'
            self.size = len(self.trunk)
        else:
            self.size = size
            self.trunk = self.generateMsgStr()


    def generateCtrl(self) -> int:
        #   0   |   0   |  0 0 0   |  0 0 0  | 0 ~ 255
        #  good |  end  |   type   |  unused |
        #  type: server:1/client:0 + Ping:00 / Bulk:01 / Streaming: 10 / Siri:11
        return (self.type << 3) + (self.end << 6) + (self.good << 7)

    def generateMsgStr(self) -> str:
        ctrlStr = '{:02x}'.format(self.ctrl)
        reqTrunkSizeStr = '{:08x}'.format(self.reqTrunkSize)
        # if self.end:
        #     return '[' + ctrlStr + ']'
        ramdomStr = string_generator(max(0, self.size - len(ctrlStr) - len(reqTrunkSizeStr) - 2), chars=string.digits)
        return '[' + ctrlStr + reqTrunkSizeStr + ramdomStr + ']'

def unpackMsgStr(msgStr: str) -> Message:
    if len(msgStr) < 5:
        return None
    if msgStr[0] != '[' or msgStr[-1] != ']':
        return None
    msg = msgStr[1:-1]
    ctrl = int(msg[0:2], 16)
    good = 0b1 & (ctrl >> 7)
    end = 0b1 & (ctrl >> 6)
    type = 0b111 & (ctrl >> 3)
    reqTrunkSize = 0xffff & (int(msg[2:10], 16))
    randomStr = msg[3:]
    return Message(good=good, end=end, reqTrunkSize=reqTrunkSize, type=type, copyString=randomStr)

class ExpNode():
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

    def getOneMsg(self, bufferedStr: str) -> Tuple[Message, str] :
        currentMsgStr = ''
        oneMsgGot = False
        s = bufferedStr
        msgCheckFlag = False
        while len(s) > 0 and not oneMsgGot:
                c = s[0]

                if c == '[':
                    msgCheckFlag = True
                    currentMsgStr += c
                elif c == ']' and msgCheckFlag:
                    msgCheckFlag = False
                    currentMsgStr += c

                    msg = unpackMsgStr(currentMsgStr)
                    if msg == None:
                        return None, bufferedStr
                    oneMsgGot = True
                    currentMsgStr = ''
                elif msgCheckFlag:
                    currentMsgStr += c
        
                s = s[1:]
        
        if not oneMsgGot:
            return None, bufferedStr
        else:
            return msg, s

    def queueAllMsg(self, bufferedStr: str) -> str:
        s = bufferedStr
        while len(s) > 0:
            msg, s = self.getOneMsg(s)
            if msg == None:
                return s
            else:
                print(msg.trunk, '+', s)
                self.putMsgInQueue(Message(good=1, end=msg.end, size=msg.reqTrunkSize))
                self.recvingThreadEnd = msg.end
                MSoMPrint('ID:{} get a msg, put in queue End:{} Size:{} '.format(self.id, self.recvingThreadEnd, msg.reqTrunkSize))
        return s

    def putMsgInQueue(self, msg: Message):
        self.queueLock.acquire()
        self.sendQueue.put(msg)
        self.queueLock.release()

    def getMsgFromQueue(self) -> Message:
        try:
            msg = self.sendQueue.get(timeout=self.waitTimer)
            return msg
        except:
            raise

    def recvData(self):
        pass 
    def sendData(self):
        pass
    def start(self):
        pass

if __name__ == '__main__':
    # good = 1
    # end = 1
    # type = 7
    # for i in range(good + 1):
    #     for j in range(end + 1):
    #         for k in range(type + 1):
    #             msg = Message(good, end, type, size=random.randint(0, 1200))
    #             unpackedMsg = unpackMsgStr(msg.trunk)
    #             if msg.ctrl == unpackedMsg.ctrl:
    #                 continue
    #             print('???')
    # print(bin(getExpType('c', 'siri')))
    msg = Message(1, 1, 0b011, size=20, reqTrunkSize=255)
    print(msg.trunk)
    print('ctrl', bin(msg.ctrl))
    print('len', len(msg.trunk))
    print(bin(unpackMsgStr(msg.trunk).ctrl))
    print('reqlen', unpackMsgStr(msg.trunk).reqTrunkSize)