# ===== 第572课：实时通信-SSE服务端推送 =====
# 知识点：
#   - SSE（Server-Sent Events）：服务端通过一个长连接持续推送文本事件
#   - 响应头：Content-Type: text/event-stream、Cache-Control: no-cache
#   - 事件格式：field: value，行之间用 \n，事件之间用空行分隔
#   - 常用字段：data（数据）、event（事件名）、id（事件 ID）、retry（重连间隔）
#   - 浏览器用 EventSource 自动解析与重连；Python 客户端逐行读取
#   - 单向：服务端 → 客户端；客户端要发消息需另开接口
#   - 与第39章 http.server 的流式响应配合
# 依赖：无（http.server / urllib）

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/events":
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            for i in range(1, 6):
                payload = json.dumps({"seq": i, "text": f"事件{i}"}, ensure_ascii=False)
                chunk = (
                    f"id: {i}\n"
                    f"event: notice\n"
                    f"data: {payload}\n\n"
                )
                self.wfile.write(chunk.encode("utf-8"))
                self.wfile.flush()
                time.sleep(0.03)
        except (BrokenPipeError, ConnectionResetError):
            print("  [服务端] 客户端已断开，停止推送")

    def log_message(self, *args):
        pass


server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{server.server_address[1]}"

print("== 客户端读取 SSE ==")
events = []
try:
    with urlopen(base + "/events", timeout=5) as resp:
        print("  Content-Type:", resp.headers.get("Content-Type"))
        current = {}
        while len(events) < 3:
            raw = resp.readline()
            if not raw:
                break
            line = raw.decode("utf-8").rstrip("\r\n")
            if line == "":
                if current:
                    events.append(current)
                    current = {}
                continue
            if ":" in line:
                field, value = line.split(":", 1)
                current[field.strip()] = value.strip()
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)

print("\n== 解析出的事件 ==")
for event in events:
    print("  ", event)
    data = json.loads(event["data"])
    print(f"     序号 {data['seq']}，内容 {data['text']}")

# ---- 事件格式说明 ----
print("\n== 事件格式 ==")
print("""
id: 1
event: notice
data: {"seq": 1, "text": "事件1"}

id: 2
event: notice
data: {"seq": 2, "text": "事件2"}
""")
print("  空行是事件分隔符；一个事件可以有多行 data（用 \\n 连接）")

# ---- 注意事项 ----
print("\n== 注意事项 ==")
for item in [
    "必须是 text/event-stream，否则浏览器不会按 SSE 解析",
    "关闭代理缓冲（Nginx 要 proxy_buffering off）",
    "长时间无数据要发注释行（: keep-alive）防超时",
    "客户端断开后服务端要停止推送，避免 BrokenPipe",
    "SSE 是单向的；客户端发消息另开 POST 接口",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给事件加 retry: 3000 字段，说明客户端重连间隔。
# 2. 服务端每 100ms 发一条心跳注释，模拟保活。
# 3. 用 curl -N 观察 SSE 流式输出。
# 4. 思考：SSE 与 WebSocket 在“自动重连”上的差异？
