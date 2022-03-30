import argparse
import subprocess
import sys
import time
import threading
import tools
import HttpClient

schedulers = ['default', 'roundrobin', 'redundant']
congestion_controls = ['cubic', 'reno', 'bbr', 'lia', 'olia']
resolutions = ['1920x1080_8000k', '3840x2160_12000k']
exp_types = ['bulk', 'ping', 'stream']
accesses = ["multipath", "wlan", "lte"]

# server_SSH_port = "1822"
# server_IP = "211.86.152.184"

server_SSH_port = "22"
server_IP = "47.100.85.48"

server_user = "libserver"
server_root = "root"

def setCongestionControl(congestion_control):
	cmd = "ssh -p " + server_SSH_port + ' ' + server_root + '@' + server_IP + " sudo sysctl net.ipv4.tcp_congestion_control=" + congestion_control
	if subprocess.call(cmd, shell = True):
		raise Exception("{} failed".format(cmd))

def setScheduler(scheduler):
	cmd = "ssh -p " + server_SSH_port + ' ' + server_root + '@' + server_IP + " sudo sysctl net.mptcp.mptcp_scheduler=" + scheduler
	if subprocess.call(cmd, shell = True):
		raise Exception("{} failed".format(cmd))

# #回显拥塞控制算法
# def getCongestionControl() -> str:
# 	cmd = "ssh -p " + server_SSH_port + ' ' + server_root + '@' + server_IP + " sudo sysctl net.ipv4.tcp_congestion_control"
# 	p = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
# 	buffer = p.stdout.read().decode()
# 	buffer = buffer.split()[-1]
# 	congestionControl = str(buffer)
# 	return congestionControl

# #回显调度算法
# def getScheduler() -> str:
# 	cmd = "ssh -p " + server_SSH_port + ' ' + server_root + '@' + server_IP + " sudo sysctl net.mptcp.mptcp_scheduler"
# 	p = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
# 	buffer = p.stdout.read().decode()
# 	buffer = buffer.split()[-1]
# 	scheduler = str(buffer)
# 	return scheduler

def setQdisc(congestion_control):
	if congestion_control == "bbr":
		cmd = "ssh -p " + server_SSH_port + ' ' + server_root + '@' + server_IP + " sudo sysctl net.core.default_qdisc=fq"
	else:
		cmd = "ssh -p " + server_SSH_port + ' ' + server_root + '@' + server_IP + " sudo sysctl net.core.default_qdisc=pfifo_fast"
	if subprocess.call(cmd, shell = True):
		raise Exception("{} failed".format(cmd))

def nicControl(nic_name, type):
	cmd = "echo a | sudo ifconfig " + nic_name + ' ' + type
	if subprocess.call(cmd, shell = True):
		raise Exception("{} failed".format(cmd))



if __name__ == '__main__':
	while True:
		#setCongestionControl(congestion_control)
		#setScheduler(scheduler)
		#setQdisc(congestion_control)
		# nicControl("eth0", "down")
		# 接收命令行参数
		parser = argparse.ArgumentParser()
		parser.add_argument('--test', help = 'run for test', action = 'store_true', default = False)
		parser.add_argument('-u', '--url', help = 'url')

		args = parser.parse_args()
		if not args.url:
			print("url is required (http://xxx.xxx.xxx.xxx:port)")
			sys.exit(1)
		url = args.url
		if args.test:
			print("run for test")
			access = 'none'
			for type in exp_types:
				if type != "stream":
					exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
					exp_id = "log_"
					exp_id += "_".join([exp_time, access, type])
					HttpClient.startExperiment(url, type, "./log-{}".format(time.strftime("%Y-%m-%d", time.localtime())), exp_id)
				else:
					for resolution in resolutions:
						exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
						exp_id = "log_"
						exp_id += "_".join([exp_time, access, type, resolution])
						HttpClient.startExperiment(url, type, "./log-{}".format(time.strftime("%Y-%m-%d", time.localtime())), exp_id, r = resolution)
			break

		config = tools.getConfigFromFile('nic_setup.config')
		if config == None:
			print("need a config file")
			sys.exit(1)
		for key in config:
			if not key in [nic_lte, nic_wlan, wifi_ssid, wifi_password]:
				print("{} is not a valid access".format(key))
				sys.exit(1)
			if key == "nic_lte":
				nic_lte = config[key]
			elif key == "nic_wlan":
				nic_wlan = config[key]
			elif key == "wifi_ssid":
				wifi_ssid = config[key]
			elif key == "wifi_password":
				wifi_password = config[key]

		for access in accesses:
			if access == "multipath":
				nicControl(nic_lte, "up")
				nicControl(nic_wlan, "up")
				time.sleep(5)
				cmd = "sudo nmcli dev wifi connect '{}' password '{}' ifname {}".format(wifi_ssid, wifi_password, nic_wlan)
				if subprocess.call(cmd, shell = True):
					raise Exception("{} failed".format(cmd))
			elif access == "lte":
				nicControl(nic_lte, "up")
				nicControl(nic_wlan, "down")
			else:
				nicControl(nic_lte, "down")
				nicControl(nic_wlan, "up")
				time.sleep(5)
				cmd = "sudo nmcli dev wifi connect '{}' password '{}' ifname {}".format(wifi_ssid, wifi_password, nic_wlan)
				if subprocess.call(cmd, shell = True):
					raise Exception("{} failed".format(cmd))
			time.sleep(20)


			for type in exp_types:
				if type != "stream":
					exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
					exp_id = "log_"
					exp_id += "_".join([exp_time, access, type])
					HttpClient.startExperiment(type, "./log-{}".format(time.strftime("%Y-%m-%d", time.localtime())), exp_id)
				else:
					for resolution in resolutions:
						exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
						exp_id = "log_"
						exp_id += "_".join([exp_time, access, type, resolution])
						HttpClient.startExperiment(type, "./log-{}".format(time.strftime("%Y-%m-%d", time.localtime())), exp_id, r = resolution)

