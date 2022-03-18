import time
import requests

print(time.time_ns())
print(time.clock_gettime(1))
print(time.clock_gettime(2))
print(time.clock_gettime(3))
time.sleep(0.00523)

print(time.time_ns())