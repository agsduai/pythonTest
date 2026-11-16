# ===== 第577课：实时通信-WebSocket广播聊天室 =====
# 知识点：
#   - 广播：服务端维护所有在线连接，收到消息后发给每个客户端
#   - 共享连接列表要加锁（第196课），遍历时用快照避免并发修改
#   - 每个连接一个线程读帧；发送时也要加锁，避免多线程写同一 socket
#   - 客户端断开（收到 close 或异常）要从列表移除并关闭
#   - 与第243课 TCP 聊天室的区别：这里是 WebSocket 帧 + 握手，浏览器可直接连
#   - 生产还要加：鉴权、房间/频道、限流、消息持久化
# 依赖：无（socket/threading）
import base64
import hashlib
import os
import socket
import struct
import threading

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
clients: list[tuple[socket.socket, str]] = []
clients_lock = threading.Lock()


def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf


def build_frame(payload: bytes, opcode=1, mask=False):
    header = bytearray([0x80 | opcode])
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


def parse_frame(sock):
    b1, b2 = recv_exact(sock, 2)
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
    return opcode, payload


def handshake(conn):
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
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
    ).encode())


def broadcast(message: str, sender=None):
    data = build_frame(message.encode("utf-8"), opcode=1, mask=False)
    with clients_lock:
        targets = list(clients)
    for conn, name in targets:
        try:
            conn.sendall(data)
        except OSError:
            remove_client(conn, name)


def remove_client(conn, name):
    removed = False
    with clients_lock:
        if (conn, name) in clients:
            clients.remove((conn, name))
            removed = True
    try:
        conn.close()
    except OSError:
        pass
    if removed:
        print(f"  [服务端] {name} 离开，当前在线 {len(clients)}")


def handle_client(conn, name):
    handshake(conn)
    with clients_lock:
        clients.append((conn, name))
    broadcast(f"系统：{name} 加入，当前 {len(clients)} 人")
    try:
        while True:
            opcode, payload = parse_frame(conn)
            if opcode == 8:               # close
                break
            if opcode == 1:               # text
                text = payload.decode("utf-8")
                print(f"  [服务端] {name}: {text}")
                broadcast(f"{name}: {text}")
    except (ConnectionError, OSError):
        pass
    finally:
        remove_client(conn, name)


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))
server.listen(5)
port = server.getsockname()[1]


def accept_loop():
    next_id = 0
    while next_id < 2:
        conn, addr = server.accept()
        conn.settimeout(5)
        name = f"用户{next_id}"
        next_id += 1
        threading.Thread(target=handle_client, args=(conn, name), daemon=True).start()


threading.Thread(target=accept_loop, daemon=True).start()


def client(name: str, messages: list[str]):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect(("127.0.0.1", port))
    key = base64.b64encode(os.urandom(16)).decode()
    sock.sendall((
        "GET /chat HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{port}\r\n"
        "Upgrade: websocket\r\nConnection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n\r\n"
    ).encode())
    data = b""
    while b"\r\n\r\n" not in data:
        data += sock.recv(4096)

    for text in messages:
        sock.sendall(build_frame(text.encode("utf-8"), opcode=1, mask=True))
        # 读两条广播（自己的 + 对方的）
        for _ in range(2):
            opcode, payload = parse_frame(sock)
            if opcode == 1:
                print(f"  [{name} 收到] {payload.decode('utf-8')}")
    sock.sendall(build_frame(b"", opcode=8, mask=True))
    sock.close()


c1 = threading.Thread(target=client, args=("小明", ["大家好"]))
c2 = threading.Thread(target=client, args=("小红", ["你好呀"]))
c1.start()
c2.start()
c1.join()
c2.join()
threading.Event().wait(0.1)

server.close()

print("\n== 聊天室要点 ==")
for item in [
    "连接列表加锁，广播用快照避免遍历中修改",
    "每个连接独立线程读，发送统一加锁（本课用列表快照）",
    "收到 close 或异常要移除并关闭",
    "生产要加鉴权、房间、限流、消息持久化（第53章）",
    "广播风暴：大房间要分片/分频道，避免 O(n) 全量发送",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 增加“房间”概念：只广播给同一房间的客户端。
# 2. 给消息加时间戳与发送者昵称。
# 3. 限制每个客户端每秒最多发 5 条（第446课）。
# 4. 思考：为什么“给每个连接一个线程”不适合万人聊天室？
