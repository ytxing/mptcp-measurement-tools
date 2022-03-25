import subprocess
import time
import threading


# run on server
if __name__ == '__main__':
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
                    print( p.stdout.read())
                    p.wait()
                    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    print("[{}] {} output {}".format(now, cmd_i, p.stdout.read().decode()).strip())
                    subprocess.call("echo infonet123 | sudo -S echo '[{}] changed algs' > /var/www/html/server_status.txt".format(now), shell=True)
                    subprocess.call("echo infonet123 | sudo -S sysctl net.mptcp.mptcp_scheduler >> /var/www/html/server_status.txt", shell=True)
                    subprocess.call("echo infonet123 | sudo -S sysctl net.ipv4.tcp_congestion_control >> /var/www/html/server_status.txt", shell=True)
                    subprocess.call("echo infonet123 | sudo -S sysctl net.core.default_qdisc >> /var/www/html/server_status.txt", shell=True)
                    with open("/var/www/html/server_status.txt", "r") as f:
                        print(f.read())
                sleep = 20 * 60
                print('sleep {}s'.format(sleep))
                time.sleep(sleep)