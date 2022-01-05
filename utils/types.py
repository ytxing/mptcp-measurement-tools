# ytxing: 这里用来定义不同的class，方便在dataDerver(DS)服务器和collectServer(CS)以及客户端(C)程序里面引用
# ytxing: for example
import random
import string


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
        ramdomStr = string_generator(size=self.size - len(msgStr), chars=string.digits)
        return msgStr + ramdomStr
    
def readMsgStr(msgStr: str) -> Message:
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

if __name__ == '__main__':
    msg = Message(1, 1, 1220)
    print(msg.msg.encode())
    print(msg.msg)
    print(len(msg.msg.encode()))