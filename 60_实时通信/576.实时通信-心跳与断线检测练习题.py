# ===== 第576课：实时通信-心跳与断线检测 =====
# 知识点：
#   - 长连接会被 NAT/代理/防火墙静默断开，双方都需要心跳确认存活
#   - WebSocket 协议层：ping（opcode=9）/ pong（opcode=10）
#   - 应用层心跳：定期发 {"type":"ping"}，收到 pong 更新 last_seen
#   - 超时判定：now - last_pong > timeout → 判定断线，清理连接
#   - 心跳间隔要小于中间设备空闲超时（常见 30~60 秒）
#   - 与第443课重试、第573课 SSE 重连的配合
# 依赖：无


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class HeartbeatMonitor:
    """管理一个连接的存活状态。"""

    def __init__(self, interval=5.0, timeout=15.0, clock=FakeClock()):
        self.interval = interval
        self.timeout = timeout
        self.clock = clock
        self.last_pong = clock()
        self.last_ping_sent = None
        self.pings_sent = 0
        self.pongs_received = 0
        self.dead = False

    def maybe_ping(self) -> bool:
        now = self.clock()
        if self.dead:
            return False
        if self.last_ping_sent is None or now - self.last_ping_sent >= self.interval:
            self.last_ping_sent = now
            self.pings_sent += 1
            print(f"  t={now:.1f}s 发送 ping（第 {self.pings_sent} 次）")
            return True
        return False

    def on_pong(self):
        self.pongs_received += 1
        self.last_pong = self.clock()
        print(f"  t={self.clock():.1f}s 收到 pong")

    def check(self) -> bool:
        now = self.clock()
        if not self.dead and now - self.last_pong > self.timeout:
            self.dead = True
            print(f"  t={now:.1f}s 超过 {self.timeout}s 未收到 pong，判定断线")
        return self.dead


clock = FakeClock()
monitor = HeartbeatMonitor(interval=5, timeout=15, clock=clock)

print("== 正常客户端：每次都回 pong ==")
for step in range(1, 7):
    clock.advance(5)
    monitor.maybe_ping()
    if not monitor.check():
        monitor.on_pong()                  # 模拟对端及时响应
print(f"  存活：{not monitor.dead}，ping {monitor.pings_sent}，pong {monitor.pongs_received}")

print("\n== 半死连接：第 3 次 ping 后不再回 pong ==")
clock2 = FakeClock()
monitor2 = HeartbeatMonitor(interval=5, timeout=15, clock=clock2)
for step in range(1, 8):
    clock2.advance(5)
    monitor2.maybe_ping()
    if monitor2.check():
        break
    if step <= 3:
        monitor2.on_pong()
print(f"  判定断线：{monitor2.dead}")

# ---- 心跳参数设计 ----
print("\n== 参数设计 ==")
rows = [
    ("interval", "5~30 秒", "小于中间设备空闲超时"),
    ("timeout", "2~3 × interval", "容忍一次丢包/抖动"),
    ("重连退避", "0.5s 起指数增长", "避免服务端刚恢复被打满"),
]
print(f"  {'参数':<12}{'建议':<20}{'理由'}")
for r in rows:
    print(f"  {r[0]:<12}{r[1]:<20}{r[2]}")

# ---- 协议层 ping/pong 与应用层心跳 ----
print("\n== 协议层 vs 应用层 ==")
rows = [
    ("协议层 ping/pong", "浏览器自动回 pong", "服务端可用；前端 JS 不能主动发 ping"),
    ("应用层 JSON 心跳", "前后端都能控制", "更灵活，可带负载/时间戳"),
]
print(f"  {'方式':<18}{'特点':<26}{'说明'}")
for r in rows:
    print(f"  {r[0]:<18}{r[1]:<26}{r[2]}")

# ---- 断线后的处理 ----
print("\n== 断线后 ==")
for item in [
    "清理该连接的资源（从广播列表移除）",
    "客户端指数退避重连（第443课）",
    "重连后重新订阅/鉴权",
    "用消息 ID 续传，避免漏消息（第573课）",
    "监控断线率，异常升高说明网络或服务端问题",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把 timeout 改成 5 秒，观察多久判定断线。
# 2. 实现“连续丢 2 次 pong 才断开”，降低误判。
# 3. 用真实 socket 发 ping/pong 帧，验证协议层心跳。
# 4. 思考：为什么移动网络下心跳间隔不能太短？
