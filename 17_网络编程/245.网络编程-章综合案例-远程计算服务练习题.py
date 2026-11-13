# ===== 第245课：网络编程-章综合案例-远程计算服务 =====
# 知识点：
#   - 综合运用：TCP 并发 + 长度前缀协议（第242课）+ 异常处理
#   - 协议设计：客户端发 "add 1 2" 这样的指令，服务端返回计算结果
#   - 服务端永不信任输入：非法指令返回错误提示，而不是崩溃
#   - 服务端读到空数据 = 客户端关闭，优雅退出循环

import socket
import struct
import threading
import time


# --- 协议收发（复习第242课） ---
def recv_all(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("连接中断")
        buf += chunk
    return buf


def send_msg(sock, text):
    body = text.encode("utf-8")
    sock.sendall(struct.pack("!I", len(body)) + body)


def recv_msg(sock):
    (length,) = struct.unpack("!I", recv_all(sock, 4))
    return recv_all(sock, length).decode("utf-8")


# --- 业务逻辑：只做白名单内的运算 ---
OPS = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b,
}


def calc(expr):
    try:
        op, a, b = expr.split()
        if op not in OPS:
            return f"错误：不支持的运算 {op}（支持 {'/'.join(OPS)}）"
        return f"结果：{OPS[op](float(a), float(b))}"
    except ValueError:
        return "错误：格式应为 'op 数字 数字'，如 add 1 2"
    except ZeroDivisionError:
        return "错误：除数不能为 0"


# --- 服务端 ---
def handle(conn, addr):
    with conn:
        while True:
            try:
                expr = recv_msg(conn)
            except (ConnectionError, struct.error):
                break                      # 客户端关闭，结束本连接
            print(f"[服务端] {addr} 请求：{expr}")
            send_msg(conn, calc(expr))


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


port_box, ready = [], threading.Event()
threading.Thread(target=server, args=(port_box, ready, 1), daemon=True).start()
ready.wait(timeout=5)

# --- 客户端 ---
cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cli.connect(("127.0.0.1", port_box[0]))
for expr in ("add 3 5", "mul 2.5 4", "hack 1 2", "div 10 0"):
    send_msg(cli, expr)
    print(f"[客户端] {expr} → {recv_msg(cli)}")
cli.close()
time.sleep(0.3)

# ===== 练习题 =====
# 1. 给 OPS 增加 pow（乘方）运算并测试。
# 2. 把 handle 里的 while True 改成“最多服务 10 条请求后主动断开”。
# 3. 多开 2 个客户端同时请求，验证并发处理（参考第240课）。
# 4. 思考：这个“指令协议”和 HTTP 的“路径 + 参数”有什么对应关系？
