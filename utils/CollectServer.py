import socket
import threading
import sys
from . import CollectServerScript
import os

# "IP", 0 : available; 1: unavailable
dataServerIPs = {}
congestionControl = ["bbr", "olia", "cubic"]
scheduler = ["roundrobin", "blest", "default", "redundant"]
lock = threading.Lock()
threads = {}
toJoin = []


def joinFinishedThreads():
	""" Join threads whose connection is closed """
	while len(toJoin) > 0:
		threadToJoinId = toJoin.pop()
		threads[threadToJoinId].join()
		del threads[threadToJoinId]


class HandleConnectionFromClient(threading.Thread):
	def __init__(self, connection, clientADDR, id):
		threading.Thread.__init__(self)
		self.codeMode = "utf-8"
		self.connection = connection
		self.client_address = clientADDR
		self.id = id
		self.serverIP = ''

	def run(self):
		closeFlag = 0
		for i in range(len(congestionControl)):
			for j in range(len(scheduler)):
				testComb = congestionControl[i] + ' ' + scheduler[j]
				lock.acquire()
				for IP, val in dataServerIPs.items():
					if val == 0:
						testComb = testComb + ' ' + IP
						self.serverIP = IP
						dataServerIPs[IP] = 1
				lock.release()
				self.connection.send(testComb.encode(self.codeMode))
				msg = self.connection.recv(1024).decode(self.codeMode)
				if msg == "NEXT":
					continue
				else:
					#TODO 每次实验结束后要创建对应的文件夹以便接受对应的实验文件
					msg = "DIRECTORY"
					self.connection.send(msg.encode(self.codeMode))
					directory = self.connection.recv(1024).decode(self.codeMode)
					homePath = os.path.expandvars('$HOME')
					directory = homePath + '/' + directory
					CollectServerScript.checkDirectoryExist(directory)
					print(self.id, ": Closing connection, something wrong with client")
					self.connection.close()
					lock.acquire()
					dataServerIPs[self.serverIP] = 0
					lock.release()
					closeFlag = 1
					toJoin.append(self.id)

		if closeFlag == 0:
			# TODO 每次实验结束后要创建对应的文件夹以便接受对应的实验文件
			msg = "DIRECTORY"
			self.connection.send(msg.encode(self.codeMode))
			directory = self.connection.recv(1024).decode(self.codeMode)
			homePath = os.path.expandvars('$HOME')
			directory = homePath + '/' + directory
			CollectServerScript.checkDirectoryExist(directory)
			print(self.id, ": Closing connection")
			self.connection.close()
			lock.acquire()
			dataServerIPs[self.serverIP] = 0
			lock.release()
			toJoin.append(self.id)


class TCPServer:
	def __init__(self, serverNums):
		self.collectServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.collectServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.collectServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.collectServerSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		self.collectServerSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 0)
		self.serverADDR = ("0.0.0.0", 8000)
		self.collectServerSocket.bind(self.serverADDR)
		self.collectServerSocket.listen(serverNums)
		self.connID = 0

	def startEXP(self):
		while True:
			clientSocket, clientADDR = self.collectServerSocket.accept()
			thread = HandleConnectionFromClient(clientSocket, clientADDR, self.connID)
			threads[self.connID] = thread
			self.connID += 1
			thread.start()
			joinFinishedThreads()


if __name__ == "__main__":
	print("Please input the data server IPs: ")
	for i in range(1, len(sys.argv)):
		dataServerIPs.update({sys.argv[i]: 0})
	serverNums = len(dataServerIPs)
	collectServer = TCPServer(serverNums)
	collectServer.startEXP()
