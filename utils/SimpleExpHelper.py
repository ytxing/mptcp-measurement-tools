import subprocess
import os
import time
import argparse
# 检测同名进程是否存在,返回同名进程个数
def check_process(name):
    cmd = 'ps -ef | grep {} | grep -v grep | wc -l'.format(name)
    return subprocess.getoutput(cmd)

# run on server
if __name__ == '__main__':
    name = os.path.basename(__file__)
    r = check_process(name)
    if int(r) > 1:
        print('{}{} is running, kill them'.format(r, name))
        exit(0)
    # args from cmd line
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--time', help='time to change algorithms (min)', default=20)
    args = parser.parse_args()
    change_time = int(args.time) * 60
    scheduler = ['default', 'roundrobin', 'redundant']
    cc = ['cubic', 'reno', 'bbr', 'lia', 'olia']
    

    while True:
        for scheduler_i in scheduler:
            for cc_i in cc:
                cmd = []
                cmd.append("echo infonet123 | sudo -S sysctl net.mptcp.mptcp_scheduler={}".format(scheduler_i))
                cmd.append("echo infonet123 | sudo -S sysctl net.ipv4.tcp_congestion_control={}".format(cc_i))
                if cc_i == 'bbr':
                    cmd.append("echo infonet123 | sudo -S sysctl net.core.default_qdisc=fq")
                else:
                    cmd.append("echo infonet123 | sudo -S sysctl net.core.default_qdisc=pfifo_fast")
                for cmd_i in cmd:
                    p = subprocess.Popen(cmd_i, shell=True, stdout=subprocess.PIPE)
                    print( p.stdout.read().decode().strip())
                    p.wait()
                    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    print("[{}] {} output {}".format(now, cmd_i, p.stdout.read().decode()).strip())
                    
                subprocess.call("echo infonet123 | sudo -S echo '[{}] changed algs' > /var/www/html/server_status.txt".format(now), shell=True)
                subprocess.call("echo infonet123 | sudo -S sysctl net.mptcp.mptcp_scheduler >> /var/www/html/server_status.txt", shell=True)
                subprocess.call("echo infonet123 | sudo -S sysctl net.ipv4.tcp_congestion_control >> /var/www/html/server_status.txt", shell=True)
                subprocess.call("echo infonet123 | sudo -S sysctl net.core.default_qdisc >> /var/www/html/server_status.txt", shell=True)
                with open("/var/www/html/server_status.txt", "r") as f:
                    print("in /var/www/html/server_status.txt \n{}".format(f.read()))
                print('sleep {}s'.format(change_time))
                time.sleep(change_time)