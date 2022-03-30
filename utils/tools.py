import datetime
import requests
import time
import sys

def getConfigFromFile(file_name):
    '''
    getConfigFromFile() -> config
    '''
    config = {}
    with open(file_name, 'r') as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if line.startswith('#') or line == '':
            continue
        key, value = line.split('=')
        config[key.strip()] = value.strip()
    print(config)
    return config

def getRcvBytesOfIface(iface):
    '''
    getRcvBytesOfIface() -> bytes
    '''
    with open('/proc/net/dev', 'r') as f:
        lines = f.readlines()
    for line in lines:
        if iface in line:
            return int(line.split()[1])
    return 0
class Logger:
    def __init__(self, prefix: str='nonprefix', log_file: str='log_empty', log_level: int=0):
        self.prefix = prefix
        self.log_file = log_file
        self.log_level = log_level
        self.log_file_handle = open(self.log_file, 'w')
        self.start_time = time.time()

    def log(self, s: str, level: int=0):
        if level <= self.log_level:
            log = '[{}][{:.6f}] '.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"), time.time() - self.start_time)
            if len(self.prefix) > 0:
                log = '[{}]'.format(self.prefix) + log
            log += s
            print(log)
            self.log_file_handle.write(log + '\n')
            self.log_file_handle.flush()

    def __del__(self):
        self.log_file_handle.close()

def getTimeMs():
    return time.time_ns()/1e6

def getTimeS():
    return time.time()

def downloadFile(name, url, s: requests.Session, logger: Logger=None):
    '''
    downloadFile() -> status_code, total_len, time, speed
    '''
    if logger is None:
        logger = Logger()
    time_last = getTimeMs()
    time_start = getTimeMs()
    r = s.get(url, stream=True)
    if r.status_code >= 300:
        logger.log('GET WRONG\t status_code:{}'.format(r.status_code))
    else:
        logger.log('GET status_code:{}'.format(r.status_code))
    total_len = float(r.headers['content-length'])
    logger.log("content-length(B):{} get_response(ms):{:.3f}".format(total_len, getTimeMs() - time_start))
    curr_len = 0
    curr_len_last = 0
    for chunk in r.iter_content(chunk_size=512):
        if chunk:
            curr_len += len(chunk)
            min_display_interval = 1000 # in ms
            time_now = getTimeMs()
            if time_now - time_last > min_display_interval or curr_len == total_len:
                p = curr_len / total_len * 100
                speed = (curr_len - curr_len_last) /(time_now - time_last)
                speed *= 1000 * 8
                speed /= 1024*1024
                curr_len_last = curr_len
                logger.log('Loading name:{} size(B):{} percentage(%/{}):{:.3f} speed(mbps):{:.3f} interval(ms):{:.3f}'.format(name, curr_len, int(total_len), p, speed, time_now - time_last))
                time_last = getTimeMs()
                if p == 100 or curr_len == total_len:
                    break
    speed = curr_len / (time_now - time_start)
    speed *= 1000 * 8
    speed /= 1024*1024
    logger.log('Complete name:{} size(B):{} percentage(/{}):{:.3f} speed(mbps):{:.3f} total_time(ms):{:.3f}'.format(name, curr_len, int(total_len), p, speed, time_now - time_start))
    return r.status_code, total_len, (time_now - time_start), speed
    
if __name__ == '__main__':
    config = getConfigFromFile('nic_setup.config')
    for key in config:
        print(key, config[key])
    if 'nic_lte' in config and 'nic_wlan' in config:
        nic_lte = config['nic_lte']
        nic_wlan = config['nic_wlan']
    print('GOOD CONFIG nic_lte:{} nic_wlan:{}'.format(nic_lte, nic_wlan))
