import argparse
import datetime
import random
import socket
import string
import threading
import time
from mytools import *

BUFFER_SIZE = 2048
ENCODING = 'ascii'

threads = {}
to_join = []

parser = argparse.ArgumentParser(description="Msg server")
parser.add_argument("-s", "--sleep", type=float, help="sleep time between reception and sending", default=5.0)
parser.add_argument("-b", "--bytes", type=int, help="number of bytes to send and receive", default=1200)

args = parser.parse_args()

def string_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


'''
ytxing: 
所有的request handler都用run来启动，
服务器根据类型不同可能需要根据客户端的reply来触发继续发送(Ping, Streaming?, Interactive),
有些不管reply一直发送
'''
class BulkRequestHandler():
    def __init__(self, size, connection: socket, id):
        self.size = size
        self.connection = connection
        self.id = id

    def run(self) -> int:
        bulk = Message(size=self.size).msg
        self.connection.sendall(bulk.encode(ENCODING))
        raw_reply = self.connection.recv(BUFFER_SIZE).decode(ENCODING)
        reply = readMsgStr(raw_reply)
        success = reply.good and reply.end
        MSoMPrint(self.id, ": Closing connection")
        # 是否构建reply具体内容，确认后再close
        self.connection.close()
        return success

class InteractiveRequestHandler():
    def __init__(self, connection, id):
        self.size = 10
        self.round = 10
        self.connection = connection
        self.id = id
        # self.avg_round_trip_time = None
        # self.total_round_trip_time = None

    def run(self) -> int:
        '''
        Interactive:1. the server sends one msg to the client
                    2. the server waits for reply
                    3. when receiving the reply form the client, go back to 1 and again
        '''
        # 如果出现异常考虑使用try语句
        success = 1
        for _ in range(round):
            msg = Message(size=self.size).msg
            self.connection.sendall(msg.encode(ENCODING))
            raw_reply = self.connection.recv(BUFFER_SIZE).decode(ENCODING)
            reply = readMsgStr(raw_reply)
            if reply.good == 1 and reply.end == 0:
                continue
            if reply.end == 1:
                break
            if reply.good != 1:
                success = 0
                break
        
        MSoMPrint(self.id, ": Closing connection")
        # 是否构建reply具体内容，确认后再close
        self.connection.close()
        return success

class PingRequestHandler():
    def __init__(self, connection, id):
        self.size = 10
        self.round = 10
        self.connection = connection
        self.id = id
        # self.avg_round_trip_time = None
        # self.total_round_trip_time = None

    def run(self) -> int:
        '''
        Ping: 1. the server sends one msg to the client
              2. the server waits for reply
              3. when receiving the reply form the client, go back to 1 and again
        '''
        # 如果出现异常考虑使用try语句
        success = 1
        for _ in range(round):
            msg = Message(size=self.size).msg
            self.connection.sendall(msg.encode(ENCODING))
            raw_reply = self.connection.recv(BUFFER_SIZE).decode(ENCODING)
            reply = readMsgStr(raw_reply)
            if reply.good == 1 and reply.end == 0:
                continue
            if reply.end == 1:
                break
            if reply.good != 1:
                success = 0
                break
        
        MSoMPrint(self.id, ": Closing connection")
        # 是否构建reply具体内容，确认后再close
        self.connection.close()
        return success

class StreamingRequestHandler():
    def __init__(self, id, size, connection, wait_for_reply=True, wait_timeout=5):
        self.size = size
        self.connection = connection
        self.wait_for_reply = wait_for_reply
        self.wait_timeout = wait_timeout
        self.id = id

    def run(self) -> int:
        '''
        Streaming:  1. the server sends one trunk to the client
                    2. the server waits for reply
                    3. when receiving the reply form the client, go back to 1 and again
        '''
        success = 1
        request_queue = Queue(0)
        while True:
            bulk = Message(size=self.size).msg
            self.connection.sendall(bulk.encode(ENCODING))
            # ytxing: TODO 发送是一瞬间的吗？还是会阻塞进程导致接不到一个很快的reply。是不是需要用另一个线程实现发送。
            # ytxing: 这个是会的 改成线程
            raw_reply = self.connection.recv(BUFFER_SIZE).decode(ENCODING)
            reply_queue = readRawMsgStr(raw_reply)
            while not reply_queue:
                t_reply = reply_queue.get()
                request_queue.put(t_reply)
            if reply == None:
                # 如果没有收到东西会怎么样
                MSoMPrint('No reply, streaming stop')
                success = 0
                break
            if reply.good != 1:
                MSoMPrint('Streaming stop by client accidentally')
                success = 0
                break
            if reply.good == 1 and reply.end == 1:
                MSoMPrint('Streaming stop by client')
                success = 1
                break
            # if reply.good == 1 and reply.end == 0 then continue to send trunk

        MSoMPrint(self.id, "Closing connection, success:{}".format(success))
        self.connection.close()
        return success

class ClientRequest():
    def __init__(self, request_type, block_size, id, msg_size):
        self.connection = connection
        self.client_address = client_address
        self.id = id
        self.msg_size = msg_size
        self.delays = []

class HandleClientConnectionThread(threading.Thread):
    """ Handle requests given by the client """

    def __init__(self, connection, client_address, id, msg_size):
        threading.Thread.__init__(self)
        self.connection = connection
        self.client_address = client_address
        self.id = id
        self.msg_size = msg_size
        self.delays = []

    def run(self):
        try:
            MSoMPrint(self.id, ": Connection from", self.client_address)
            start_time = None
            buffer_data = ""

            # Receive the data and retransmit it
            while True:
                data = self.connection.recv(BUFFER_SIZE).decode(ENCODING)

                if len(data) == 0:
                    # Connection closed at remote; close the connection
                    break

                buffer_data += data

                if len(buffer_data) >= self.msg_size:
                    stop_time = datetime.datetime.now()
                    if start_time:
                        self.delays.append(stop_time - start_time)
                    time.sleep(args.sleep)
                    response = string_generator(size=self.msg_size, chars=string.digits)
                    start_time = datetime.datetime.now()
                    self.connection.sendall(response.encode(ENCODING))
                    buffer_data = buffer_data[self.msg_size:]

        finally:
            # Clean up the connection
            MSoMPrint(self.id, ": Closing connection")
            self.connection.close()
            MSoMPrint(self.delays)
            to_join.append(self.id)


def join_finished_threads():
    """ Join threads whose connection is closed """
    while len(to_join) > 0:
        thread_to_join_id = to_join.pop()
        threads[thread_to_join_id].join()
        del threads[thread_to_join_id]

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
conn_id = 0

while True:
    # Wait for a connection
    connection, client_address = sock.accept()
    thread = HandleClientConnectionThread(connection, client_address, conn_id, args.bytes)
    threads[conn_id] = thread
    conn_id += 1
    thread.start()
    join_finished_threads()