# ===== 第578课：实时通信-综合案例-实时通知服务 =====
# 知识点：
#   - 综合运用：SSE 服务端（572）+ 订阅/发布（第260课观察者）
#     + HTTP POST 发布 + 队列缓冲 + 优雅关闭
#   - 架构：订阅者建立 SSE 长连接 → 发布者 POST /publish → Hub 广播到所有订阅队列
#   - 每个订阅者一个 queue.Queue，避免慢客户端阻塞其他人
#   - 心跳注释行保持连接；写失败说明客户端断开，清理订阅
#   - 与第260课事件总线、第53章消息队列的区别：这里是浏览器友好的轻量实现
# 依赖：无（标准库）

import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen


class NotificationHub:
    def __init__(self):
        self.subscribers: list[queue.Queue] = []
        self.lock = threading.Lock()
        self.published = 0

    def subscribe(self) -> queue.Queue:
        q = queue.Queue(maxsize=100)
        with self.lock:
            self.subscribers.append(q)
        print(f"  [Hub] 新订阅，当前 {len(self.subscribers)} 个")
        return q

    def unsubscribe(self, q: queue.Queue):
        with self.lock:
            if q in self.subscribers:
                self.subscribers.remove(q)
        print(f"  [Hub] 取消订阅，剩余 {len(self.subscribers)} 个")

    def publish(self, event: dict) -> int:
        with self.lock:
            targets = list(self.subscribers)
            self.published += 1
        delivered = 0
        for q in targets:
            try:
                q.put_nowait(event)
                delivered += 1
            except queue.Full:
                print("  [Hub] 某个订阅者队列满，丢弃该条")
        return delivered


hub = NotificationHub()


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok", "subscribers": len(hub.subscribers)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path != "/events":
            self.send_response(404)
            self.end_headers()
            return

        q = hub.subscribe()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            while True:
                try:
                    event = q.get(timeout=0.5)
                except queue.Empty:
                    # 心跳注释，顺便探测客户端是否还活着
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    continue
                data = json.dumps(event, ensure_ascii=False)
                chunk = f"id: {event.get('id', 0)}\ndata: {data}\n\n"
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ValueError):
            pass
        finally:
            hub.unsubscribe(q)

    def do_POST(self):
        if self.path != "/publish":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            event = json.loads(raw.decode("utf-8"))
        except ValueError:
            self.send_response(400)
            self.end_headers()
            return
        event.setdefault("id", hub.published + 1)
        delivered = hub.publish(event)
        body = json.dumps({"delivered": delivered}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{server.server_address[1]}"

results: dict[str, list] = {"甲": [], "乙": []}


def subscribe(name: str):
    with urlopen(base + "/events", timeout=5) as resp:
        for raw in resp:
            line = raw.decode("utf-8").rstrip("\r\n")
            if line.startswith("data: "):
                event = json.loads(line[6:])
                results[name].append(event)
                print(f"  [{name}] 收到通知：{event}")
                if len(results[name]) >= 2:
                    return


sub1 = threading.Thread(target=subscribe, args=("甲",))
sub2 = threading.Thread(target=subscribe, args=("乙",))
sub1.start()
sub2.start()
time.sleep(0.3)          # 等订阅建立

print("== 发布通知 ==")
for event in (
    {"title": "订单已支付", "order_id": "A001"},
    {"title": "库存不足", "sku": "P1"},
):
    request = Request(
        base + "/publish",
        data=json.dumps(event, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3) as resp:
        print("  ->", resp.read().decode("utf-8"))

sub1.join(timeout=5)
sub2.join(timeout=5)

print("\n== 结果 ==")
for name, events in results.items():
    print(f"  {name} 收到 {len(events)} 条：{[e['title'] for e in events]}")

with urlopen(base + "/health", timeout=3) as resp:
    print("  健康检查：", resp.read().decode("utf-8"))

server.shutdown()
server.server_close()
thread.join(timeout=2)

print("\n== 设计要点 ==")
for item in [
    "每个订阅者独立队列：慢客户端不阻塞其他人",
    "队列设上限：满了丢弃并告警，避免内存涨爆",
    "心跳注释行保持连接，写失败即清理订阅",
    "发布接口返回实际送达人数，便于监控",
    "生产可换 Redis Pub/Sub / Kafka，协议仍是 SSE",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给通知加 topic，订阅时按 topic 过滤。
# 2. 队列满时改成“丢弃最旧的一条”而不是丢弃新消息。
# 3. 增加订阅者鉴权（URL token 或 Cookie）。
# 4. 思考：为什么 SSE 服务端要避免在单个连接上阻塞太久？
