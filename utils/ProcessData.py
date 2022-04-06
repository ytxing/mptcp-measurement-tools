import os
import sys
import re
import time
from typing import List

import numpy as np

ccs = ['cubic', 'bbr', 'reno', 'lia', 'olia']
scheulers = ['roundrobin', 'default', 'redundant']
exp_types = ['bulk', 'stream', 'ping']
path_configs = ['lte', 'wlan', 'multipath']

class ExpResult:
    def __init__(self, file_name, result_keys: List[str] = []):
        self.file_name = file_name
        self.time = time.strptime(re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', file_name).group(), '%Y-%m-%d_%H-%M-%S')
        for cc in ccs:
            if cc in file_name:
                self.congestion_control = cc
                break
        for sch in scheulers:
            if sch in file_name:
                self.scheduler = sch
                break
        for exp in exp_types:
            if exp in file_name:
                self.exp_type = exp
                break
        for path in path_configs:
            if path in file_name:
                self.path_config = path
                break
        if self.exp_type == "stream":
            try:
                self.resolution = re.search(r'\d+x\d+_\d+k', file_name).group()
            except:
                self.resolution = None
            self.bulk_size = None
            self.pause = getDataByKeywords(file_name, ['Final Result'], ['pause\(s\)'])
            if len(self.pause) == 0:
                print("{}: cannot find a result:{}!".format(file_name, 'pause\(s\)'))
                self.pause = None
            else:
                self.pause = self.pause[0].split(':')[1].strip()
        elif self.exp_type == "bulk":
            self.resolution = None
            try:
                self.bulk_size = re.search(r'\d+(K|M)', file_name).group()
            except:
                self.bulk_size = None
            self.speed = getDataByKeywords(file_name, ['Final Result'], ['speed\(mbps\)'])
            if len(self.speed) == 0:
                print("{}: cannot find a result:{}!".format(file_name, 'speed\(mbps\)'))
                self.speed = None
            else:
                self.speed = self.speed[0].split(':')[1].strip()
        else:
            self.resolution = None
            self.bulk_size = None
            self.rtt = getDataByKeywords(file_name, ['Final Result'], ['avg_ping_time\(ms\)'])
            if len(self.rtt) == 0:
                print("{}: cannot find a result:{}!".format(file_name, 'avg_ping_time\(ms\)'))
                self.rtt = None
            else:
                self.rtt = self.rtt[0].split(':')[1].strip()
        
        for result_key in result_keys:
            key = result_key.replace('(', '\(').replace(')', '\)')
            if self.__dict__.get(result_key):
                print("{}: already exists {}!".format(file_name, result_key))
                continue
            self.__dict__[result_key] = getDataByKeywords(file_name, ['Final Result'], [key])
            if len(self.__dict__[result_key]) == 0:
                print("{}: cannot find a result:{}!".format(file_name, result_key))
                self.__dict__[result_key] = None
            else:
                self.__dict__[result_key] = self.__dict__[result_key][0].split(':')[1].strip()


    def show(self):
        print(self.__dict__)

# 递归获取目录下所有文件
def getAllFiles(path):
    result = []
    for root, dirs, files in os.walk(path):
        print(root)
        files.sort()
        for file in files:
            result.append(os.path.join(root, file))
    return result

# 递归获取目录下名称中有关键字的文件
def getFilesByKeywords(path, keywords: List[str]):
    result = []
    for root, dirs, files in os.walk(path):
        print(root)
        for file in files:
            yes = True
            for keyword in keywords:
                if keyword in file:
                    continue
                else:
                    yes = False
                    break
            if yes:
                result.append(os.path.join(root, file))
    return result

# 获取文件中关键词后数据
def getDataByKeywords(file, keywords: List[str], data_keys: List[str]):
    with open(file, 'r') as f:
        lines = f.readlines()
    result = []
    for line in lines:
        yes = True
        for keyword in keywords:
            if keyword in line:
                continue
            else:
                yes = False
                break
        if yes:
            for data_key in data_keys:
                print(line, data_key)
                match = re.search(data_key + ':(\S+)\s', line)
                print(match.group(1))
                if match:
                    result.append(match.group().strip())
    print(result)
    return result

def getResult(files: List[str], keywords: List[str], data_key: str):
    '''
    get result from files and return a dict of result{}
    '''
    pass

def run(dataDirectory, file_name_keys, result_keys):
    if len(sys.argv) != 4:
        print("Usage: python3 ProcessData.py <data directory> <file_name_key1,file_name_key2> <result_key1,result_key2>")
        sys.exit(1)
    if not os.path.isdir(dataDirectory):
        print("Error: data directory does not exist")
        sys.exit(1)
    # 获取目录下所有文件
    files = getFilesByKeywords(dataDirectory, file_name_keys)
    print(len(files))
    # 获取文件中关键词后数据
    # 'pause\(s\)' 'speed\(mbps\)'
    # keys = ["speed(mbps)", "total_len(bytes)"]
    keys = []
    for key in result_keys:
        keys.append(key.replace('(', '\(').replace(')', '\)'))
    print(keys)
    data = []
    for file in files:
        line = "{}".format(str(file).split('/')[-1].split('.')[0])
        for key in keys:
            print(file)
            results = getDataByKeywords(file, ['Final Result'], [key])
            print(results)
            for result in results:
                line += ",{}".format(result.split(':')[1].strip())
        results = getDataByKeywords(file, ['NIC BYTES'], ['ifname', 'total\(bytes\)'])
        for result in results:
            line += ",{}".format(result.split(':')[1].strip())
        print("line: ", line)
        print(results)
        data.append(line)

    header = 'file_name,' + ','.join([key for key in result_keys])
    header += ',ifname1,total(bytes),ifname2,total(bytes)'
    print(header)
    print('\n'.join(data))
    dir = './result-{}/'.format(time.strftime('%Y%m%d', time.localtime(time.time())))
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(dir + 'result-{}-{}-{}.csv'.format(time.strftime("%Y%m%d-%H%M%S", time.localtime()), '-' .join(file_name_keys), '-' .join(result_keys)), 'w') as f:
        f.write(header + '\n')
        f.write('\n'.join(data))

def getResult24h(dataDirectory, file_name_keys):
    files = getFilesByKeywords(dataDirectory, file_name_keys)
    exp_results: List[ExpResult] = []
    for file in files:
        exp_results.append(ExpResult(file, ['speed(mbps)']))
    
    result_lines = []
    for h in range(24):
        lte_speed = []
        wlan_speed = []
        multipath_speed = []
        count = 0
        for exp in exp_results:
            if exp.time.tm_hour != h:
                continue
            if exp.exp_type == 'bulk':
                exp.show()
                if exp.path_config == 'lte':
                    lte_speed.append(float(exp.speed))
                elif exp.path_config == 'wlan':
                    wlan_speed.append(float(exp.speed))
                elif exp.path_config == 'multipath':
                    multipath_speed.append(float(exp.speed))
                count += 1
        result_lines.append('{},{},{},{},{}'.format(h, np.mean(lte_speed), np.mean(wlan_speed), np.mean(multipath_speed), count))
    
    result_dir_today = './result-{}/'.format(time.strftime('%Y%m%d', time.localtime(time.time())))
    if not os.path.exists(result_dir_today):
        os.makedirs(result_dir_today)

    with open(result_dir_today + 'result-overtime.csv'.format(time.strftime("%Y%m%d-%H%M%S", time.localtime())), 'w') as f:
        f.write('hour,lte_speed,wlan_speed,multipath_speed,count\n')
        f.write('\n'.join(result_lines))
    print('\n'.join(result_lines))

if __name__ == '__main__':

    run(sys.argv[1], sys.argv[2].split(','), sys.argv[3].split(','))
    # results = getDataByKeywords('/home/ytxing/mptcpwireless-measurement/utils/log_real/log-2022-04-02/log_2022-04-03_01-49-46_wlan_bulk_10M_default_lia.txt', ['NIC BYTES'], ['ifname', 'total\(bytes\)'])
    exit(1)
    if len(sys.argv) != 4:
        print("Usage: python3 ProcessData.py <data directory> <file_name_key1,file_name_key2> <result_key1,result_key2>")
        sys.exit(1)
    dataDirectory = sys.argv[1]
    if not os.path.isdir(dataDirectory):
        print("Error: data directory does not exist")
        sys.exit(1)
    # 获取目录下所有文件
    file_name_keys = sys.argv[2].split(',')
    result_keys = sys.argv[3].split(',')
    files = getFilesByKeywords(dataDirectory, file_name_keys)
    exp_results: List[ExpResult] = []
    for file in files:
        exp_results.append(ExpResult(file, ['speed(mbps)']))
    
    result_lines = []
    for h in range(24):
        for m in range(2):
            lte_speed = []
            wlan_speed = []
            multipath_speed = []
            count = 0
            for exp in exp_results:
                if exp.time.tm_hour != h:
                    continue
                if not (m * 30 <= exp.time.tm_min < (m + 1) * 30):
                    continue
                if exp.exp_type == 'bulk':
                    exp.show()
                    if exp.path_config == 'lte':
                        lte_speed.append(float(exp.speed))
                    elif exp.path_config == 'wlan':
                        wlan_speed.append(float(exp.speed))
                    elif exp.path_config == 'multipath':
                        multipath_speed.append(float(exp.speed))
                    count += 1
            result_lines.append('{}.{},{},{},{},{}'.format(h, m * 5, np.mean(lte_speed), np.mean(wlan_speed), np.mean(multipath_speed), count))
    
    result_dir_today = './result-{}/'.format(time.strftime('%Y%m%d', time.localtime(time.time())))
    if not os.path.exists(result_dir_today):
        os.makedirs(result_dir_today)

    with open(result_dir_today + 'result-overtime.csv'.format(time.strftime("%Y%m%d-%H%M%S", time.localtime())), 'w') as f:
        f.write('hour,lte_speed,wlan_speed,multipath_speed,count\n')
        f.write('\n'.join(result_lines))
    print('\n'.join(result_lines))