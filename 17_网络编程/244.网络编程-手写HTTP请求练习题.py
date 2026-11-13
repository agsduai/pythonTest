# ===== 第244课：网络编程-手写HTTP请求 =====
# 知识点：
#   - HTTP 建立在 TCP 之上：连接 → 发请求报文 → 收响应报文 → 关闭
#   - 请求报文 = 请求行 + 请求头 + 空行 + 请求体
#   - 响应报文 = 状态行 + 响应头 + 空行 + 响应体
#   - 头与体之间用空行（\r\n\r\n）分隔
#   - 手写一次 GET，就明白 requests 库帮你做了什么
#   - 本课示例在本机自建一个迷你 HTTP 服务，无需外网

import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    """迷你 HTTP 服务端：返回一句话。"""

    def do_GET(self):
        body = f"你好，你访问的是 {self.path}".encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass                          # 关闭默认日志输出


def server(port_box, ready):
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    port_box.append(srv.server_address[1])
    ready.set()
    srv.handle_request()              # 只处理一个请求
    srv.server_close()


port_box, ready = [], threading.Event()
threading.Thread(target=server, args=(port_box, ready), daemon=True).start()
ready.wait(timeout=5)
port = port_box[0]

# --- 用 socket 手写 HTTP GET 请求 ---
cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cli.settimeout(5)
cli.connect(("127.0.0.1", port))
request = (
    "GET /hello?name=python HTTP/1.1\r\n"     # 请求行：方法 路径 协议
    "Host: 127.0.0.1\r\n"                     # 请求头
    "Connection: close\r\n"
    "\r\n"                                    # 空行：头结束
)
cli.send(request.encode("utf-8"))

# 循环收响应直到对方关闭（Connection: close）
response = b""
while True:
    chunk = cli.recv(4096)
    if not chunk:
        break
    response += chunk
cli.close()

# 拆响应报文：头 + \r\n\r\n + 体
head, _, body = response.partition(b"\r\n\r\n")
print("=== 响应头 ===")
print(head.decode("utf-8"))
print("=== 响应体 ===")
print(body.decode("utf-8"))

# ===== 练习题 =====
# 1. 把请求路径换成 /abc，验证响应体跟着变化。
# 2. 手写一个 POST 请求：加 Content-Length 头和请求体，服务端在 do_POST 里回显。
# 3. 用第093课的 Apifox 对比：手写报文与图形工具发的是不是同一回事。
# 4. 思考：requests.get(url) 底层至少帮你做了哪 5 件事？
