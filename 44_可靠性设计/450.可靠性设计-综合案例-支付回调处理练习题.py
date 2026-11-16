# ===== 第450课：可靠性设计-综合案例-支付回调处理 =====
# 知识点：
#   - 综合运用：幂等（447）+ 重试（443）+ 熔断（445）+ 死信（448）
#   - 支付回调的三个必须：验签、幂等、快速响应（否则对方一直重发）
#   - 本课模拟：重复回调、临时故障、持续故障、恢复后重放
#   - 目标：同一条回调只处理一次；失败不丢单；故障时不拖垮系统
import sqlite3
import time
from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    CLOSED = "关闭"
    OPEN = "熔断"
    HALF_OPEN = "半开"


class CircuitBreaker:

    def __init__(self, threshold=3, recovery=0.2, clock=time.monotonic):
        self.threshold, self.recovery, self.clock = threshold, recovery, clock
        self.state, self.failures, self.opened_at = State.CLOSED, 0, 0.0

    def allow(self):
        if self.state is State.OPEN:
            if self.clock() - self.opened_at >= self.recovery:
                self.state = State.HALF_OPEN
                print("  [熔断器] OPEN → HALF_OPEN")
                return True
            return False
        return True

    def on_success(self):
        if self.state is State.HALF_OPEN:
            self.state = State.CLOSED
            self.failures = 0
            print("  [熔断器] HALF_OPEN → CLOSED")
        else:
            self.failures = 0

    def on_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = State.OPEN
            self.opened_at = self.clock()
            print(f"  [熔断器] → OPEN（连续失败 {self.failures} 次）")


@dataclass
class Callback:
    callback_id: str
    order_id: str
    amount: float
    attempts: int = 0


@dataclass
class PaymentGateway:
    healthy: bool = False
    charges: list = field(default_factory=list)
    calls: int = 0

    def charge(self, callback):
        self.calls += 1
        if not self.healthy:
            raise ConnectionError("支付网关不可用")
        self.charges.append((callback.order_id, callback.amount))
        return f"charge_{len(self.charges):03d}"


class PaymentCallbackHandler:

    def __init__(self, gateway, breaker, max_retries=3):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE processed (
                callback_id TEXT PRIMARY KEY,
                order_id TEXT,
                result TEXT,
                processed_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE dead_letters (
                callback_id TEXT PRIMARY KEY,
                order_id TEXT,
                amount REAL,
                error TEXT,
                attempts INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        self.gateway = gateway
        self.breaker = breaker
        self.max_retries = max_retries
        self.stats = {"duplicate": 0, "success": 0, "dead": 0, "fast_fail": 0}

    def handle(self, cb: Callback):
        # 1) 幂等：已处理过直接返回
        row = self.conn.execute(
            "SELECT result FROM processed WHERE callback_id = ?", (cb.callback_id,)
        ).fetchone()
        if row:
            self.stats["duplicate"] += 1
            print(f"  [重复] {cb.callback_id} 已处理，返回 {row['result']}")
            return "duplicate"

        # 2) 熔断：打开时快速失败，进死信
        if not self.breaker.allow():
            self.stats["fast_fail"] += 1
            self._dead_letter(cb, "熔断器打开，快速失败")
            return "fast_fail"

        # 3) 重试
        for attempt in range(1, self.max_retries + 1):
            cb.attempts = attempt
            try:
                result = self.gateway.charge(cb)
            except Exception as exc:
                self.breaker.on_failure()
                print(f"  [失败] {cb.callback_id} 第 {attempt} 次：{exc}")
                if attempt == self.max_retries:
                    self._dead_letter(cb, str(exc))
                    return "dead"
                time.sleep(0.02)
            else:
                self.breaker.on_success()
                self.conn.execute(
                    "INSERT INTO processed (callback_id, order_id, result) VALUES (?, ?, ?)",
                    (cb.callback_id, cb.order_id, result),
                )
                self.conn.commit()
                self.stats["success"] += 1
                print(f"  [成功] {cb.callback_id} → {result}（尝试 {attempt} 次）")
                return "success"

    def _dead_letter(self, cb, error):
        self.conn.execute("""
            INSERT OR REPLACE INTO dead_letters
            (callback_id, order_id, amount, error, attempts) VALUES (?, ?, ?, ?, ?)
        """, (cb.callback_id, cb.order_id, cb.amount, error, cb.attempts))
        self.conn.commit()
        self.stats["dead"] += 1
        print(f"  [死信] {cb.callback_id}：{error}")

    def replay(self):
        rows = self.conn.execute("SELECT * FROM dead_letters").fetchall()
        for r in rows:
            cb = Callback(r["callback_id"], r["order_id"], r["amount"], r["attempts"])
            print(f"\n  [重放] {cb.callback_id}")
            result = self.handle(cb)
            if result in ("success", "duplicate"):
                self.conn.execute(
                    "DELETE FROM dead_letters WHERE callback_id = ?", (cb.callback_id,))
                self.conn.commit()

    def close(self):
        self.conn.close()


# ---------------- 场景编排 ----------------
gateway = PaymentGateway(healthy=False)
breaker = CircuitBreaker(threshold=3, recovery=0.2)
handler = PaymentCallbackHandler(gateway, breaker)

callbacks = [
    Callback("CB1", "ORDER-1", 99),
    Callback("CB1", "ORDER-1", 99),          # 重复投递
    Callback("CB2", "ORDER-2", 199),
    Callback("CB3", "ORDER-3", 299),
    Callback("CB4", "ORDER-4", 399),         # 熔断期间 → 快速失败
    Callback("CB5", "ORDER-5", 499),
]

print("== 阶段 1：网关故障，连续回调 ==")
for cb in callbacks:
    print(f"\n处理 {cb.callback_id}")
    handler.handle(cb)

print(f"\n统计：{handler.stats}")
print(f"网关真实调用次数：{gateway.calls}")

print("\n== 阶段 2：网关恢复，重放死信 ==")
gateway.healthy = True
time.sleep(0.25)                              # 等熔断恢复窗口
handler.replay()

print("\n== 最终结果 ==")
print("已处理订单：", [dict(r) for r in handler.conn.execute(
    "SELECT order_id, result FROM processed ORDER BY order_id")])
print("剩余死信：", [dict(r) for r in handler.conn.execute(
    "SELECT callback_id, order_id, error FROM dead_letters")])
print("真实扣款：", gateway.charges)
print("统计：", handler.stats)

handler.close()

# 结论：
#   重复回调被幂等拦截；故障期失败进死信；恢复后重放成功；
#   每个订单最终只扣款一次。

# ===== 练习题 =====
# 1. 给回调加“验签”：HMAC 校验（第267课），签名错直接 401。
# 2. 把重试改成指数退避 + 抖动（第443课）。
# 3. 给死信加重放次数上限，超过后标记“需人工处理”。
# 4. 思考：回调接口为什么必须“先返回 200 再异步处理”？同步处理会怎样？
