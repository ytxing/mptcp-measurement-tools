import time
import requests

s = requests.Session()
t = 0
for _ in range(100):
    start = time.time_ns()
    response = s.get('http://192.168.5.136/test10k')
    response = s.get('http://192.168.5.136/test10k')
    response = s.get('http://192.168.5.136/test10k')
    response = s.get('http://192.168.5.136/test10k')
    # response = requests.get('http://192.168.5.136/test10k')
    # response = requests.get('http://192.168.5.136/test10k')
    end = time.time_ns()
    t += end - start
t = t/20
t /= 1e6
print('session: avg {}'.format(t))
t = 0
for _ in range(100):
    start = time.time_ns()
    # response = s.get('http://192.168.5.136/test10k')
    # response = s.get('http://192.168.5.136/test10k')
    response = requests.get('http://192.168.5.136/test10k')
    response = requests.get('http://192.168.5.136/test10k')
    response = requests.get('http://192.168.5.136/test10k')
    response = requests.get('http://192.168.5.136/test10k')
    end = time.time_ns()
    t += end - start
t = t/20
t /= 1e6
print('requests: avg {}'.format(t))
# print(response.status_code)
# print(response.content)