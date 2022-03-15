import threading
import queue
import requests
import download
import time
server_addr = '192.168.5.136'
def GoBulk(s: requests.Session):
    download.downloadFile('test100m', 'http://192.168.5.136/trunk/test100m', s)


class MimicPlayer:
    def __init__(self, s: requests.Session):
        self.session: requests.Session = s
        self.replay_buffer: queue.Queue = queue.Queue(0)
        self.buffer_length = 10
        self.get_seg: bool = True
        self.play_pause: bool = False
        self.play_end: bool = False

        self.timer_all = 0
        self.timer_pause = 0
        self.timer_start = 0

        self.total_seg_count = 10
        self.played_seg_count = 0
        self.got_seg_count = 0
    
    def Player(self):
        total_time_start = time.time()
        while self.played_seg_count < self.total_seg_count:
            try:
                start = time.time()
                seg = self.replay_buffer.get(timeout=60)
            except:
                print("queue timeout, something wrong")
                break
            else:
                self.timer_pause += time.time() - start
                if seg is not None and seg == 4:
                    print("play seg{}, 4s".format(self.played_seg_count))
                    time.sleep(seg)
                    self.played_seg_count += 1

        self.play_end = True
        self.timer_all = time.time() - total_time_start

    def GetSegs(self):
        pass

    def start(self):
        '''
        ```
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
        download.downloadFile('bbb_30fps.mpd', 'http://192.168.5.136/stream/bbb_30fps.mpd', s)
        download.downloadFile('bbb_30fps_0.m4v', 'http://192.168.5.136/stream/bbb_30fps_0.m4v', s)
        self.got_seg_count += 1
        self.replay_buffer.put(4)
        self.timer_start = time.time() - time_start 
        self.PlayerThreading.start()
        # self.TimerThreading.start()

        while self.got_seg_count < self.total_seg_count:
            qsize = self.replay_buffer.qsize()
            if qsize <= 0.5 * self.buffer_length:
                print("qsize: {}, get seg".format(qsize))
                download.downloadFile('bbb_30fps_1920x1080_8000k_4s_{}.m4v'.format(self.got_seg_count), 'http://192.168.5.136/stream/bbb_30fps_1920x1080_8000k_4s.m4v', s)
                self.got_seg_count += 1
                self.replay_buffer.put(4)
        
        self.PlayerThreading.join()
        # self.TimerThreading.join()
        print("start: {:.2f}s all: {:.2f}s pause:{:.2f}s".format(self.timer_start, self.timer_all, self.timer_pause))






def GoStream(s: requests.Session):
    '''
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
    '''
    # replay_buffer = queue.Queue(0)
    # get_seg: bool = True
    # download.downloadFile('bbb_30fps.mpd', 'http://192.168.5.136/stream/bbb_30fps.mpd', s)
    # download.downloadFile('bbb_30fps_0.m4v', 'http://192.168.5.136/stream/bbb_30fps_0.m4v', s)
    # replay_buffer.put(4) # each seg lasts for 4 seconds
    player = MimicPlayer(s)
    player.start()


if __name__ == '__main__':
    
    s = requests.Session()
    start = time.time()
    GoStream(s)
    print("{} in all".format(time.time() - start))
    # GoBulk(s)
