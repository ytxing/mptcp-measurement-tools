import argparse
from asyncio import constants
from cmath import exp
import multiprocessing
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
accesses = ["multipath", "multipath", "multipath", "multipath", "multipath", 'lte', 'wlan']

# server_SSH_port = "1822"
# server_IP = "211.86.152.184"

server_SSH_port = "22"
server_IP = "47.100.85.48"


log = tools.Logger()

def nicControl(nic_name, type):
	cmd = "echo a | sudo -S ifconfig " + nic_name + ' ' + type
	print(cmd)
	if subprocess.call(cmd, shell = True, timeout=20):
		raise Exception("{} failed".format(cmd))

def getLogNum(log_path):
	cmd = "ls " + log_path + " | wc -l"
	log_num = subprocess.check_output(cmd, shell = True)
	return int(log_num)

def main(args):

	if not args.url:
		print("url is required (http://xxx.xxx.xxx.xxx:port)")
		sys.exit(1)
	if not args.location:
		print("location is required (server-client)")
		sys.exit(1)
	url = args.url

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

	while True:
		log_path_today = "./log-{}".format(time.strftime("%Y-%m-%d", time.localtime()))
		if not os.path.exists(log_path_today):
			os.mkdir(log_path_today)
		explog_file = os.path.join(log_path_today, "explog_error.txt")
		log = tools.Logger(prefix='explog', log_file=explog_file)

		try:
			for access in accesses:
				if access == "multipath":
					nicControl(nic_lte, "up")
					nicControl(nic_wlan, "up")
					print('sleep 5s')
					time.sleep(5)
					cmd = "echo a | sudo -S nmcli dev wifi connect '{}' password '{}' ifname {}".format(wifi_ssid, wifi_password, nic_wlan)
					if subprocess.call(cmd, shell = True, timeout=200):
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
					if subprocess.call(cmd, shell = True, timeout=200):
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
	parser = argparse.ArgumentParser()
	parser.add_argument('-u', '--url', help = 'url')
	parser.add_argument('--location', help = 'location of the server and client')
	args = parser.parse_args()

	# check python version > 3.8
	if sys.version_info < (3, 8):
		print("need python 3.8 or above")
		sys.exit(1)
	main_process = multiprocessing.Process(target=main, args=[args])
	main_process.start()
	restart_flag = False
	while True:
		if restart_flag:
			main_process.terminate()
			main_process.join(timeout=30)
			if main_process.is_alive():
				print("restart failed")
				main_process.kill()
				main_process.join(timeout=30)
			main_process.close()
			main_process = multiprocessing.Process(target=main, args=[args])
			print("restart")
			main_process.start()
			restart_flag = False
		
		log_path_today = "./log-{}".format(time.strftime("%Y-%m-%d", time.localtime()))
		if not os.path.exists(log_path_today):
			os.mkdir(log_path_today)
		explog_file = os.path.join(log_path_today, "monitor_error.txt")
		log = tools.Logger(prefix='monitor', log_file=explog_file, log_type='a')

		previous_exp_count = getLogNum(log_path_today)
		print(getLogNum(log_path_today))
		time.sleep(600)
		if previous_exp_count == getLogNum(log_path_today):
			log.log("no new experiment")
			restart_flag = True


