# ===== 第571课：实时通信-方案对比与轮询 =====
# 知识点：
#   - 实时通信四种方案：短轮询、长轮询、SSE、WebSocket
#   - 短轮询：客户端定时问“有新消息吗”，实现简单但延迟/浪费请求
#   - 长轮询：服务端 hold 住请求直到有数据或超时，延迟低但占连接
#   - SSE：服务端单向推送（text/event-stream），浏览器原生 EventSource
#   - WebSocket：全双工，握手后双向通信，适合聊天/协作/游戏
#   - 选型：只需要服务端推 → SSE；需要双向 → WebSocket；老环境 → 轮询
#   - 与第39章 HTTP、第17章 socket 的关系
# 依赖：无
import time


class FakeServer:
    """模拟一个“有新消息”的服务端。"""
    def __init__(self):
        self.messages = ["消息1", "消息2", "消息3"]
        self.requests = 0

    def poll(self):
        self.requests += 1
        return self.messages.pop(0) if self.messages else None


# ---------------- 短轮询 ----------------
print("== 短轮询 ==")
server = FakeServer()
received = []
for tick in range(1, 8):
    message = server.poll()
    if message:
        received.append(message)
        print(f"  第 {tick} 次轮询：收到 {message}")
    else:
        print(f"  第 {tick} 次轮询：暂无消息")
    time.sleep(0.01)
print(f"  共请求 {server.requests} 次，收到 {len(received)} 条")
print("  问题：大部分请求是空的，延迟取决于轮询间隔")

# ---------------- 长轮询模拟 ----------------
print("\n== 长轮询（模拟）==")
class LongPollServer:
    def __init__(self):
        self.queue = ["A", "B"]
        self.pending = False

    def poll(self, timeout=0.2):
        # 实际服务端会 hold 住连接；这里用“等待/超时”模拟
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.queue:
                return self.queue.pop(0)
            time.sleep(0.01)
        return None


long_server = LongPollServer()
for i in range(3):
    result = long_server.poll(timeout=0.05)
    print(f"  第 {i + 1} 次长轮询：{result!r}")
print("  有数据立即返回，无数据等到超时；减少空请求但仍占连接")

# ---------------- 方案对比 ----------------
print("\n== 方案对比 ==")
rows = [
    ("短轮询", "简单、兼容好", "延迟高、空请求多", "低频状态刷新"),
    ("长轮询", "延迟较低、兼容好", "占连接、服务端资源", "兼容老浏览器"),
    ("SSE", "浏览器原生、自动重连", "单向、文本协议", "通知/进度/日志"),
    ("WebSocket", "全双工、低开销", "实现复杂、需心跳", "聊天/协作/游戏"),
]
print(f"  {'方案':<10}{'优点':<22}{'缺点':<24}{'场景'}")
for r in rows:
    print(f"  {r[0]:<10}{r[1]:<22}{r[2]:<24}{r[3]}")

# ---------------- 选型清单 ----------------
print("\n== 选型清单 ==")
for item in [
    "只需要服务端推 → SSE（实现比 WebSocket 简单）",
    "需要客户端频繁发消息 → WebSocket",
    "消息频率很低、客户端少 → 短轮询也够",
    "必须兼容非常老的客户端 → 长轮询/短轮询",
    "移动网络频繁断线 → SSE 自带重连更省心",
]:
    print("  -", item)

# ---------------- 延迟与开销 ----------------
print("\n== 延迟与开销 ==")
print("  短轮询：平均延迟 ≈ 轮询间隔 / 2，请求数 = 时长 / 间隔")
print("  长轮询：有数据立即返回，连接数 ≈ 在线用户数")
print("  SSE/WebSocket：长连接，消息即时到达，需心跳保活")

# ===== 练习题 =====
# 1. 把短轮询间隔从 1 秒改成 0.2 秒，计算请求数变化。
# 2. 实现一个“带超时”的长轮询服务端（用 queue.Queue）。
# 3. 列出你常用 App 中哪些功能适合 SSE、哪些适合 WebSocket。
# 4. 思考：为什么“实时”通常不是“零延迟”，而是“可接受的延迟”？
