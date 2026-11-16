# ===== 第519课：消息队列与事件驱动-死信队列 =====
# 知识点：
#   - 死信队列（DLQ）：重试仍失败的消息集中存放，不阻塞主队列
#   - 进入 DLQ 的常见原因：处理代码 bug、数据格式错误、下游长期不可用
#   - 消息要带：原始内容、错误原因、尝试次数、首次/最后失败时间
#   - 重放（replay）：修复后从 DLQ 取回，走同一套处理逻辑
#   - 重放必须幂等（第447课），并限速，避免再次打垮下游
#   - 与第448课“补偿”的区别：DLQ 是消息层面，补偿是业务层面
import time


class Message:
    def __init__(self, msg_id, payload):
        self.id = msg_id
        self.payload = payload
        self.attempts = 0
        self.last_error = None


class DLQ:
    def __init__(self):
        self.items = []

    def add(self, msg: Message):
        self.items.append(msg)
        print(f"  [DLQ] {msg.id} 进入死信（尝试 {msg.attempts} 次）：{msg.last_error}")

    def replay(self, handler, max_count=10):
        ok, remain = 0, []
        for msg in self.items[:max_count]:
            try:
                handler(msg)
                ok += 1
                print(f"  [重放成功] {msg.id}")
            except Exception as exc:
                msg.last_error = str(exc)
                remain.append(msg)
                print(f"  [重放失败] {msg.id}: {exc}")
        self.items = remain + self.items[max_count:]
        return ok, len(self.items)


class Consumer:
    def __init__(self, dlq: DLQ, max_attempts=3):
        self.dlq = dlq
        self.max_attempts = max_attempts
        self.processed = []
        self.failed = []

    def process(self, msg: Message):
        msg.attempts += 1
        try:
            if "bad" in msg.payload:
                raise ValueError("数据格式错误：缺少 order_id")
            if "timeout" in msg.payload:
                raise ConnectionError("下游服务超时")
            self.processed.append(msg.payload)
            print(f"  [成功] {msg.id}: {msg.payload}")
            return True
        except Exception as exc:
            msg.last_error = str(exc)
            self.failed.append(msg.id)
            print(f"  [失败] {msg.id} 第 {msg.attempts} 次：{exc}")
            if msg.attempts >= self.max_attempts:
                self.dlq.add(msg)
            return False


print("== 正常与失败消息 ==")
dlq = DLQ()
consumer = Consumer(dlq, max_attempts=3)

messages = [
    Message("M1", "order-1"),
    Message("M2", "bad-order"),
    Message("M3", "order-3"),
    Message("M4", "timeout-order"),
]
for msg in messages:
    consumer.process(msg)

print("\n== 重试失败的消息 ==")
# 对未进 DLQ 的消息重试（模拟主队列重投）
for msg in messages:
    if msg.id not in consumer.processed and msg not in dlq.items:
        consumer.process(msg)

print(f"\n统计：成功 {len(consumer.processed)}，DLQ {len(dlq.items)} 条")
for msg in dlq.items:
    print(f"  {msg.id}: {msg.payload} | {msg.last_error} | 尝试 {msg.attempts} 次")

# ---- 修复后重放 ----
print("\n== 修复下游后重放 ==")
def fixed_handler(msg: Message):
    # 模拟修复：bad 消息补上缺失字段，timeout 消息下游恢复
    if "bad" in msg.payload:
        msg.payload = msg.payload.replace("bad-", "")
        print(f"    [修复] 补全字段 → {msg.payload}")
    # 处理
    print(f"    [处理] {msg.payload}")
    consumer.processed.append(msg.payload)


ok, remain = dlq.replay(fixed_handler)
print(f"  重放成功 {ok} 条，剩余 {remain} 条")

# ---- DLQ 管理 ----
print("\n== DLQ 管理清单 ==")
for item in [
    "按原因分类统计（格式错误 vs 下游故障）",
    "设置最大保留时间，避免无限增长",
    "重放要限速，并监控重放后的失败率",
    "告警：DLQ 数量突增通常意味着系统性问题",
    "死信内容脱敏（可能含用户手机号/地址）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给 DLQ 增加按 last_error 分类统计。
# 2. 实现“只重放格式错误的消息”，下游故障消息继续等待。
# 3. 给 Message 增加 first_failed_at/last_failed_at 时间戳。
# 4. 思考：死信重放和“直接重新入队”有什么本质区别？
