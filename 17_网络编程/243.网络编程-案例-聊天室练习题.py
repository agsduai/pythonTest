# ===== 第243课：网络编程-案例-聊天室 =====
# 知识点：
#   - 聊天室 = 并发服务端（第240课） + 广播逻辑
#   - 用列表管理在线连接，广播时给每个 socket 发一份
#   - 共享的连接列表要加锁保护（复习第196课）
#   - 客户端用“超时排水”收广播：读完当前所有消息再继续

import socket
import threading
import time

clients = []
lock = threading.Lock()


def broadcast(text, sender_label):
    """把消息发给所有在线客户端。"""
    with lock:
        targets = list(clients)      # 快照，避免遍历时列表被修改
    for sock, _ in targets:
        try:
            sock.sendall(f"{sender_label} 说：{text}".encode("utf-8"))
        except OSError:
            pass                     # 某个客户端掉线不影响其他人


def handle(conn, addr):
    with lock:
        clients.append((conn, addr))
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            broadcast(data.decode("utf-8"), f"端口{addr[1]}")
    finally:
        with lock:
            if (conn, addr) in clients:
                clients.remove((conn, addr))
        conn.close()


def server(port_box, ready, n_clients):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(n_clients)
    port_box.append(srv.getsockname()[1])
    ready.set()
    for _ in range(n_clients):
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
    srv.close()


def client(port, name, messages):
    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli.connect(("127.0.0.1", port))
    cli.settimeout(1.0)
    for msg in messages:
        cli.sendall(msg.encode("utf-8"))
        time.sleep(0.2)
        try:
            while True:              # 排干当前积压的广播
                data = cli.recv(1024)
                if not data:
                    break
                print(f"[{name}] 收到广播：{data.decode('utf-8')}")
        except socket.timeout:
            pass                     # 一秒内没有新消息就继续
    cli.close()


port_box, ready = [], threading.Event()
N_CLIENTS = 2
threading.Thread(target=server, args=(port_box, ready, N_CLIENTS), daemon=True).start()
ready.wait(timeout=5)
port = port_box[0]

t1 = threading.Thread(target=client, args=(port, "A", ["大家好", "我是A"]))
t2 = threading.Thread(target=client, args=(port, "B", ["你好A"]))
t1.start()
t2.start()
t1.join()
t2.join()
time.sleep(0.3)      # 等服务端线程收尾

# ===== 练习题 =====
# 1. 给聊天室加“昵称协议”：首条消息发昵称，广播时显示昵称而不是端口。
# 2. 增加“系统消息”：有人加入/离开时广播提示。
# 3. 思考：如果两个客户端同时广播，输出顺序一定吗？为什么这没关系？
