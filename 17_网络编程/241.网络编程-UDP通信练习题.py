# ===== 第241课：网络编程-UDP通信 =====
# 知识点：
#   - UDP 无连接：sendto 直接发，recvfrom 返回 (数据, 对方地址)
#   - 不保证送达、不保证顺序，但快、开销小
#   - 适用场景：直播、游戏心跳、DNS 查询、局域网广播
#   - 与 TCP 对比：没有 accept，也没有“连接”概念

import socket
import threading


def server(port_box, ready):
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.bind(("127.0.0.1", 0))
    port_box.append(srv.getsockname()[1])
    ready.set()
    for _ in range(2):
        data, addr = srv.recvfrom(1024)
        print(f"[服务端] 来自 {addr}：{data.decode('utf-8')}")
        srv.sendto(f"已收到：{data.decode('utf-8')}".encode("utf-8"), addr)
    srv.close()


port_box, ready = [], threading.Event()
threading.Thread(target=server, args=(port_box, ready), daemon=True).start()
ready.wait(timeout=5)
port = port_box[0]

# --- 客户端：直接 sendto，不需要 connect ---
cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
cli.settimeout(3)        # UDP 不保证送达，设置超时避免死等
for msg in ("第一条UDP", "第二条UDP"):
    cli.sendto(msg.encode("utf-8"), ("127.0.0.1", port))
    data, _ = cli.recvfrom(1024)
    print(f"[客户端] 收到：{data.decode('utf-8')}")
cli.close()

# TCP vs UDP 一句话总结：
# TCP 要先“握手”建立连接，可靠但慢一点；UDP 抬手就发，快但可能丢。

# ===== 练习题 =====
# 1. 连发 5 条消息，把服务端改成一直接收（while True + Ctrl+C 结束）。
# 2. 故意不启动服务端，只跑客户端，观察 recvfrom 超时报什么异常。
# 3. 对比：把本课示例改回 TCP 版本，代码多了哪些步骤？
# 4. 思考：视频通话为什么选 UDP？转账为什么必须 TCP？
