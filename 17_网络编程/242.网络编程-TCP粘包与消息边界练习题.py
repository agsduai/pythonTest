# ===== 第242课：网络编程-TCP粘包与消息边界 =====
# 知识点：
#   - TCP 是“字节流”：没有消息边界，两次 send 可能被一次 recv 收到（粘包）
#   - 三种常见解决方案：①固定长度 ②分隔符 ③长度前缀（最常用）
#   - struct.pack("!I", n)：4 字节大端整数，作消息长度头
#   - recv 不保证收满：长消息要循环收，直到凑够

import socket
import struct
import threading


def recv_all(sock, n):
    """确保收满 n 字节。"""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("连接中断")
        buf += chunk
    return buf


def send_msg(sock, text):
    """按协议发一条消息：4 字节长度头 + 内容。"""
    body = text.encode("utf-8")
    sock.sendall(struct.pack("!I", len(body)) + body)


def recv_msg(sock):
    """按协议收一条消息：先读 4 字节头，再按长度读内容。"""
    (length,) = struct.unpack("!I", recv_all(sock, 4))
    return recv_all(sock, length).decode("utf-8")


def server(port_box, ready):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port_box.append(srv.getsockname()[1])
    ready.set()
    conn, _ = srv.accept()
    for _ in range(3):
        print("[服务端] 收到独立消息：", recv_msg(conn))
    conn.close()
    srv.close()


port_box, ready = [], threading.Event()
server_thread = threading.Thread(target=server, args=(port_box, ready), daemon=True)
server_thread.start()
ready.wait(timeout=5)

cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cli.connect(("127.0.0.1", port_box[0]))
# 连发 3 条，字节流在网络里会“粘”在一起，但按协议拆包后互不干扰
send_msg(cli, "消息一")
send_msg(cli, "消息二")
send_msg(cli, "消息三")
cli.close()
server_thread.join(timeout=5)     # 等服务端处理完再退出，否则看不到它的输出

# 方案对比：
#   固定长度：简单但浪费带宽；分隔符：适合文本（如 \n）；长度前缀：通用最强。

# ===== 练习题 =====
# 1. 用“\n 分隔符”方案实现同样的三条消息传输（提示：recv 循环找 \n）。
# 2. 发送一条 5KB 的长消息，验证 recv_msg 能完整收到。
# 3. 思考：为什么 recv(4) 可能只收到 2 个字节？什么情况下会发生？
