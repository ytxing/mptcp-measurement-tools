import subprocess
import os
import time
import argparse
import random
# 检测同名进程是否存在,返回同名进程个数并杀死进程
def check_process(name):
    cmd = "ps -ef | grep -v grep | grep -v sudo | grep -v SCREEN | grep -v screen | grep " + name + " | wc -l"
    result = subprocess.getoutput(cmd)
    if int(result) > 1:
        cmd = "ps -ef | grep -v grep | grep " + name + " | awk '{print $2}'"
        pid = subprocess.getoutput(cmd)
        print(cmd)
        cmd = "kill -9 " + pid
        subprocess.getoutput(cmd)
        print("kill process: " + name)
    return result


# run on server
if __name__ == '__main__':
    # need sudo
    if os.getuid() != 0:
        print('please run with sudo')
        exit(1)

    name = os.path.basename(__file__)
    r = check_process(name)
    if int(r) > 1:
        print('{} is running({}), killed them. Run again.'.format(name, r))
        exit(0)
    # args from cmd line
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--time', help='time to change algorithms (min)', default=20)
    parser.add_argument('-d', '--directory', help='directory to the server', required=True)
    args = parser.parse_args()
    change_time = int(args.time) * 60
    pwd = args.directory
    # if pwd is not exist
    if not os.path.isdir(pwd):
        print("Error: data directory does not exist")
        exit
    status_file = os.path.join(pwd, 'server_status.txt')

    scheduler = ['default', 'roundrobin', 'redundant', 'ecf', 'blest', 'ols']
    random.shuffle(scheduler)
    # scheduler = ['default', 'roundrobin', 'redundant', 'ecf', 'blest', 'ol' ,'ols']
    cc = ['bbr']
    random.shuffle(cc)
    # cc = ['cubic', 'reno', 'bbr', 'lia', 'olia']
    

    while True:
        random.shuffle(scheduler)
        random.shuffle(cc)
        for scheduler_i in scheduler:
            for cc_i in cc:
                cmd = []
                cmd.append("sysctl net.mptcp.mptcp_scheduler={}".format(scheduler_i))
                if scheduler_i == 'ol':
                    cmd.append("sysctl net.mptcp.mptcp_debug=1")
                else:
                    cmd.append("sysctl net.mptcp.mptcp_debug=0")
                cmd.append("sysctl net.ipv4.tcp_congestion_control={}".format(cc_i))
                if cc_i == 'bbr':
                    cmd.append("sysctl net.core.default_qdisc=fq")
                else:
                    cmd.append("sysctl net.core.default_qdisc=pfifo_fast")
                    
                now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print('\033[1;31;40m[{}]\033[0m'.format(now))
                for cmd_i in cmd:
                    p = subprocess.Popen(cmd_i, shell=True, stdout=subprocess.PIPE)
                    print("output:", p.stdout.read().decode().strip())
                    p.wait()
                    # print in red
                    print("{}".format(cmd_i))

                subprocess.call("echo '[{}] changed algs' > {}".format(now, status_file), shell=True)
                subprocess.call("sysctl net.mptcp.mptcp_scheduler >> {}".format(status_file), shell=True)
                subprocess.call("sysctl net.ipv4.tcp_congestion_control >> {}".format(status_file), shell=True)
                subprocess.call("sysctl net.core.default_qdisc >> {}".format(status_file), shell=True)
                with open(status_file, "r") as f:
                    # print in green
                    print('\033[1;32;40min /root/server_dir/server_status.txt\033[0m')
                    for line in f.readlines():
                        print('\033[1;32;40m{}\033[0m'.format(line.strip()))
                print('sleep {}s'.format(change_time))
                print('all ccs = {}'.format(','.join(cc)))
                print('all schedulers = {}'.format(','.join(scheduler)))
                time.sleep(change_time)