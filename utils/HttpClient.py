import argparse
import os
import multiprocessing
import threading
import queue
import subprocess
import requests
import tools
import time
import SMTPMonitor
server_url = 'http://211.86.152.184:1880'
EXP_TIMEOUT = 300 # max exp time(s)

def GoBulk(s: requests.Session, url: str, logger: tools.Logger, size : str = "10M"):
    '''
    downloadFile() -> status_code, total_len, time, speed
    '''
    server_url = url
    if size in ['1000K', '1000M', '100K', '100M', '10B', '10K', '10M', '1K', '1M']:
        name = 'test{}'.format(size)
    else:
        name = 'test10M'
    status_code, total_len, t, speed = tools.downloadFile(name, '{}/trunk/{}'.format(server_url, name), s, logger=logger)
    logger.log("Final Result code:{} total_len(bytes):{} time(ms):{} speed(mbps):{:.3f}".format(status_code, int(total_len), t, speed))
    return status_code, total_len, t, speed

class MimicPlayer:
    def __init__(self, s: requests.Session, url: str, bitrate: str = '8000k', logger: tools.Logger = None):
        self.session = s
        self.url = url
        self.bitrate = bitrate
        self.replay_buffer = queue.Queue(0)
        self.buffer_length = 10
        self.get_seg = True
        self.play_pause = False
        self.play_end = False

        self.timer_all = 0
        self.timer_pause = 0
        self.timer_start = 0

        self.total_seg_count = 10
        self.played_seg_count = 0
        self.got_seg_count = 0

        if logger is None:
            self.logger = tools.Logger('','')
        self.logger = logger
    
    def Player(self):
        total_time_start = time.time()
        while self.played_seg_count < self.total_seg_count:
            try:
                start = time.time()
                print('qsize: ' + str(self.replay_buffer.qsize()))
                seg = self.replay_buffer.get(timeout=60)
            except:
                self.logger.log("queue timeout(s):{} something WRONG".format(time.time() - start))
                break
            else:
                self.timer_pause += time.time() - start
                self.logger.log("pasue for {:.4f}s".format(time.time() - start))
                if seg is not None and seg == 4:
                    self.logger.log("Playing... seg_No.({}s):{}".format(seg, self.played_seg_count))
                    time.sleep(seg)
                    self.played_seg_count += 1

        self.play_end = True
        self.timer_all = time.time() - total_time_start

    def GetSegs(self):
        pass

    def start(self):
        '''
        -> 1st_seg_time, total_time, pause_time
        ```
        segment list:
        bbb_30fps.mpd
        bbb_30fps_0.m4v
        stream_2500k_4s
        stream_4000k_4s
        stream_8000k_4s
        stream_12000k_4s
        stream_15000k_4s
        stream_18000k_4s
        stream_30000k_4s
        stream_40000k_4s
        stream_50000k_4s
        stream_80000k_4s
        ```
        '''
        server_url = self.url
        self.PlayerProcessing = threading.Thread(target=self.Player)
        self.replay_buffer.put(4)
        self.got_seg_count += 1
        
        s = self.session
        # time the first seg
        time_start = time.time()
        tools.downloadFile('bbb_30fps.mpd', '{}/stream/bbb_30fps.mpd'.format(server_url), s, logger=self.logger)
        tools.downloadFile('bbb_30fps_0.m4v', '{}/stream/bbb_30fps_0.m4v'.format(server_url), s, logger=self.logger)
        self.got_seg_count += 1
        self.replay_buffer.put(4)
        self.timer_start = time.time() - time_start 
        self.PlayerProcessing.start()

        while self.got_seg_count < self.total_seg_count and not self.play_end:
            qsize = self.replay_buffer.qsize()
            if qsize <= 0.5 * self.buffer_length:
                self.logger.log("qsize:{} to get a seg".format(qsize))
                tools.downloadFile('stream_{}_4s_{}'.format(self.bitrate, self.got_seg_count), '{}/stream/stream_{}_4s'.format(server_url, self.bitrate), s, logger=self.logger)
                self.got_seg_count += 1
                self.replay_buffer.put(4)
        
        self.PlayerProcessing.join()
        self.logger.log("Final Result bitrate(bps):{} 1st_seg_time(s):{:.4f} all(s):{:.4f} pause(s):{:.4f} got_segs:{}".format(self.bitrate, self.timer_start, self.timer_all, self.timer_pause, self.got_seg_count))
        return self.timer_start, self.timer_all, self.timer_pause

def GoStream(s: requests.Session, url: str, logger: tools.Logger, bitrate: str = '8000k'):
    '''
    -> 1st_seg_time, total_time, pause_time
    ```
    segment list:
    bbb_30fps.mpd
    bbb_30fps_0.m4v
    stream_2500k_4s
    stream_4000k_4s
    stream_8000k_4s
    stream_12000k_4s
    stream_15000k_4s
    stream_18000k_4s
    stream_30000k_4s
    stream_40000k_4s
    stream_50000k_4s
    stream_80000k_4s
    ```
        '''
    player = MimicPlayer(s, url, bitrate, logger=logger)
    return player.start()

def GoPing(s: requests.Session, url: str, logger: tools.Logger):
    # 这两次得到的时延有较大的差距，因为第一次需要三次握手
    logger.log("first ping")
    server_url = url
    status_code, _, t1, _ = tools.downloadFile('test10B', '{}/trunk/test10B'.format(server_url), s, logger=logger)
    if status_code < 300:
        logger.log("Code {}\t ping(ms):{}".format(status_code, t1))
    else:
        logger.log("Wrong code {}\t ping(ms):{}".format(status_code, t1))
    logger.log("other pings")
    all_t = 0
    count = 0
    for _ in range(10):
        status_code, _, t, _ = tools.downloadFile('test10B', '{}/trunk/test10B'.format(server_url), s, logger=logger)
        if status_code < 300:
            logger.log("Code {}\t ping(ms):{}".format(status_code, t))
            all_t += t
            count += 1
        else:
            logger.log("Wrong code {}\t ping(ms):{}".format(status_code, t))
    logger.log("Final Result ({}/10) avg_ping_time(ms):{:.3f}".format(count, all_t/count))
    return t1, all_t/count

def startExperiment(url: str, type: str, log_path: str='./log/', log_file_name: str='log.txt', bitrate: str='8000k', size: str = '10M') -> int:
    if not url:
        print("need a url")
        return -1
    # get algorithms the server using
    req = requests.get('{}/server_status.txt'.format(url))
    if req.status_code >= 300:
        print("Server Error")
        body = req.text
        SMTPMonitor.sendEmail('Server Error', 'Server Error', body)
        return -1
    for line in req.content.decode().split('\n'):
        if line.startswith('net.mptcp.mptcp_scheduler ='):
                scheduler = line.split('=')[1].strip()
        if line.startswith('net.ipv4.tcp_congestion_control ='):
                congestion_control = line.split('=')[1].strip()
    log_file_name = '{}_{}_{}.txt'.format(log_file_name, scheduler, congestion_control)
    print(log_file_name)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    log_file_path = os.path.join(log_path, log_file_name)
    logger = tools.Logger(prefix='{}'.format(type), log_file=log_file_path)
    # get local nic info
    config = tools.getConfigFromFile('nic_setup.config')
    if 'nic_lte' in config:
        nic_lte = config['nic_lte']
    else:
        nic_lte = 'eth0'
        logger.log('NIC CONFIG WARNING no nic_lte')
    if 'nic_wlan' in config:
        nic_wlan = config['nic_wlan']
    else:
        nic_wlan = 'wlan0'
        logger.log('NIC CONFIG WARNING no nic_wlan')
    logger.log('NIC CONFIG nic_lte:{} nic_wlan:{}'.format(nic_lte, nic_wlan))
    lte_bytes_start = tools.getRcvBytesOfIface(nic_lte)
    wlan_bytes_start = tools.getRcvBytesOfIface(nic_wlan)
    # cmd = 'echo a | sudo -S tcpdump -l -n -i {} src host {}'.format(nic_wlan, '47.100.85.48')
    # dumpWlanProcess = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
    # cmd = 'echo a | sudo -S tcpdump -l -n -i {} src host {}'.format(nic_lte, '47.100.85.48')

    # cmd = 'echo a | sudo -S tcpdump -l -n -v -i {} src host {} and port 80'.format(nic_lte, url[7:])
    # logger.log(cmd)
    # dump_lte = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # cmd = 'echo a | sudo -S tcpdump -l -n -v -i {} src host {} and port 80'.format(nic_wlan, url[7:])
    # logger.log(cmd)
    # dump_wlan = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # time.sleep(1)
    # start the experiment
    s = requests.Session()
    if type == 'bulk':
        GoBulkProcessing = multiprocessing.Process(target=GoBulk, args=(s, url, logger, size))
        GoBulkProcessing.start()
        GoBulkProcessing.join(timeout=EXP_TIMEOUT)
        if GoBulkProcessing.is_alive():
            logger.log('Timeout {}s GoBulk terminate'.format(EXP_TIMEOUT))
            GoBulkProcessing.terminate()
    elif type == 'ping':
        GoPingProcessing = multiprocessing.Process(target=GoPing, args=(s, url, logger))
        GoPingProcessing.start()
        GoPingProcessing.join(timeout=EXP_TIMEOUT)
        if GoPingProcessing.is_alive():
            logger.log('Timeout {}s GoPing terminate'.format(EXP_TIMEOUT))
            GoPingProcessing.terminate()
    elif type == 'stream':
        GoStreamProcessing = multiprocessing.Process(target=GoStream, args=(s, url, logger, bitrate))
        GoStreamProcessing.start()
        GoStreamProcessing.join(timeout=EXP_TIMEOUT)
        if GoStreamProcessing.is_alive():
            logger.log('Timeout {}s GoStream terminate'.format(EXP_TIMEOUT))
            GoStreamProcessing.terminate()

    s.close()
    # time.sleep(1)
    # lte_bytes_count = tools.getDumpedBytes(dump_lte.stdout)
    # wlan_bytes_count = tools.getDumpedBytes(dump_wlan.stdout)
    # logger.log('DUMP BYTES ifname:{} total(bytes):{} '.format(nic_lte, lte_bytes_count))
    # logger.log('DUMP BYTES ifname:{} total(bytes):{} '.format(nic_wlan, wlan_bytes_count))
    lte_bytes_end = tools.getRcvBytesOfIface(nic_lte)
    wlan_bytes_end = tools.getRcvBytesOfIface(nic_wlan)
    logger.log('NIC BYTES ifname:{} total(bytes):{} '.format(nic_lte, lte_bytes_end - lte_bytes_start))
    logger.log('NIC BYTES ifname:{} total(bytes):{} '.format(nic_wlan, wlan_bytes_end - wlan_bytes_start))


if __name__ == '__main__':

    s = requests.Session()
    # 接收命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--type', help = 'type of experiment', choices = ['bulk', 'ping', 'stream'])
    # test1000K  test1000M  test100K  test100M  test10B  test10K  test10M  test1K  test1M
    parser.add_argument('--size', help = 'trunk size',
                        choices = ['1000K', '1000M', '100K', '100M', '10B', '10K', '10M', '1K', '1M'], default='10M')
    parser.add_argument('-l', '--log_path', help = 'log path',
                        default = './log-{}/'.format(time.strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('-i', '--id', help = 'id of experiment', default = 'lib')
    parser.add_argument('--inside', help = 'run from the inside', action = 'store_true', default = False)
    parser.add_argument('-u', '--url', help = 'url of server')
    parser.add_argument('-r', '--resolution', help = 'resolution of stream', default = '1920x1080_8000k')
    parser.add_argument('-b', '--bitrate', help = 'bitrate of stream', default = '8000k', choices=['2500k', '4000k', '8000k', '12000k', '15000k', '18000k', '30000k', '40000k', '50000k', '80000k'])
    parser.add_argument('-a', '--all', help = 'all experiment', action = 'store_true')
    args = parser.parse_args()
    # from the outside
    # server_url = 'http://211.86.152.184:1880'
    # from the inside
    # server_url = 'http://192.168.5.81'
    if args.inside:
        server_url = 'http://192.168.5.81'
    elif args.url:
        server_url = args.url
    else:
        print('Please input the url of server or use --inside')
        exit(1)
    if args.all:
        for type in ['bulk', 'ping', 'stream']:
            exp_id = '{}_{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), args.id, type)
            startExperiment(server_url, type, args.log_path, log_file_name = exp_id, bitrate = args.bitrate)
    elif args.type == 'stream':
        
        if args.bitrate in ['2500k', '4000k', '8000k', '12000k', '15000k', '18000k', '30000k', '40000k', '50000k', '80000k']:
            exp_id = '{}_{}_{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), args.id, args.type, args.bitrate)
            startExperiment(server_url, args.type, args.log_path, log_file_name = exp_id, bitrate=args.bitrate)
        else:
            print('Wrong bitrate: {}'.format(args.bitrate))
    elif args.type == 'bulk':
        exp_id = '{}_{}_{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), args.id, args.type, args.size)
        if args.size in ['1000K', '1000M', '100K', '100M', '10B', '10K', '10M', '1K', '1M']:
            startExperiment(server_url, args.type, args.log_path, log_file_name = exp_id, size = args.size)
        else:
            print('Wrong size: {}'.format(args.size))
    elif args.type == 'ping':
        exp_id = '{}_{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), args.id, type)
        print(exp_id)
        startExperiment(server_url, args.type, args.log_path, log_file_name = exp_id)
    else:
        print('please specify type of experiment')
        exit(1)


