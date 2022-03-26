import argparse
import os
import threading
import queue
import requests
import tools
import time
server_url = 'http://211.86.152.184:1880'
def GoBulk(s: requests.Session, logger: tools.Logger):
    '''
    downloadFile() -> status_code, total_len, time, speed
    '''
    return tools.downloadFile('test10M', '{}/trunk/test10M'.format(server_url), s, logger=logger)

class MimicPlayer:
    def __init__(self, s: requests.Session, r: str = '1920x1080_8000k', logger: tools.Logger = None):
        self.session = s
        self.resolution = r
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
                seg = self.replay_buffer.get(timeout=60)
            except:
                self.logger.log("queue timeout, something WRONG")
                break
            else:
                self.timer_pause += time.time() - start
                self.logger.log("pasue for {:.4f}s".format(time.time() - start))
                if seg is not None and seg == 4:
                    self.logger.log("Playing... seg_No.(4s):{}".format(self.played_seg_count))
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
        bbb_30fps_320x180_400k_4s.m4v
        bbb_30fps_480x270_600k_4s.m4v
        bbb_30fps_640x360_1000k_4s.m4v
        bbb_30fps_1024x576_2500k_4s.m4v
        bbb_30fps_1280x720_4000k_4s.m4v
        bbb_30fps_1920x1080_8000k_4s.m4v
        bbb_30fps_3840x2160_12000k_4s.m4v
        bbb_30fps-bbb_30fps.fbbb_30fps_3840x2160_12000k.mp4
        ```
        '''
        self.PlayerThreading = threading.Thread(target=self.Player)
        # self.TimerThreading = threading.Thread(target=self.Timer)
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
        self.PlayerThreading.start()
        # self.TimerThreading.start()

        while self.got_seg_count < self.total_seg_count:
            qsize = self.replay_buffer.qsize()
            if qsize <= 0.5 * self.buffer_length:
                self.logger.log("qsize:{} to get a seg".format(qsize))
                tools.downloadFile('bbb_30fps_{}_4s_{}.m4v'.format(self.resolution, self.got_seg_count), '{}/stream/bbb_30fps_{}_4s.m4v'.format(server_url, self.resolution), s, logger=self.logger)
                self.got_seg_count += 1
                self.replay_buffer.put(4)
        
        self.PlayerThreading.join()
        # self.TimerThreading.join()
        self.logger.log("1st_seg_time(s):{:.4f} all(s):{:.4f} pause(s):{:.4f}".format(self.timer_start, self.timer_all, self.timer_pause))
        return self.timer_start, self.timer_all, self.timer_pause

def GoStream(s: requests.Session, logger: tools.Logger, r: str = '1920x1080_8000k'):
    '''
    -> 1st_seg_time, total_time, pause_time
    ```
    segment list:
    bbb_30fps.mpd
    bbb_30fps_0.m4v
    bbb_30fps_320x180_400k_4s.m4v
    bbb_30fps_480x270_600k_4s.m4v
    bbb_30fps_640x360_1000k_4s.m4v
    bbb_30fps_1024x576_2500k_4s.m4v
    bbb_30fps_1280x720_4000k_4s.m4v
    bbb_30fps_1920x1080_8000k_4s.m4v
    bbb_30fps_3840x2160_12000k_4s.m4v
    bbb_30fps-bbb_30fps.fbbb_30fps_3840x2160_12000k.mp4
    ```
        '''
    player = MimicPlayer(s, r, logger=logger)
    return player.start()

def GoPing(s: requests.Session, logger: tools.Logger):
    # 这两次得到的时延有较大的差距，因为第一次需要三次握手
    logger.log("first ping")
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
    logger.log("({}/10) pings\t avg_ping_time(ms):{:.3f}".format(count, all_t/count))
    return t1, all_t/count

def startExperiment(type: str, log_path: str='./log/', id: str='', r: str='1920x1080_8000k', scheduler: str = '', congestion_control: str = '', path: str = ''):
    if type == "stream":
        log_file_name = 'log_{}_{}_{}_{}_{}_{}.txt'.format(id, type, scheduler, congestion_control, r, path)
    else:
        log_file_name = 'log_{}_{}_{}_{}_{}.txt'.format(id, type, scheduler, congestion_control, path)
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    logger = tools.Logger(prefix='{}'.format(type), log_file=os.path.join(log_path, log_file_name))
    #req = requests.get('{}/server_status.txt'.format(server_url))
    #for line in req.content.decode().split('\n'):
    #    logger.log(line)
    s = requests.Session()
    if type == 'bulk':
        GoBulk(s, logger)
    elif type == 'ping':
        GoPing(s, logger)
    elif type == 'stream':
        GoStream(s, logger, r)


if __name__ == '__main__':
    
    s = requests.Session()
    # 接收命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--type', help='type of experiment', choices=['bulk', 'ping', 'stream'])
    parser.add_argument('-l', '--log_path', help='log path', default='./log-{}/'.format(time.strftime('%Y%m%d-%H%M%S')))
    parser.add_argument('-i', '--id', help='id of experiment', default='lib')
    parser.add_argument('--inside', help='run from the inside', action='store_true')
    parser.add_argument('-u', '--url', help='url of server', default='http://211.86.152.184:1880')
    parser.add_argument('-r', '--resolution', help='resolution of stream', default='1920x1080_8000k')
    parser.add_argument('-a', '--all', help='all experiment', action='store_true')
    args = parser.parse_args()
    # from the outside
    # server_url = 'http://211.86.152.184:1880'
    # from the inside
    # server_url = 'http://192.168.5.81'
    if args.inside:
        server_url = 'http://192.168.5.81'
    else:
        server_url = args.url
    if args.all:
        for type in ['bulk', 'ping', 'stream']:
            exp_id = '{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), args.id)
            startExperiment(type, args.log_path, exp_id, args.resolution)
    elif args.type:
        exp_id = '{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), args.id)
        if args.resolution in ['320x180_400k', '480x270_600k', '640x360_1000k', '1024x576_2500k', '1280x720_4000k', '1920x1080_8000k', '3840x2160_12000k']:
            startExperiment(args.type, args.log_path, exp_id, args.resolution)
        else:
            print('Wrong resolution: {}'.format(args.resolution))
    else:
        print('please specify type of experiment')
        exit(1)

    # log_path = './log/'
    # my_id = 'lib'
    # exp_id = '{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), my_id)
    # startExperiment('stream', log_path, exp_id)
    # exp_id = '{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), my_id)
    # startExperiment('ping', log_path, exp_id)
    # exp_id = '{}_{}'.format(time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()), my_id)
    # startExperiment('bulk', log_path, exp_id)



