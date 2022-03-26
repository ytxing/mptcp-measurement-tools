import subprocess
import time
import threading
import tools
import HttpClient

schedulers = ['default', 'roundrobin', 'redundant']
congestion_controls = ['cubic', 'reno', 'bbr', 'lia', 'olia']
resolutions = ['320x180_400k', '480x270_600k', '640x360_1000k', '1024x576_2500k', '1280x720_4000k', '1920x1080_8000k', '3840x2160_12000k']
exp_types = ['bulk', 'ping', 'stream']
path_configs = ["multipath", "wlan", "lte"]

server_SSH_port = "1822"
server_IP = "211.86.152.184"
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

#回显拥塞控制算法
def getCongestionControl() -> str:
	cmd = "ssh -p " + server_SSH_port + ' ' + server_root + '@' + server_IP + " sudo sysctl net.ipv4.tcp_congestion_control"
	p = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
	buffer = p.stdout.read()
	buffer = buffer.split()
	congestionControl = str(buffer[-1], encoding = "utf-8")
	return congestionControl

#回显调度算法
def getScheduler() -> str:
	cmd = "ssh -p " + server_SSH_port + ' ' + server_root + '@' + server_IP + " sudo sysctl net.mptcp.mptcp_scheduler"
	p = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)
	buffer = p.stdout.read()
	buffer = buffer.split()
	scheduler = str(buffer[-1], encoding = "utf-8")
	return scheduler

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
		nic_name1 = 'eth1'
		nic_name2 = 'wlan0'
		wifi_ssid = 'LONGLONGLONG_5G'
		wifi_pwd = 'ustc11314'
		for path_config in path_configs:
			if path_config == "multipath":
				nicControl(nic_name1, "up")
				nicControl(nic_name2, "up")
				time.sleep(5)
				cmd = "sudo nmcli dev wifi connect '{}' password '{}' iface wlan0".format(wifi_ssid, wifi_pwd)
				if subprocess.call(cmd, shell = True):
					raise Exception("{} failed".format(cmd))
			elif path_config == "lte":
				nicControl(nic_name1, "up")
				nicControl(nic_name2, "down")
			else:
				nicControl(nic_name1, "down")
				nicControl(nic_name2, "up")
				time.sleep(5)
				cmd = "sudo nmcli dev wifi connect '{}' password '{}' iface wlan0".format(wifi_ssid, wifi_pwd)
				if subprocess.call(cmd, shell = True):
					raise Exception("{} failed".format(cmd))
			time.sleep(20)
			this_congestion_control = getCongestionControl()
			this_scheduler = getScheduler()
			for type in exp_types:
				exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
				if type != "stream":
					HttpClient.startExperiment(type, "./log", exp_time, '1920x1080_8000k', this_scheduler, this_congestion_control, path_config)
				else:
					for resolution in resolutions:
						HttpClient.startExperiment(type, "./log", exp_time, resolution, this_scheduler, this_congestion_control, path_config)

