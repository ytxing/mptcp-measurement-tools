import argparse
import smtplib
import time 
import tools
from email.header import Header     # 用来设置邮件头和邮件主题 
from email.mime.text import MIMEText    # 发送正文只包含简单文本的邮件，引入MIMEText即可 

def get_send_bytes(iface):
    with open('/proc/net/dev', 'r') as f:
        lines = f.readlines()
    for line in lines:
        if iface in line:
            send_bytes = int(line.split()[9])
            break
    return send_bytes

# 倒计时20分钟，显示进度条
def timer(total_time):
    total_time = int(total_time)
    total_time = total_time
    for i in range(total_time + 1):
        time.sleep(1)
        print('\r', end='')
        print('#' * int(i/total_time * 50), end='')
        print('%d%%' % (i/total_time * 100), end='')
        print('({}/{})'.format(i, total_time), end='')
    print('\n')

def sendEmail(str):
    # 发件人和收件人 
    sender = 'ytxing96@qq.com'
    receiver = 'ytxing96@qq.com'
    
    # 所使用的用来发送邮件的SMTP服务器 
    smtpServer = 'smtp.qq.com'
    
    # 发送邮箱的用户名和授权码（不是登录邮箱的密码） 
    username = 'ytxing96@qq.com'
    password = 'ppqdsylikmocbcig'
    
    mail_title = 'MPTCP测试邮件,很急'
    mail_body = 'MPTCP测试有点问题,很急\n'
    mail_body += str
    
    # 创建一个实例 
    message = MIMEText(mail_body, 'plain', 'utf-8') # 邮件正文 
    message['From'] = sender       # 邮件上显示的发件人 
    message['To'] = receiver       # 邮件上显示的收件人 
    message['Subject'] = Header(mail_title, 'utf-8') # 邮件主题 
    
    try: 
        smtp = smtplib.SMTP()       # 创建一个连接 
        smtp.connect(smtpServer)      # 连接发送邮件的服务器 
        smtp.login(username, password)    # 登录服务器 
        smtp.sendmail(sender, receiver, message.as_string()) # 填入邮件的相关信息并发送 
        print("邮件发送成功！！！") 
        smtp.quit() 
    except smtplib.SMTPException: 
        print("邮件发送失败！！！")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--iface', type=str, default='eth0', help='the interface to monitor')
    args = parser.parse_args()
    iface = args.iface
    # 获得网卡发送的流量
    while True:
        send_bytes_start = get_send_bytes(iface)
        print('send_bytes_start:', send_bytes_start)
        print('sleep 20min')
        timer(10)
        send_bytes_end = get_send_bytes(iface)
        print('send_bytes_end:', send_bytes_end)
        print('send bytes in 20min:', send_bytes_end - send_bytes_start)
        # sendEmail('test')