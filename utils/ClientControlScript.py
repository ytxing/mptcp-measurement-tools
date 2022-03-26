import socket
import os
import subprocess
import time
import datetime
import smtplib
from email.mime.text import MIMEText
from typing import List
from . import HttpClient
from . import tools

# 设置ssh端口
SSHPort = "22"


# 发送邮件已告知是否出现BUG,使用QQ邮箱使用SMTP发送
class EmailToSendBugInfo:
	def __init__(self, msgFrom, passWd, msgTo):
		self.msgFrom = msgFrom
		self.passWd = passWd
		self.msgTo = msgTo
		self.subject = None
		self.content = None

	def sendEmail(self, subject, content):
		self.subject = subject
		self.content = content
		msg = MIMEText(content)
		msg['Subject'] = self.subject
		msg['From'] = self.msgFrom
		msg['To'] = self.msgTo
		try:
			s = smtplib.SMTP_SSL("smtp.qq.com", 465)  # 邮件服务器及端口号
			s.login(self.msgFrom, self.passWd)
			s.sendmail(self.msgFrom, self.msgTo, msg.as_string())
		except smtplib.SMTPException as e:
			print(e)
		finally:
			s.quit()


class ConnectToCollectServer:
	# TODO 这里的location是放置的地点，运行程序前需要明确
	def __init__(self, collectServerIP, collectServerPort, dataServerPort, dataServerUserName, location,
	             collectServerUserName):
		self.codeMode = "utf-8"
		self.clientToCollectServerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.collectServerIP = collectServerIP
		self.collectServerPort = collectServerPort
		self.collectServerSSHPort = SSHPort
		self.collectServerUserName = collectServerUserName
		self.collectServerName = collectServerUserName + '@' + collectServerIP
		self.congestionControl = None
		self.scheduler = None
		self.dataServerIP = None
		self.dataServerSSHPort = SSHPort
		self.dataServerPort = dataServerPort
		self.dataServerUserName = dataServerUserName
		self.dataServerName = None
		self.toPost = []
		self.location = location
		self.directoryName = None
		self.clientDirectoryPath = None
		self.collectServerDirectoryPath = None

	def checkDirectoryExist(self, directory):
		if os.path.exists(directory):
			if not os.path.isdir(directory):
				raise Exception(directory + "is a existing file")
			else:
				os.makedirs(directory)

	def setCongestionControl(self):
		cmd = "ssh -p " + self.dataServerSSHPort + ' ' + self.dataServerName + "sudo sysctl net.ipv4.tcp_congestion_control=" + self.congestionControl
		if subprocess.call(cmd, shell = True):
			raise Exception("{} failed".format(cmd))

	def setScheduler(self):
		cmd = "ssh -p " + self.dataServerSSHPort + ' ' + self.dataServerName + "sudo sysctl net.mptcp.mptcp_scheduler=" + self.scheduler
		if subprocess.call(cmd, shell = True):
			raise Exception("{} failed".format(cmd))

	#回显拥塞控制算法
	def getCongestionControl(self) -> str:
		cmd = "ssh - p " + self.dataServerSSHPort + ' ' + self.dataServerName + "sudo sysctl net.ipv4.tcp_congestion_control"
		p = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
		congestionControl = p.stdout.read()
		congestionControl = str(congestionControl, encoding = self.codeMode)
		return congestionControl

	#回显调度算法
	def getScheduler(self) -> str:
		cmd = "ssh - p " + self.dataServerSSHPort + ' ' + self.dataServerName + "sudo sysctl net.mptcp.mptcp_scheduler"
		p = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
		scheduler = p.stdout.read()
		scheduler = str(scheduler, encoding = self.codeMode)
		return scheduler

	# 获取client的IP地址，便于在tcpdump时指定host，同时在结束实验时通过相关命令定位到指定进程
	def clientGetIpv4(self) -> List[str]:
		devnull = open(os.devnull, "w")
		p = subprocess.Popen("hostname -I", shell = True, stdout = subprocess.PIPE, stderr = devnull)
		IpAddrs = p.stdout.read()
		IpAddrs = str(IpAddrs, encoding = "UTF-8")
		IpList = IpAddrs.split(' ')
		if "\n" in IpList:
			IpList.remove("\n")
		return IpList

	# 在客户端创建对应实验的文件夹
	def createDirectory(self):
		time = datetime.datetime.utcnow().strftime('%Y%m%d%h%M%S')
		directoryName = self.location + '_' + self.congestionControl + '_' + self.scheduler + '_' + time
		self.directoryName = directoryName
		self.collectServerDirectoryPath = "/home/" + self.collectServerUserName + '/' + self.location + '_' + self.congestionControl + '_' + self.scheduler
		# cmd = "ssh -p " + self.collectServerSSHPort + ' ' + self.collectServerName + "python3 /home/a/serverScript/createFileOrDirectory.py -d " + directoryName
		# if subprocess.call(cmd, shell = True):
		# 	raise Exception("{} failed".format(cmd))
		homePath = os.path.expandvars('$HOME')
		self.checkDirectoryExist(homePath + "/EXPLog")
		directoryPath = homePath + '/EXPLog'
		self.clientDirectoryPath = directoryPath
		directoryPath = directoryPath + self.directoryName
		self.checkDirectoryExist(directoryPath)

	def createFile(self, fileName):
		file = os.path.join(fileName, self.clientDirectoryPath)
		if not os.access(file, os.F_OK):
			os.mknod(file)

	def postToCollectServer(self):
		cmd = "scp -r " + self.collectServerSSHPort + " " + self.clientDirectoryPath+ " " + self.collectServerName + ":" + self.collectServerDirectoryPath
		if subprocess.call(cmd, shell = True):
			raise Exception("{} failed".format(cmd))

	def startEXP(self):
		self.clientToCollectServerSock.connect((self.collectServerIP, self.collectServerPort))
		while True:
			expSetting = self.clientToCollectServerSock.recv(1024).decode(self.codeMode)
			if expSetting == "END":
				self.clientToCollectServerSock.close()
				break
			elif expSetting == "DIRECTORY":
				msg = self.location + '_' + self.congestionControl + '_' + self.scheduler
				self.clientToCollectServerSock.send(msg.encode(self.codeMode))
				self.postToCollectServer()
				continue
			expList = expSetting.split(' ')
			self.congestionControl = expList[0]
			self.scheduler = expList[1]
			self.dataServerIP = expList[2]
			# TODO 这里的dataServerUserName是data server的用户名，data server尽量都起一个名字，便于操作
			self.dataServerName = self.dataServerUserName + '@' + self.dataServerIP
			self.setScheduler()
			#TODO 如果长时间未成功加一个通知机制
			while self.congestionControl != self.getCongestionControl():
				self.setCongestionControl()
			while self.scheduler != self.getScheduler():
				self.setScheduler()
			self.createDirectory()
			HttpClient.startExperiment("ping", self.clientDirectoryPath + '/')
			HttpClient.startExperiment("bulk", self.clientDirectoryPath + '/')
			HttpClient.startExperiment("stream", self.clientDirectoryPath + '/')



