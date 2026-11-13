# ===== 第239课：网络编程-TCP通信入门 =====
# 知识点：
#   - 服务端流程：bind → listen → accept → recv/send → close
#   - 客户端流程：connect → send/recv → close
#   - 收发的都是 bytes：发送前 encode，接收后 decode
#   - recv(1024) 的 1024 是“本次最多收”的字节数，不是“必须收满”
#   - 演示技巧：同一进程内用一个线程当服务端、主线程当客户端

import socket
import threading


def server(port_box, ready):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))       # 端口 0：系统自动分配空闲端口
    srv.listen(1)
    port_box.append(srv.getsockname()[1])
    ready.set()                      # 告诉客户端：可以连了

    conn, addr = srv.accept()        # 阻塞等待连接
    print(f"[服务端] 客户端 {addr} 已连接")
    data = conn.recv(1024)
    print("[服务端] 收到：", data.decode("utf-8"))
    conn.send("收到，欢迎！".encode("utf-8"))
    conn.close()
    srv.close()


port_box, ready = [], threading.Event()
t = threading.Thread(target=server, args=(port_box, ready), daemon=True)
t.start()
ready.wait(timeout=5)
port = port_box[0]

# --- 客户端 ---
cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cli.connect(("127.0.0.1", port))
print(f"[客户端] 已连接端口 {port}")
cli.send("你好，服务端！".encode("utf-8"))
reply = cli.recv(1024)
print("[客户端] 收到：", reply.decode("utf-8"))
cli.close()
t.join(timeout=5)

# ===== 练习题 =====
# 1. 把客户端连发 3 条消息，服务端循环 recv 打印。
# 2. 给客户端加上输入：服务端把消息原样（回声）发回（提示：echo 服务）。
# 3. 把 recv(1024) 改成 recv(4)，发送长消息观察“只收到一段”的现象。
# 4. 思考：accept 返回的 conn 和监听用的 srv 各自负责什么？
