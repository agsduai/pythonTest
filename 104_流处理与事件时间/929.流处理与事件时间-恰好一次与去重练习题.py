# ===== 第929课：流处理与事件时间-恰好一次与去重 =====
# 知识点：
#   - 交付语义：至多一次（丢数据）/ 至少一次（重复）/ 恰一次（昂贵但干净）
#   - 恰一次 ≈ 至少一次 + 幂等/去重：端到端要「可判定地消除重复」
#   - 去重：按事件唯一 id 维护已见集合（TTL 控制状态规模）
#   - 幂等 sink：按 (key, window) 主键覆盖写 —— 重复投递无害
#   - 两阶段提交思想：预写 → 提交 → 确认，崩溃后按日志恢复
# 依赖：无（标准库）
import random
from collections import defaultdict


class SourceWithDuplicates:
    """模拟网络重传的源：部分事件会重复投递。"""

    def __init__(self, events, rng, duplicate_rate=0.3):
        self.events = []
        for et, uid, amount in events:
            self.events.append((et, uid, amount))
            if rng.random() < duplicate_rate:
                self.events.append((et, uid, amount))   # 重发同一事件
        rng.shuffle(self.events)

    def read(self):
        return list(self.events)


class Deduplicator:
    """按事件 id 去重：TTL 控制已见集合的状态规模。"""

    def __init__(self, ttl=10):
        self.ttl = ttl
        self.seen = {}                       # id -> 最后见到的事件时间
        self.duplicates = 0
        self.now = 0

    def process(self, et, uid, amount):
        self.now = max(self.now, et)
        # GC：TTL 过期的 id 移除
        for k in [k for k, t in self.seen.items() if self.now - t > self.ttl]:
            del self.seen[k]
        eid = (uid, et)                      # 事件唯一 id = (用户, 事件时间)
        if eid in self.seen:
            self.duplicates += 1
            return False                     # 重复：丢弃
        self.seen[eid] = et
        return True                          # 首次：通过


class IdempotentSink:
    """幂等 sink：按 (uid, 窗口) 主键覆盖写 —— 重复写入结果一致。"""

    def __init__(self, width=5):
        self.width = width
        self.store = {}                      # (uid, window) -> amount

    def write(self, et, uid, amount):
        key = (uid, et // self.width * self.width)
        self.store[key] = amount             # 覆盖语义：天然幂等
        return key

    def snapshot(self):
        return dict(sorted(self.store.items()))


rng = random.Random(115)
raw_events = [(t, t % 5 + 1, (t + 1) * 10) for t in range(20)]
source = SourceWithDuplicates(raw_events, rng, duplicate_rate=0.35)

print("== 源（带重复投递）==")
print(f"  真实事件 {len(raw_events)} 个，投递总数 {len(source.events)} 个"
      f"（重复 {len(source.events) - len(raw_events)} 次）")
counts = {}
for et, uid, amount in source.events:
    counts[(uid, et)] = counts.get((uid, et), 0) + 1
dups = {k: v for k, v in counts.items() if v > 1}
print(f"  重复的 (uid, et) 样例: {dict(list(dups.items())[:5])}")

print("\n== 不去重的后果（至少一次语义）==")
naive_sum = defaultdict(int)
for et, uid, amount in source.events:
    naive_sum[uid] += amount
truth = defaultdict(int)
for et, uid, amount in raw_events:
    truth[uid] += amount
print(f"  {'uid':>4}{'正确值':>10}{'不去重值':>10}{'虚增':>8}")
for uid in sorted(truth):
    print(f"  {uid:>4}{truth[uid]:>10}{naive_sum[uid]:>10}"
          f"{naive_sum[uid] - truth[uid]:>+8}")
print("  重复投递让汇总虚增 —— 至少一次语义必须配合去重/幂等")

print("\n== 去重器 + 幂等 sink ==")
dedup = Deduplicator(ttl=10)
sink = IdempotentSink()
passed = 0
for et, uid, amount in source.events:
    if dedup.process(et, uid, amount):
        passed += 1
        sink.write(et, uid, amount)
print(f"  通过去重的事件 = {passed}（应等于真实事件数 {len(raw_events)}）")
print(f"  去重器识别的重复 = {dedup.duplicates}")
snapshot = sink.snapshot()
print(f"  幂等 sink 最终状态（每 (uid, 窗口) 最新值，共 {len(snapshot)} 个主键）:")
for (uid, win), amount in list(snapshot.items())[:8]:
    print(f"    uid={uid} 窗口[{win},{win + sink.width}): {amount}")
print(f"    ... 共 {len(snapshot)} 个主键")

print("\n== 端到端校验 ==")
final_counts = {}
d2 = Deduplicator(10)
for et, uid, amount in source.events:
    if d2.process(et, uid, amount):
        final_counts[uid] = final_counts.get(uid, 0) + 1
all_ok = True
for uid in sorted(final_counts):
    truth_n = sum(1 for et, u, _ in raw_events if u == uid)
    ok = final_counts[uid] == truth_n
    all_ok = all_ok and ok
    print(f"    uid={uid}: 去重后 {final_counts[uid]} vs 真实 {truth_n}"
          f" {'✓' if ok else '✗'}")
print(f"  全部一致: {all_ok}")
print("  注意：幂等 sink 是『按主键覆盖最新值』—— 聚合语义由下游决定")

print("\n== 两阶段提交思想 ==")
for line in (
    "  阶段 1（预提交）：把结果写到带版本号的暂存区",
    "  阶段 2（提交）：checkpoint 成功 → 暂存区数据对外可见",
    "  崩溃恢复：未提交的暂存数据回滚，已提交的天然幂等",
    "  Flink 的两阶段提交 sink / Kafka 事务：把这套思想产品化",
    "  成本：延迟（等 checkpoint）与复杂度 —— 幂等设计常是更便宜的替代",
):
    print("  -", line)

print("\n== 去重状态规模 ==")
print(f"  TTL=10 时已见集合大小 = {len(dedup.seen)}（真实事件 20 个 + 迟期未过期）")
print("  TTL 越长越可靠，状态越大 —— 又是那个熟悉的权衡")
print("  高基数场景：布隆过滤器预筛（426 课）+ 精确集合确认，两级结构")

print("\n== 小结 ==")
for line in (
    "  恰一次不是『魔法交付』，而是 至少一次 + 可判定的去重/幂等",
    "  去重靠事件唯一 id；幂等靠主键覆盖；二者常组合使用",
    "  TTL 与状态规模、交付可靠性的权衡贯穿始终",
    "  930 课：综合案例 —— 订单风控流水线",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「布隆过滤器两级去重」：布隆可能误判已见 → 再查精确集合。
# 2. 实现「事务性 sink」：写暂存表 + commit 标记，模拟崩溃恢复。
# 3. 统计去重器在不同 duplicate_rate 下的状态规模曲线。
# 4. 思考：什么业务能用『至多一次』？丢数据 vs 重复数据，你的业务选哪个？
