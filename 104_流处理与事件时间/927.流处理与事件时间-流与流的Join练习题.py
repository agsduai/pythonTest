# ===== 第927课：流处理与事件时间-流与流的Join =====
# 知识点：
#   - 流-流 Join：两条流的事件按 key 匹配 —— 双方都要缓冲等对方
#   - 时间边界：区间 Join（双方事件时间差 ≤ timeout）用 watermark 释缓冲
#   - 流-表 Join：维表（changelog）找历史版本 —— 事件时间一致性读取
#   - 状态规模 = 活跃 key 数 × 缓冲时长 —— Join 的核心成本
#   - 外 Join 的超时补发：等不到对方时发 (key, NULL)
# 依赖：无（标准库）
import random
from collections import defaultdict


class StreamStreamJoin:
    """订单流 × 支付流 按 order_id 的区间 Join（超时 20 个时间单位）。
    水印推进后清理过期缓冲；超时补发 NULL（外 Join 语义）。"""

    def __init__(self, timeout=20):
        self.timeout = timeout
        self.buffer = {"orders": {}, "payments": {}}   # key -> (et, payload)
        self.max_et = None
        self.results = []                              # 匹配结果
        self.null_results = []                         # 超时未匹配
        self.matched_keys = set()

    def watermark(self):
        return self.max_et

    def _try_join(self, key):
        o = self.buffer["orders"].get(key)
        p = self.buffer["payments"].get(key)
        if o is None or p is None:
            return
        o_et, o_val = o
        p_et, p_val = p
        if abs(o_et - p_et) <= self.timeout:
            self.results.append((key, o_val, p_val, abs(o_et - p_et)))
            self.matched_keys.add(key)
            self.buffer["orders"].pop(key, None)
            self.buffer["payments"].pop(key, None)

    def process(self, side, key, et, payload):
        self.max_et = et if self.max_et is None else max(self.max_et, et)
        self.buffer[side][key] = (et, payload)
        self._try_join(key)
        # 水印推进：把等待超时的 key 补发 NULL 并清理
        if self.max_et is not None:
            for k in list(self.buffer["orders"]):
                if self.max_et - self.buffer["orders"][k][0] > self.timeout:
                    if k not in self.matched_keys:
                        self.null_results.append((k, "order 无支付"))
                    self.buffer["orders"].pop(k, None)
            for k in list(self.buffer["payments"]):
                if self.max_et - self.buffer["payments"][k][0] > self.timeout:
                    if k not in self.matched_keys:
                        self.null_results.append((k, "支付 无订单"))
                    self.buffer["payments"].pop(k, None)


class StreamTableJoin:
    """订单流 × 变更维表（商品价格）：按事件时间读取维表版本。"""

    def __init__(self):
        self.changelog = []                   # (生效事件时间, 商品, 价格)
        self.results = []

    def update_table(self, et, product, price):
        self.changelog.append((et, product, price))
        self.changelog.sort()

    def price_at(self, product, et):
        """事件时间一致性读取：找 ≤ et 的最近版本。"""
        best = None
        for t, prod, price in self.changelog:
            if prod == product and t <= et:
                best = price                  # changelog 已排序，后者覆盖
        return best

    def process_order(self, et, product, quantity):
        price = self.price_at(product, et)
        self.results.append((et, product, quantity,
                             price, quantity * price if price else None))


rng = random.Random(114)

print("== 场景数据：订单流 + 支付流 ==")
orders = [(1, "o1", 30), (3, "o2", 50), (8, "o3", 20),
          (22, "o4", 70), (26, "o5", 10)]
payments = [(5, "o1", 30), (9, "o2", 50), (20, "o6", 45),
            (28, "o4", 70), (35, "o3", 20), (50, "o7", 5)]
print(f"  订单流: {orders}")
print(f"  支付流: {payments}")
print("  o3 订单(8) 与其支付(35) 相差 27 —— 超过 timeout=20，应补发 NULL")
print("  o5 只有订单、o6 只有支付 —— 各自超时后补发 NULL")
print("  o7 是新支付，先缓冲等它的订单（未超时）")

print("\n== 流-流 Join 执行 ==")
join = StreamStreamJoin(timeout=20)
print(f"  {'侧':>8}{'key':>6}{'et':>4}   事件")
for side, stream in (("orders", orders), ("payments", payments)):
    for et, key, val in stream:
        join.process(side, key, et, val)
        print(f"  {side:>8}{key:>6}{et:>4}   缓冲/匹配")
print(f"\n  匹配结果:")
for key, o, p, gap in join.results:
    print(f"    {key}: 订单 {o} + 支付 {p}（时间差 {gap}）")
print(f"  超时补发（NULL Join）:")
for key, why in join.null_results:
    print(f"    {key}: {why}")
print(f"  Join 后剩余缓冲: {dict(join.buffer)}（o7 仍在等它的订单，未超时）")

print("\n== 流-表 Join：价格版本一致性 ==")
stj = StreamTableJoin()
stj.update_table(0, "苹果", 5)
stj.update_table(10, "苹果", 8)               # 事件时间 10 起涨价
stj.update_table(20, "苹果", 6)
print("  维表变更日志: [(0,苹果,5), (10,苹果,8), (20,苹果,6)]")
for et, qty in ((5, 4), (12, 2), (25, 3)):
    stj.process_order(et, "苹果", qty)
print(f"  {'下单et':>8}{'数量':>6}{'适用价格':>10}{'金额':>8}")
for et, prod, qty, price, amount in stj.results:
    print(f"  {et:>8}{qty:>6}{price!s:>10}{amount!s:>8}")
print("  订单按『下单时刻的版本』计价 —— 事件时间一致性避免跨版本污染")

print("\n== Join 状态规模的估算 ==")
print(f"  {'场景':<24}{'状态规模'}")
for row in (("1 万 QPS × 20s 缓冲", "20 万活跃 key"),
            ("10 万 QPS × 20s 缓冲", "200 万活跃 key"),
            ("skew 大（缓冲 5 分钟）", "×15 倍")):
    print(f"  {row[0]:<24}{row[1]}")
print("  状态是 Join 的核心成本：key 基数 × 缓冲时长 × 每条大小")
print("  水印清理就是状态 GC —— 没有它，内存必然泄漏")

print("\n== Join 类型补全 ==")
for line in (
    "  内 Join：双方到齐才发（本课默认）",
    "  左外：左事件超时后发 (key, NULL) —— 本课的 NULL 补发",
    "  全外：两侧都要超时补发",
    "  区间 Join：谓词不止 key 相等，还有时间距离约束",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  流-流 Join = 双边缓冲 + 水印清理 + 超时补发，三件缺一不可",
    "  流-表 Join 的关键是『事件时间一致性读取』—— 别用最新版本",
    "  Join 状态规模 = 活跃 key × 缓冲时长，是流作业最大的内存消耗点",
    "  928 课：在流上做模式识别 —— CEP",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「多事件 Join」：一个订单对应多笔支付（部分支付），聚合后再匹配。
# 2. 实现区间 Join 的自定义谓词（如订单金额 > 支付金额 视为异常）。
# 3. 给 StreamTableJoin 加维表删除（tombstone 版本），处理价格下架语义。
# 4. 思考：为什么流-流 Join 的缓冲必须按 key 分而不是全局 FIFO？
