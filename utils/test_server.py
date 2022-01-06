import argparse
import datetime
import random
import socket
import string
import threading
import time
from mytools import *

parser = argparse.ArgumentParser(description="Msg server")
parser.add_argument("-s", "--sleep", type=float, help="sleep time between reception and sending", default=5.0)
parser.add_argument("-b", "--bytes", type=int, help="number of bytes to send and receive", default=1200)

args = parser.parse_args()

class ClientRequest():
    def __init__(self, request_type, block_size, id, msg_size):
        self.connection = connection
        self.client_address = client_address
        self.id = id
        self.msg_size = msg_size
        self.delays = []


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
    connection, client_address = sock.accept()
    # 这里先用这个connection传输一些用于初始化TestServer的信息，用这些信息来创建下面的testServer
    conn_id = 'time-ip-note'
    testServer = TestServer(conn_id, connection, trunkSize=1200)
    testServer.runExp()