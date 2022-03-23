import subprocess
import time



if __name__ == '__main__':
    scheduler = ['default', 'roundrobin', 'redundant']
    cc = ['cubic', 'reno']
    while True:
        for scheduler_i in scheduler:
            for cc_i in cc:
                cmd = []
                cmd.append("sudo sysctl net.mptcp.mptcp_scheduler={}".format(scheduler_i))
                cmd.append("sudo sysctl net.ipv4.tcp_congestion_control={}".format(cc_i))
                for cmd_i in cmd:
                    p = subprocess.Popen(cmd_i, shell=True, stdout=subprocess.PIPE)
                    p.wait()
                    now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    if p.returncode != 0:
                        print("[{}] {} FAILED".format(now, cmd_i))
                    else:  
                        print("[{}] {} SUCCESSED \noutput {}".format(now, cmd_i, p.stdout.read().decode()))
                        subprocess.call("sudo echo > /var/www/html/server_status.txt", shell=True)
                        subprocess.call("sudo sysctl net.mptcp.mptcp_scheduler >> /var/www/html/server_status.txt", shell=True)
                        subprocess.call("sudo sysctl net.ipv4.tcp_congestion_control >> /var/www/html/server_status.txt", shell=True)
                time.sleep(30 * 60)