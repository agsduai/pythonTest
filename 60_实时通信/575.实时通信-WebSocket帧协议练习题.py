# ===== 第575课：实时通信-WebSocket帧协议 =====
# 知识点：
#   - 握手后传输的是“帧”：FIN + opcode + mask + payload length + payload
#   - opcode：1=文本、2=二进制、8=关闭、9=ping、10=pong
#   - 客户端发往服务端的帧必须 Mask（4 字节掩码异或），服务端帧不掩码
#   - 长度：<=125 直接放；126 用 2 字节扩展；127 用 8 字节扩展
#   - 接收要循环读满（TCP 是字节流，一次 recv 不保证一帧完整）
#   - 与第242课“粘包/长度前缀”的思想一致：必须自己界定消息边界
# 依赖：无（socket/struct/os）
import base64
import hashlib
import os
import socket
import struct
import threading
import time

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("连接已关闭")
        buf += chunk
    return buf


def build_frame(payload: bytes, opcode: int = 1, mask: bool = False) -> bytes:
    header = bytearray([0x80 | opcode])       # FIN=1
    length = len(payload)
    mask_bit = 0x80 if mask else 0
    if length < 126:
        header.append(mask_bit | length)
    elif length < 65536:
        header.append(mask_bit | 126)
        header += struct.pack("!H", length)
    else:
        header.append(mask_bit | 127)
        header += struct.pack("!Q", length)

    if mask:
        key = os.urandom(4)
        header += key
        payload = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    return bytes(header) + payload


def parse_frame(sock: socket.socket):
    b1, b2 = recv_exact(sock, 2)
    fin = (b1 >> 7) & 1
    opcode = b1 & 0x0F
    masked = (b2 >> 7) & 1
    length = b2 & 0x7F

    if length == 126:
        length = struct.unpack("!H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", recv_exact(sock, 8))[0]

    key = recv_exact(sock, 4) if masked else None
    payload = recv_exact(sock, length)
    if masked:
        payload = bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    return fin, opcode, payload


def handshake_server(conn):
    data = b""
    while b"\r\n\r\n" not in data:
        data += conn.recv(4096)
    headers = {}
    for line in data.decode("latin-1").split("\r\n")[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    accept = base64.b64encode(
        hashlib.sha1((headers["sec-websocket-key"] + GUID).encode()).digest()
    ).decode()
    conn.sendall((
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
    ).encode())


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))
server.listen(1)
port = server.getsockname()[1]
received = []


def serve():
    conn, _ = server.accept()
    conn.settimeout(3)
    handshake_server(conn)
    for _ in range(2):
        fin, opcode, payload = parse_frame(conn)
        text = payload.decode("utf-8")
        received.append((opcode, text))
        print(f"  [服务端] 收到 opcode={opcode} 文本={text!r}")
        conn.sendall(build_frame(f"echo: {text}".encode("utf-8"), opcode=1, mask=False))
    conn.close()


thread = threading.Thread(target=serve, daemon=True)
thread.start()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(3)
client.connect(("127.0.0.1", port))
key = base64.b64encode(os.urandom(16)).decode()
client.sendall((
    "GET /ws HTTP/1.1\r\n"
    f"Host: 127.0.0.1:{port}\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {key}\r\n"
    "Sec-WebSocket-Version: 13\r\n\r\n"
).encode())
# 读掉 101 响应
data = b""
while b"\r\n\r\n" not in data:
    data += client.recv(4096)
print("== 握手完成 ==", data.split(b"\r\n")[0].decode())

print("\n== 发送帧（客户端必须掩码）==")
for text in ("你好，WebSocket", "第二条消息"):
    client.sendall(build_frame(text.encode("utf-8"), opcode=1, mask=True))
    fin, opcode, payload = parse_frame(client)
    print(f"  [客户端] 收到 opcode={opcode} 文本={payload.decode('utf-8')!r}")

client.close()
thread.join(timeout=2)
server.close()

print("\n== 服务端记录 ==", received)

# ---- 帧结构表 ----
print("\n== 帧结构 ==")
rows = [
    ("FIN", "1 bit", "是否是消息的最后一帧"),
    ("opcode", "4 bit", "1 文本 / 2 二进制 / 8 关闭 / 9 ping / 10 pong"),
    ("MASK", "1 bit", "客户端→服务端必须为 1"),
    ("payload len", "7 bit", "<=125 直接表示；126/127 表示扩展长度"),
    ("masking key", "4 字节", "仅 MASK=1 时存在"),
    ("payload", "变长", "实际数据（可能被掩码异或）"),
]
print(f"  {'字段':<14}{'长度':<10}{'含义'}")
for r in rows:
    print(f"  {r[0]:<14}{r[1]:<10}{r[2]}")

# ---- 注意 ----
print("\n== 注意 ==")
for item in [
    "TCP 不保证一次 recv 读到完整帧，必须 recv_exact",
    "客户端帧必须掩码，服务端帧不能掩码（否则浏览器断开）",
    "大消息分片：FIN=0 的后续帧，opcode=0 表示延续",
    "payload 是字节，文本要 UTF-8 编解码",
    "关闭要发 close 帧（opcode=8），不要直接断 TCP",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 发送一条 200 字节的消息，验证 126 扩展长度分支。
# 2. 实现 close 帧（opcode=8）并让服务端优雅退出。
# 3. 故意不掩码发送，观察服务端解析结果（模拟错误客户端）。
# 4. 思考：为什么 WebSocket 要自己定义帧，而不直接发 JSON 文本？
