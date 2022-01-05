import socket
import threading
import sys


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
	def __init__(self, connection, client_address, id):
		threading.Thread.__init__(self)
		self.codeMode = "utf-8"
		self.connection = connection
		self.client_address = client_address
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
					print(self.id, ": Closing connection, something wrong with client")
					endMsg = "END"
					self.connection.send(endMsg.encode(self.codeMode))
					self.connection.close()
					lock.acquire()
					dataServerIPs[self.serverIP] = 0
					lock.release()
					closeFlag = 1
					toJoin.append(self.id)

		if closeFlag == 0:
			print(self.id, ": Closing connection")
			endMsg = "END"
			self.connection.send(endMsg.encode(self.codeMode))
			self.connection.close()
			lock.acquire()
			dataServerIPs[self.serverIP] = 0
			lock.release()
			toJoin.append(self.id)




class TCPServer(object):
	def __init__(self, serverNums):
		self.collectServerSocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
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
