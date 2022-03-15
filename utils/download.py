import requests
import time
import sys

def formatFloat(num):
    return '{:.2f}'.format(num)

def getTimeMs():
    return time.time_ns()/1e6

def getTimeS():
    return time.time()

def downloadFile(name, url, s: requests.Session):
    r = s.get(url, stream=True)
    total_len = float(r.headers['content-length'])
    print("content-length: {}".format(total_len))
    curr_len = 0
    curr_len_last = 0
    time_last = getTimeMs()
    time_start = getTimeMs()
    for chunk in r.iter_content(chunk_size = 512):
        if chunk:
            curr_len += len(chunk)
            min_display_interval = 100
            time_now = getTimeMs()
            if time_now - time_last > min_display_interval or curr_len == total_len:
                p = curr_len / total_len * 100
                speed = (curr_len - curr_len_last) / (1024 * 1024) / (time_now - time_last) * 1000
                curr_len_last = curr_len
                print(name + ': Size: {}/{} '.format(curr_len, int(total_len)) + formatFloat(p) + '%' + ' Speed: ' + formatFloat(speed) + 'M/S Time: ' + formatFloat(time_now - time_last) + 'ms')
                time_last = getTimeMs()
    print("{}: Size: {} Speed: {}M/S Time:{}ms".format(name, int(total_len), formatFloat(speed), formatFloat(time_now - time_start)))
    
if __name__ == '__main__':
    s = requests.Session()
    downloadFile('test1000m', 'http://192.168.5.136/trunk/test1000m', s)