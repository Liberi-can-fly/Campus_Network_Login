# UTF-8
from datetime import datetime
import socket
import uuid
import time
import requests
import os
from requests.exceptions import HTTPError, Timeout

#####################################################
#                                                   #
#               Campus_Network_Login                #
#                                                   #
#####################################################


# ====================-> 账密 <-======================
userid = ""                                         # <- 账号
password = ""                                       # <- 密码

# ====================-> 设备 <-======================
this_is_PC = True                                   # <- True 以电脑方式登录,False 为手机方式登录(注意大写)
MAC = "1a%3A7c%3A46%3A02%3A35%3A7c"                 # <- URL编码的MAC地址(不必为真实的MAC地址)
hostname = "MIKU"                                   # <- 主机名(不必为真实的主机名)
vlan = ""                                           # <- vlan(可以为空)

# ==================-> 自动重联 <-=====================
auto_reconnect = True                               # <- 自动重联功能
passwd_error_out = True                             # <- 密码错误时退出
waiting_for_startup_time = 10                       # <- 启动后等待时间(s)
sleeptime = 60                                      # <- 联网状态检测时间间隔(s)
login_retry_time = 30                               # <- 重试登录间隔，由于会进行网络检测，时间变长(s)
retry_count = 0                                     # <- 重试登录次数，0为无限次(s)

# ==================-> 网络检测 <-=====================
network_check_count = 3                             # <- 网络检测时最大尝试次数
network_check_sleep_time = 10                       # <- 网络检测不通过时，下次网络检测间隔时间
network_check_web = "https://www.baidu.com"         # <- 测试网络连接用的网站

# ====================================================


def logo():
    logo_str = """
         ^
        /_\\
      |＝|＝|
 __   |＝|＝|   __
|==|  |＝|＝|  |==|
|==|  |＝|＝|  |==|
|==|__//_=_\\\\__|==|
|=== SONG SHAN ===|
    """
    return logo_str


session = requests.Session()
login_url = "http://10.100.100.4/quickauth.do?"


def get_headers():
    headers_PC = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Cookie": "",
        "DNT": "1",
        "Host": "10.100.100.4",
        "Referer": "",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0",
        "X-Requested-With": "XMLHttpRequest"
    }
    if this_is_PC:
        return headers_PC
    else:
        return ""


def log(msg):
    """日志函数"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {msg}")


def get_ip():
    """获取IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    # log("获取IP : " + ip)
    return ip


def get_uuid():
    """获取uuid4"""
    return str(uuid.uuid4())


def get_timestamp():
    """获取时间戳"""
    return time.time() * 1000


def get_url():
    """拼接登录URL"""
    url = f"""{login_url}userid={userid}&passwd={password}&wlanuserip={get_ip()}&wlanacname=VBRAS-GDSGLH&wlanaclp=10.100.100.5&ssid=&vlan={vlan}&mac={MAC}&version=0&portalpageid=3&timestamp={get_timestamp()}&uuid={get_uuid()}&portaltype=0&hostname={hostname}&bindCtrlld=&validateType=0&bindOperatorType=2&sendFttrNotice=0&skipTemporaryAccountCheck=false&token3gpp=8&noBindMac=0&roleGroupld=&roleClassld=&testGateWay=&skipOverTopLimit=0"""
    # log("拼接URL : " + url)
    return url


def network_connection_status():
    network_web = network_check_web
    for i in range(network_check_count):
        log(f"第{i + 1}次测试网络连接...")
        try:
            status = session.get(network_web).status_code
            if status == 200:
                log("已连接网络")
                return True
            else:
                log("网络连接已断开")
        except Exception:
            log("网络连接已断开")
        time.sleep(network_check_sleep_time)
    return False


def do_login():
    """登录"""
    try:
        url = get_url()
        headers = get_headers()
        log("登录中...")
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # 检查 HTTP 状态码是否正常，如果是 4xx/5xx 会抛出 HTTPError
        data = response.json()
        # print(data)

        # 判断成功与否
        if data.get("code") == "0":
            log("登录成功")
            return True
        elif (data.get("code") == "7" or data.get("code") == "1") and passwd_error_out == True:
            log(f"登录失败，代码: {data.get('code')}, 原因: {data.get("message")}")
            log("正在结束进程...")
            os._exit(1)
        else:
            log(f"登录失败，代码: {data.get('code')}, 原因: {data.get("message")}")
            return False
    except Timeout:
        log("连接超时")
        return False
    except ConnectionError:
        log("连接失败")
        return False
    except HTTPError:
        log("HTTPError")
    except:
        log("登录失败，未知原因")
        return False


def login_protection():
    """登录保护"""
    while True:
        if network_connection_status():
            print("------------------------------------------------")
            time.sleep(sleeptime)
        else:
            count = 0
            while True:
                log(f"第{count + 1}次尝试登录...")
                if do_login():
                    if network_connection_status():
                        time.sleep(sleeptime)
                        break
                if retry_count != 0:
                    count += 1
                    if count >= retry_count:
                        log("重试次数过多，即将退出程序")
                        os._exit(1)
                time.sleep(login_retry_time)


if __name__ == "__main__":
    print(logo())
    if auto_reconnect:
        log("等待中...")
        time.sleep(waiting_for_startup_time)
        log("========== 开始运行 ==========")
        login_protection()
    else:
        if do_login():
            if network_connection_status():
                print("网络已连接")
            else:
                print("网络连接失败")
