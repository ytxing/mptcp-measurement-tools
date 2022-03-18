import datetime
import requests
import time
import sys

def printLog(s: str, prefix: str='test'):
    log = '[{}] '.format(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    if len(prefix) > 0:
        log = '[{}]'.format(prefix) + log
    log += s
    print(log)

def formatFloat(num):
    return '{:.3f}'.format(num)

def getTimeMs():
    return time.time_ns()/1e6

def getTimeS():
    return time.time()

def downloadFile(name, url, s: requests.Session):
    time_last = getTimeMs()
    time_start = getTimeMs()
    r = s.get(url, stream=True)
    if r.status_code >= 300:
        printLog('WRONG!\t status_code:{}'.format(r.status_code))
    else:
        printLog('status_code:{}'.format(r.status_code))
    total_len = float(r.headers['content-length'])
    printLog("content-length: {} get response: {:.3f}ms".format(total_len, getTimeMs() - time_start))
    curr_len = 0
    curr_len_last = 0
    for chunk in r.iter_content(chunk_size=512):
        if chunk:
            curr_len += len(chunk)
            min_display_interval = 100
            time_now = getTimeMs()
            if time_now - time_last > min_display_interval or curr_len == total_len:
                p = curr_len / total_len * 100
                speed = (curr_len - curr_len_last) /(time_now - time_last)
                speed *= 1000
                speed /= 1024*1024
                curr_len_last = curr_len
                printLog('Loading...\t name:{} size(B):{} percentage(/{}):{} speed(mBps):{:.3f} interval(ms):{:.3f}'.format(name, curr_len, int(total_len), formatFloat(p), speed, time_now - time_last))
                time_last = getTimeMs()
    speed = curr_len / (time_now - time_start)
    speed *= 1000
    speed /= 1024*1024
    printLog('Complete!\t name:{} size(B):{} percentage(/{}):{} speed(mBps):{:.3f} total_time(ms):{:.3f}'.format(name, curr_len, int(total_len), formatFloat(p), speed, time_now - time_start))
    
if __name__ == '__main__':
    s = requests.Session()
    downloadFile('test1000m', 'http://192.168.5.136/trunk/test10M', s)
