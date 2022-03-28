import subprocess
import time
import threading
import tools
import HttpClient

schedulers = ['default', 'roundrobin', 'redundant']
congestion_controls = ['cubic', 'reno', 'bbr', 'lia', 'olia']
resolutions = ['1920x1080_8000k', '3840x2160_12000k']
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
		
		nic_lte = 'eth1'
		nic_wlan = 'wlan0'
		wifi_ssid = 'LONGLONGLONG_5G'
		wifi_pwd = 'ustc11314'
		for path_config in path_configs:
			if path_config == "multipath":
				nicControl(nic_lte, "up")
				nicControl(nic_wlan, "up")
				time.sleep(5)
				cmd = "sudo nmcli dev wifi connect '{}' password '{}' ifname {}".format(wifi_ssid, wifi_pwd, nic_wlan)
				if subprocess.call(cmd, shell = True):
					raise Exception("{} failed".format(cmd))
			elif path_config == "lte":
				nicControl(nic_lte, "up")
				nicControl(nic_wlan, "down")
			else:
				nicControl(nic_lte, "down")
				nicControl(nic_wlan, "up")
				time.sleep(5)
				cmd = "sudo nmcli dev wifi connect '{}' password '{}' ifname {}".format(wifi_ssid, wifi_pwd, nic_wlan)
				if subprocess.call(cmd, shell = True):
					raise Exception("{} failed".format(cmd))
			time.sleep(20)
			this_congestion_control = getCongestionControl()
			this_scheduler = getScheduler()
			for type in exp_types:
				exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
				if type != "stream":
					log_name = "log_"
					log_name += "_".join(exp_time, type, this_scheduler, this_congestion_control, path_config)
					log_name += '.txt'
					HttpClient.startExperiment(type, "./log{}".format(time.strftime("%Y-%m-%d", time.localtime())), log_name)
				else:
					for resolution in resolutions:
						log_name = "log_"
						log_name += "_".join(exp_time, type, resolution, this_scheduler, this_congestion_control, path_config)
						log_name += '.txt'
						HttpClient.startExperiment(type, "./log{}".format(time.strftime("%Y-%m-%d", time.localtime())), log_name)

