import argparse
import os
import subprocess
import sys
import time
import threading
import tools
import HttpClient

# schedulers = ['default', 'roundrobin', 'redundant']
# congestion_controls = ['cubic', 'reno', 'bbr', 'lia', 'olia']
bitrates = ['18000k']
exp_types = ['bulk', 'ping', 'stream']
# exp_types = ['bulk']
accesses = ["multipath", 'lte', 'wlan']

# server_SSH_port = "1822"
# server_IP = "211.86.152.184"

server_SSH_port = "22"
server_IP = "47.100.85.48"

server_user = "libserver"
server_root = "root"

log = tools.Logger()

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
	cmd = "echo a | sudo -S ifconfig " + nic_name + ' ' + type
	print(cmd)
	if subprocess.call(cmd, shell = True, timeout=20):
		raise Exception("{} failed".format(cmd))


def main():
	#setCongestionControl(congestion_control)
	#setScheduler(scheduler)
	#setQdisc(congestion_control)
	# nicControl("eth0", "down")
	# 接收命令行参数
	parser = argparse.ArgumentParser()
	parser.add_argument('--test', help = 'run for test', action = 'store_true', default = False)
	parser.add_argument('-u', '--url', help = 'url')
	parser.add_argument('--location', help = 'location of the server and client (server-client)"')

	args = parser.parse_args()
	if not args.url:
		print("url is required (http://xxx.xxx.xxx.xxx:port)")
		sys.exit(1)
	if not args.location:
		print("location is required (server-client)")
		sys.exit(1)
	url = args.url
	log_path_today = "./log-{}".format(time.strftime("%Y-%m-%d", time.localtime()))
	if not os.path.exists(log_path_today):
		os.mkdir(log_path_today)
	config = tools.getConfigFromFile('nic_setup.config')
	if config == None:
		print("need a config file")
		sys.exit(1)
	for key in config:
		if not key in ['nic_lte', 'nic_wlan', 'wifi_ssid', 'wifi_password']:
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
		
		if args.test:
			print("run for test")
			access = 'none'
			for type in exp_types:
				if type != "stream":
					exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
					exp_id = "log_"
					exp_id += "_".join([exp_time, access, type])
					HttpClient.startExperiment(url, type, log_path_today, exp_id)
				else:
					for bitrate in bitrates:
						exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
						exp_id = "log_"
						exp_id += "_".join([exp_time, access, type, bitrate])
						HttpClient.startExperiment(url, type, log_path_today, exp_id, bitrate = bitrate)

	while True:
		explog_file = os.path.join(log_path_today, "explog.txt")
		log = tools.Logger(prefix='explog', log_file=explog_file)

		try:
			for access in accesses:
				if access == "multipath":
					nicControl(nic_lte, "up")
					nicControl(nic_wlan, "up")
					print('sleep 5s')
					time.sleep(5)
					cmd = "echo a | sudo -S nmcli dev wifi connect '{}' password '{}' ifname {}".format(wifi_ssid, wifi_password, nic_wlan)
					if subprocess.call(cmd, shell = True, timeout=60):
						log.log("{} failed, continue".format(cmd))
						continue
				elif access == "lte":
					nicControl(nic_lte, "up")
					nicControl(nic_wlan, "down")
					print('sleep 5s')
					time.sleep(5)
				else:
					try:
						nicControl(nic_lte, "down")
					except:
						log.log("nicControl {} down failed, continue".format(nic_lte))
					try:
						nicControl(nic_wlan, "up")
					except:
						log.log("nicControl {} up failed, continue".format(nic_lte))
					print('sleep 5s')
					time.sleep(5)
					cmd = "echo a | sudo -S nmcli dev wifi connect '{}' password '{}' ifname {}".format(wifi_ssid, wifi_password, nic_wlan)
					if subprocess.call(cmd, shell = True, timeout=20):
						log.log("{} failed, continue".format(cmd))
						continue
				print('sleep 5s')
				time.sleep(5)

				for type in exp_types:
					if type == "ping":
						exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
						exp_id = "log_"
						exp_id += "_".join([exp_time, args.location, access, type, wifi_ssid])
						HttpClient.startExperiment(url, type, log_path_today, exp_id)
					elif type == "bulk":
						bulk_size = '10M'
						exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
						exp_id = "log_"
						exp_id += "_".join([exp_time, args.location, access, type, bulk_size, wifi_ssid])
						HttpClient.startExperiment(url, type, log_path_today, exp_id, size = bulk_size)
					else:
						for bitrate in bitrates:
							exp_time = '{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
							exp_id = "log_"
							exp_id += "_".join([exp_time, args.location, access, type, bitrate, wifi_ssid])
							HttpClient.startExperiment(url, type, log_path_today, exp_id, bitrate=bitrate)
		except Exception as e:
			print(e)
			print("continue...")
			time.sleep(5)
			continue

if __name__ == "__main__":
	main()
