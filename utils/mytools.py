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

def bin2Str(b) -> str:
    return format(int(b), 'b')

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

    |   0   |   0   |  0 0 0   |  0 0 0  | 0 ~ 255

    |  good |  end  |   type   |  unused |

    |  type: server:1/client:0 + Ping:00 / Bulk:01 / Streaming: 10 / Siri:11
    '''
    def __init__(self, good=1, end=0, type=0b000, size=10, copyString=None):
        self.good: bool = good
        self.end: bool = end
        self.type = type
        self.ctrl = self.generateCtrl()
        self.trunk: str = None
        if copyString != None:
            self.trunk = '[{:03}'.format(self.ctrl) + copyString + ']'
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
        ctrlStr = '{:03}'.format(self.ctrl)
        if self.end:
            return '[' + ctrlStr + ']'
        ramdomStr = string_generator(max(0, self.size - len(ctrlStr) - 2), chars=string.digits)
        return '[' + ctrlStr + ramdomStr + ']'

def unpackMsgStr(msgStr: str) -> Message:
    if len(msgStr) < 5:
        return None
    if msgStr[0] != '[' or msgStr[-1] != ']':
        return None
    msg = msgStr[1:-1]
    ctrl = int(bin2Str(msg[0:3]), 2)
    good = 0b1 & (ctrl >> 7)
    end = 0b1 & (ctrl >> 6)
    type = 0b111 & (ctrl >> 3)
    randomStr = msg[3:]
    return Message(good=good, end=end, type=type, copyString=randomStr)

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
    print(bin(getExpType('c', 'siri')))
    # msg = Message(1, 1, 0b011, size=10)
    # print(msg.trunk)
    # print(msg.ctrl)
    # print(bin(unpackMsgStr(msg.trunk).ctrl))