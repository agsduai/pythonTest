# ===== 第448课：可靠性设计-死信队列与补偿 =====
# 知识点：
#   - 死信队列（DLQ）：重试仍失败的消息集中存放，不再拖住主流程
#   - 补偿：已经成功的步骤，在后续失败时要做“反向操作”（如退款）
#   - 处理流程：尝试 → 失败重试 → 仍失败进死信 → 人工/定时重放
#   - 死信要带上下文：原始消息、错误原因、失败次数、时间
#   - 重放要幂等（第447课），否则会重复扣款
import time
from dataclasses import dataclass, field


@dataclass
class Message:
    msg_id: str
    action: str
    payload: dict
    attempts: int = 0
    error: str | None = None


@dataclass
class DeadLetterQueue:
    messages: list[Message] = field(default_factory=list)

    def add(self, msg: Message, error: str):
        msg.error = error
        self.messages.append(msg)
        print(f"  [DLQ] {msg.msg_id} 进入死信：{error}")

    def replay(self, handler, max_replay: int = 10):
        """重放死信：成功则移出，仍失败保留。"""
        succeeded, remaining = [], []
        for msg in self.messages[:max_replay]:
            try:
                handler(msg)
                succeeded.append(msg)
                print(f"  [重放成功] {msg.msg_id}")
            except Exception as exc:
                msg.attempts += 1
                msg.error = str(exc)
                remaining.append(msg)
                print(f"  [重放失败] {msg.msg_id}: {exc}")
        self.messages = remaining + self.messages[max_replay:]
        return len(succeeded), len(self.messages)


class OrderService:
    """模拟下单：扣库存 → 扣款 → 发券。任一步失败要补偿前面的步骤。"""

    def __init__(self):
        self.stock = {"sku-1": 10}
        self.payments = []
        self.coupons = []
        self.compensations = []
        self.fail_payment = False

    def process(self, msg: Message):
        msg.attempts += 1
        sku = msg.payload["sku"]
        if self.stock.get(sku, 0) <= 0:
            raise RuntimeError("库存不足")

        # 步骤 1：扣库存
        self.stock[sku] -= 1
        try:
            # 步骤 2：扣款（可注入故障）
            if self.fail_payment:
                raise RuntimeError("支付网关超时")
            self.payments.append((msg.msg_id, msg.payload["amount"]))

            # 步骤 3：发券
            self.coupons.append(msg.msg_id)
            return f"订单 {msg.msg_id} 完成"
        except Exception:
            # 补偿：把库存加回去
            self.stock[sku] += 1
            self.compensations.append((msg.msg_id, "库存已回滚"))
            raise


def process_with_retry(service: OrderService, msg: Message, dlq: DeadLetterQueue,
                       max_retries: int = 2):
    for attempt in range(1, max_retries + 1):
        try:
            result = service.process(msg)
            print(f"  [成功] {msg.msg_id}（尝试 {attempt} 次）：{result}")
            return True
        except Exception as exc:
            print(f"  [失败] {msg.msg_id} 第 {attempt} 次：{exc}")
            if attempt == max_retries:
                dlq.add(msg, str(exc))
                return False
            time.sleep(0.01)
    return False


service = OrderService()
dlq = DeadLetterQueue()

print("== 正常消息 ==")
process_with_retry(service, Message("M1", "create_order", {"sku": "sku-1", "amount": 99}), dlq)

print("\n== 支付故障：重试后进死信，库存被补偿 ==")
service.fail_payment = True
process_with_retry(service, Message("M2", "create_order", {"sku": "sku-1", "amount": 199}), dlq)
print("  当前库存：", service.stock)
print("  补偿记录：", service.compensations)

print("\n== 死信重放：故障已修复 ==")
service.fail_payment = False
ok, left = dlq.replay(lambda m: service.process(m))
print(f"  重放成功 {ok} 条，剩余死信 {left} 条")
print("  最终库存：", service.stock, "| 支付记录：", service.payments)

# ---- 死信内容示例 ----
print("\n== 死信记录 ==")
for msg in dlq.messages:
    print("  ", msg)
print("  （重放成功后已从队列移除）")

# ---- 设计清单 ----
print("\n== 死信队列设计清单 ==")
for item in [
    "最大重试次数：3~5 次，指数退避（第443课）",
    "死信带原始消息 + 错误堆栈 + 尝试次数 + 时间戳",
    "重放要幂等（第447课），且限速，避免再次打垮下游",
    "死信数量要监控告警（第417课），持续增长说明系统性问题",
    "补偿操作要可重入：重复执行不出错（如“库存 +1”要防重复）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给死信队列加“最大容量”，满了丢弃最旧的并告警。
# 2. 给补偿加幂等：同一条消息只回滚一次库存。
# 3. 把死信持久化到 SQLite（第13章），重启后还能重放。
# 4. 思考：什么情况下“补偿”比“回滚”更合适？
