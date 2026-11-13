# ===== 第238课：网络编程-基础概念 =====
# 知识点：
#   - IP 定位主机，端口定位进程（0~65535，1024 以下多为系统保留）
#   - TCP：可靠连接，像打电话；UDP：无连接、快，像寄明信片
#   - 套接字 Socket = IP + 端口，是网络编程的“门”
#   - 127.0.0.1 本机回环：自己连自己，开发测试专用
#   - 第093课学的 HTTP 是构建在 TCP 之上的应用层协议

import socket

print("本机名：", socket.gethostname())

# 查询 IP（可能离线，做容错处理）
try:
    print("本机IP：", socket.gethostbyname(socket.gethostname()))
except OSError as exc:
    print("本机IP查询失败：", exc)

try:
    print("baidu.com →", socket.gethostbyname("www.baidu.com"))
except OSError as exc:
    print("DNS查询失败（可能无网络）：", exc)

# 创建套接字：AF_INET = IPv4；SOCK_STREAM = TCP，SOCK_DGRAM = UDP
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("TCP 类型：", tcp_sock.type, "| UDP 类型：", udp_sock.type)
tcp_sock.close()
udp_sock.close()

# 实用技巧：绑定端口 0，让系统分配一个空闲端口
probe = socket.socket()
probe.bind(("127.0.0.1", 0))
print("系统分配的空闲端口：", probe.getsockname()[1])
probe.close()

# ===== 练习题 =====
# 1. 查询 3 个常见域名的 IP，多运行几次看是否有变化。
# 2. 用 netstat -ano | findstr LISTENING 查看本机正在监听的端口。
# 3. 创建一个 UDP 套接字并打印它的类型。
# 4. 思考：为什么说“一台机器只有一个 IP，但可以有 6 万多个端口”？
