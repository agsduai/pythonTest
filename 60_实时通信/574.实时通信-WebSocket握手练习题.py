# ===== 第574课：实时通信-WebSocket握手 =====
# 知识点：
#   - WebSocket 复用 HTTP 端口：先发一个“升级”请求，再切换协议
#   - 请求头：Upgrade: websocket、Connection: Upgrade、Sec-WebSocket-Key、Version: 13
#   - 服务端把 Key + 固定 GUID 做 SHA-1，再 Base64，得到 Sec-WebSocket-Accept
#   - 响应 101 Switching Protocols 后，这条 TCP 连接就变成全双工
#   - 握手不是加密：明文 ws:// 仍需 TLS 才有 wss://
#   - 与第239课 TCP、第244课手写 HTTP 的关系：握手就是一次特殊 HTTP 请求
# 依赖：无（socket/hashlib/base64）

import base64
import hashlib
import socket
import threading
import time

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def accept_key(client_key: str) -> str:
    digest = hashlib.sha1((client_key + GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def recv_until(sock: socket.socket, marker: bytes) -> bytes:
    data = b""
    while marker not in data:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
    return data


def parse_headers(raw: bytes) -> dict[str, str]:
    text = raw.decode("latin-1")
    headers = {}
    for line in text.split("\r\n")[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    return headers


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))
server.listen(1)
port = server.getsockname()[1]
seen = {}


def serve():
    conn, addr = server.accept()
    conn.settimeout(3)
    request = recv_until(conn, b"\r\n\r\n")
    headers = parse_headers(request)
    seen["headers"] = headers

    key = headers.get("sec-websocket-key", "")
    accept = accept_key(key)
    seen["accept"] = accept

    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n"
        "\r\n"
    )
    conn.sendall(response.encode("ascii"))
    time.sleep(0.05)
    conn.close()


thread = threading.Thread(target=serve, daemon=True)
thread.start()

# ---------------- 客户端握手 ----------------
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(3)
client.connect(("127.0.0.1", port))

client_key = base64.b64encode(b"0123456789abcdef").decode("ascii")   # 16 字节随机
request = (
    "GET /chat HTTP/1.1\r\n"
    f"Host: 127.0.0.1:{port}\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {client_key}\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    "\r\n"
)
client.sendall(request.encode("ascii"))
response = recv_until(client, b"\r\n\r\n")
client.close()

print("== 客户端请求头 ==")
for line in request.split("\r\n"):
    if line:
        print("  ", line)

print("\n== 服务端响应 ==")
print("  ", response.decode("latin-1").replace("\r\n", "\n  ").strip())

# ---------------- 校验 ----------------
print("\n== 校验 ==")
status = response.split(b"\r\n")[0].decode()
headers = parse_headers(response)
expected = accept_key(client_key)
actual = headers.get("sec-websocket-accept")
print("  状态行：", status)
print("  期望 Accept：", expected)
print("  实际 Accept：", actual)
print("  握手成功：", status.startswith("HTTP/1.1 101") and actual == expected)

thread.join(timeout=2)
server.close()

# ---- 握手流程总结 ----
print("\n== 握手流程 ==")
for item in [
    "1. 客户端发 HTTP GET，带 Upgrade 与随机 Key",
    "2. 服务端校验版本/头，计算 Accept",
    "3. 返回 101，连接升级为 WebSocket",
    "4. 之后收发的是 WebSocket 帧（第575课），不再是 HTTP 报文",
    "5. 生产用 wss://（TLS），并校验 Origin 防跨站劫持",
]:
    print("  ", item)

# ---- 安全注意 ----
print("\n== 安全注意 ==")
for item in [
    "服务端要校验 Origin，防恶意网页连接你的 WebSocket",
    "Key 必须随机（16 字节），不能复用",
    "握手阶段可用 Cookie/Token 认证，但注意 CSRF 风险",
    "wss 才能防窃听/中间人",
    "限制消息大小与连接数，防资源耗尽",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 打印服务端收到的全部头，确认 Upgrade/Connection 字段。
# 2. 用错误版本号（12）请求，观察服务端应返回 426。
# 3. 把 Accept 计算写错（去掉 GUID），验证客户端校验失败。
# 4. 思考：为什么 WebSocket 不直接用一个全新的端口/协议？
