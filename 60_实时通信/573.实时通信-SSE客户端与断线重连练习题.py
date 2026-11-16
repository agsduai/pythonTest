# ===== 第573课：实时通信-SSE客户端与断线重连 =====
# 知识点：
#   - SSE 客户端要解析：id / event / data / retry 字段
#   - 断线后带 Last-Event-ID 重连，服务端从该 ID 之后继续发
#   - 重连要有退避（第443课），避免服务端刚恢复就被打满
#   - 客户端要处理重复事件（第447课幂等）
#   - Python 没有内置 EventSource，手写解析可以完全控制重连逻辑
#   - 与第572课服务端配合：服务端读取 Last-Event-ID 决定起点
# 依赖：无（http.server / urllib）

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from urllib.request import Request, urlopen

EVENTS = [
    {"id": 1, "data": "订单已创建"},
    {"id": 2, "data": "支付成功"},
    {"id": 3, "data": "已发货"},
    {"id": 4, "data": "已签收"},
    {"id": 5, "data": "评价完成"},
]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/events":
            self.send_response(404)
            self.end_headers()
            return

        last_id = int(self.headers.get("Last-Event-ID", "0"))
        # 每次连接只发 3 条，模拟“发着发着断开”
        batch = [e for e in EVENTS if e["id"] > last_id][:3]

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            for event in batch:
                chunk = (
                    f"id: {event['id']}\n"
                    f"event: order\n"
                    f"data: {json.dumps(event['data'], ensure_ascii=False)}\n"
                    f"retry: 500\n\n"
                )
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()
                time.sleep(0.02)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, *args):
        pass


def parse_sse(lines):
    """把逐行输入解析成事件字典。"""
    current = {}
    for raw in lines:
        line = raw.decode("utf-8").rstrip("\r\n") if isinstance(raw, bytes) else raw.rstrip()
        if line == "":
            if current:
                yield current
                current = {}
            continue
        if line.startswith(":"):
            continue                              # 注释/心跳
        if ":" in line:
            field, value = line.split(":", 1)
            current[field.strip()] = value.strip()


class SSEClient:
    def __init__(self, url: str, max_reconnects: int = 3):
        self.url = url
        self.max_reconnects = max_reconnects
        self.last_id = 0
        self.processed = set()

    def stream(self):
        reconnects = 0
        while reconnects <= self.max_reconnects:
            headers = {}
            if self.last_id:
                headers["Last-Event-ID"] = str(self.last_id)
            request = Request(self.url, headers=headers)
            try:
                with urlopen(request, timeout=5) as resp:
                    for event in parse_sse(resp):
                        event_id = int(event.get("id", 0))
                        if event_id <= self.last_id:
                            continue               # 幂等：跳过重复
                        self.last_id = event_id
                        yield event
            except (URLError, TimeoutError, OSError) as exc:
                print(f"  [连接断开] {type(exc).__name__}: {exc}")
            if self.last_id >= EVENTS[-1]["id"]:
                return
            reconnects += 1
            delay = min(0.5, 0.05 * 2 ** reconnects)   # 指数退避
            print(f"  [重连 {reconnects}] 从 id={self.last_id} 继续，等待 {delay:.2f}s")
            time.sleep(delay)
        print("  [放弃] 达到最大重连次数")


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{server.server_address[1]}"

print("== 客户端接收（自动重连）==")
client = SSEClient(base + "/events")
received = []
try:
    for event in client.stream():
        received.append(event)
        print(f"  收到 id={event.get('id')} event={event.get('event')} "
              f"data={event.get('data')} retry={event.get('retry')}")
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)

print(f"\n共收到 {len(received)} 条，最后 id={client.last_id}")
print("  说明：每次连接只发 3 条，客户端靠 Last-Event-ID 续传，最终拿到全部 5 条")

# ---- SSE 客户端实现清单 ----
print("\n== 实现清单 ==")
for item in [
    "记录 last_id，重连时放进 Last-Event-ID 请求头",
    "解析多行 data（按 \\n 拼接）",
    "忽略注释行（: 开头）与空事件",
    "按 retry 字段调整重连间隔，并加指数退避",
    "用事件 ID 去重，避免重连后重复处理",
    "设置读取超时，避免永久挂起",
]:
    print("  -", item)

# ---- 与浏览器 EventSource 对比 ----
print("\n== 与浏览器 EventSource ==")
print("  EventSource 自动重连、自动解析、自动带 Last-Event-ID")
print("  但它不能自定义请求头（如 Authorization），需要 Cookie 或 URL token")
print("  Python 手写客户端可以完全控制认证、重试与日志")

# ===== 练习题 =====
# 1. 把每次连接批量改成 1 条，观察重连次数与退避。
# 2. 模拟服务端 500 错误，验证客户端会重试并最终放弃。
# 3. 给客户端增加 on_event 回调，而不是 yield。
# 4. 思考：为什么“至少一次 + 幂等”比“追求恰好一次”更现实？
