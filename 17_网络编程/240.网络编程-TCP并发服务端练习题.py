# ===== 第240课：网络编程-TCP并发服务端 =====
# 知识点：
#   - accept 每次返回一个新的连接 socket，与监听 socket 分工不同
#   - 每个客户端交给一个线程处理 → 多个客户端可同时通信
#   - sendall：保证把数据全部发完（send 可能只发一半）
#   - 复习前置：第195课多线程 + 第239课回声协议

import socket
import threading


def handle(conn, addr):
    """每个客户端连接独享一个线程。"""
    with conn:
        for _ in range(2):
            data = conn.recv(1024)
            if not data:                 # 对方关闭了连接
                break
            reply = f"[回声] {data.decode('utf-8')}".encode("utf-8")
            conn.sendall(reply)
    print(f"[服务端] {addr} 已断开")


def server(port_box, ready):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(5)
    port_box.append(srv.getsockname()[1])
    ready.set()
    for _ in range(2):                   # 接待 2 个客户端
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
    srv.close()


port_box, ready = [], threading.Event()
server_thread = threading.Thread(target=server, args=(port_box, ready), daemon=True)
server_thread.start()
ready.wait(timeout=5)
port = port_box[0]


def client(name):
    cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cli.connect(("127.0.0.1", port))
    for i in range(2):
        cli.sendall(f"{name} 的第{i + 1}条消息".encode("utf-8"))
        print(f"[{name}] 收到：", cli.recv(1024).decode("utf-8"))
    cli.close()


t1 = threading.Thread(target=client, args=("客户端A",))
t2 = threading.Thread(target=client, args=("客户端B",))
t1.start()
t2.start()
t1.join()
t2.join()
server_thread.join(timeout=5)     # 等服务端收尾，避免输出被截断

# 说明：真实并发服务端用 while True 循环 accept（本课示意固定接待 2 个）。

# ===== 练习题 =====
# 1. 把客户端数量增加到 4 个，观察输出交织顺序。
# 2. 给 handle 加上“收到 quit 就断开”的协议。
# 3. 思考：如果 1000 个客户端同时连，一个线程一个客户端有什么问题？
#    （引子：第200课的 asyncio 就是为这种场景准备的）
