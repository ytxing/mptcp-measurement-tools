import mytools
import requests
import download
server_addr = '192.168.5.136'
def GoBulk(s: requests.Session):
    download.downloadFile('test100m', 'http://192.168.5.136/trunk/test100m', s)
    


if __name__ == '__main__':
    
    s = requests.Session()
    GoBulk(s)
