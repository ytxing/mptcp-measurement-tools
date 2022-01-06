# ytxing: 这里用来定义不同的class，方便在dataDerver(DS)服务器和collectServer(CS)以及客户端(C)程序里面引用
# ytxing: for example
import datetime
import random
import socket
import string
from queue import Queue
import re
import threading

READ_BUFFER_SIZE = 2048
ENCODING = 'ascii'
class readingThread (threading.Thread):
    def __init__(self, connection: socket):
        threading.Thread.__init__(self)
        self.connection = connection
    def run(self):
        while True:
            msg = self.connection.recv(READ_BUFFER_SIZE).decode(ENCODING)
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

def MSoMPrint(*args, **kwargs):
   print('[MSoM][{}] '.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")), end='')
   return print(*args, **kwargs)

def string_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

class Message():
    def __init__(self, good=1, end=0, size=None, randomString=None):
        self.round = round
        self.good = good
        self.end = end
        if size == None:
            self.msg = str(self.good) + str(self.end) + str(randomString)
            self.size = len(self.msg)
        else:
            self.size = size
            self.msg = self.generateMsgStr()

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

def readRawMsgStr(msgStr: str) -> Queue:
    q = Queue(-1)
    p = re.compile(r'\[(.*?)\]')
    raw_replies = re.findall(p, msgStr)
    for raw_reply in raw_replies:
        q.put(unpackMsgStr(raw_reply))
    return q

class Request():
    def __init__(self, trunk_size, round, wait_for_reply_timeout):
        self.trunk_size = trunk_size
        self.round = round
        self.wait_for_reply_timeout = wait_for_reply_timeout

    def request(self):
        return self

if __name__ == '__main__':
    msg = Message(1, 1, 1220)
    print(msg.msg)
    print(len(msg.msg.encode()))