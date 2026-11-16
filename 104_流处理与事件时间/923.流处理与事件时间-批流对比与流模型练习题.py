# ===== 第923课：流处理与事件时间-批流对比与流模型 =====
# 知识点：
#   - 有界数据（批）vs 无界数据（流）：本质区别是「数据会不会完」
#   - 批思维：数据到齐再算，结果一次成型；流思维：边到边算，结果持续更新
#   - Lambda 架构：批层（准确）+ 速度层（快速）双写 —— 双代码的维护之痛
#   - Kappa 架构：一切皆流，批只是流的极限形式 —— 用一套代码
#   - 本章的目标：掌握流语义的核心原语，它们在批引擎里同样适用
# 依赖：无（标准库）
import random
from collections import defaultdict


def make_clicks(rng, n=2000):
    """点击流：(事件时间, 用户, 页面)。"""
    return [(rng.randint(0, 3600), f"u{rng.randint(1, 50)}",
             rng.choice(["首页", "详情", "购物车", "支付"]))
            for _ in range(n)]


def batch_aggregate(all_events, width=600):
    """批处理：数据到齐后一次性聚合。"""
    buckets = defaultdict(int)
    for et, _user, page in all_events:
        buckets[et // width * width] += 1
    return dict(sorted(buckets.items()))


class StreamingAggregator:
    """流式聚合：每个事件到达即更新增量状态；可随时「读当前结果」。"""

    def __init__(self, width=600):
        self.width = width
        self.buckets = defaultdict(int)

    def process(self, et, user, page):
        self.buckets[et // self.width * self.width] += 1

    def snapshot(self):
        return dict(sorted(self.buckets.items()))


def split_stream(all_events, rng, offline_delay=0.35):
    """模拟在线/离线：35% 的事件延迟很久才到（离线补传）。"""
    online, offline = [], []
    for e in all_events:
        (offline if rng.random() < offline_delay else online).append(e)
    return online, offline


rng = random.Random(121)
clicks = make_clicks(rng)

print("== 同一聚合的两种计算方式 ==")
batch_result = batch_aggregate(clicks)
sa = StreamingAggregator()
for et, user, page in clicks:
    sa.process(et, user, page)
stream_result = sa.snapshot()
print(f"  批式结果 = 流式结果: {batch_result == stream_result}")
print(f"  {'窗口起点':>10}{'PV':>8}")
for k in sorted(batch_result)[:6]:
    print(f"  {k:>10}{batch_result[k]:>8}")
print("  无乱序、无迟到时，批与流给出完全相同的结果 —— 语义一致性的底线")

print("\n== 迟到数据：批与流的分野 ==")
online, offline = split_stream(clicks, rng)
# 流式：只基于在线部分即时出结果
sa2 = StreamingAggregator()
for et, user, page in online:
    sa2.process(et, user, page)
online_only = sa2.snapshot()
# 批式：等 offline 到齐后全量重算
batch_with_offline = batch_aggregate(online + offline)
print(f"  在线事件 {len(online)}，离线补传 {len(offline)}")
drift = [k for k in batch_with_offline
         if online_only.get(k, 0) != batch_with_offline[k]]
print(f"  结果发生变化的窗口 = {len(drift)} / {len(batch_with_offline)}")
print("  流式的选择：a) 接受不完整  b) 撤回修正(926课)  c) 等水印(925课)")
print("  批式的选择：全量重算 —— 简单但延迟以小时计")

print("\n== Lambda 架构的痛 ==")
print("""
  ┌────────┐    ┌──────────┐
  │ 事件流  │───→│ 速度层    │───→ 实时视图（近似）
  └────┬───┘    └──────────┘
       │（落盘）  ┌──────────┐
       └───────→│ 批层      │───→ 批视图（准确）  → 定期合并视图
                └──────────┘
""")
print("  同一个聚合逻辑要写两遍（批 + 流），结果还要能对账")
print("  对不上账是最常见的运维事故：口径漂移、时区漂移、重放不一致")

print("\n== Kappa 架构：一套代码 ==")
for line in (
    "  一切皆流：批 = 「有界流」，重放历史日志即可重算",
    "  需要修正口径时：换版本重放日志（不是改两份代码）",
    "  前提：日志可持久化、可重放、顺序可保证（Kafka 类系统）",
    "  本章所有原语（水印/窗口/撤回）就是 Kappa 架构的零件",
):
    print("  -", line)

print("\n== 增量聚合的正确姿势 ==")
print(f"  {'聚合类型':<12}{'增量维护':<24}{'撤回难度'}")
for row in (("COUNT/SUM", "加减一个数", "容易"),
            ("MIN/MAX", "需要保留全部值或堆", "难（次大值顶上）"),
            ("AVG", "sum/count 双状态", "容易"),
            ("分位数", " sketch 结构（88 章）", "中")):
    print(f"  {row[0]:<12}{row[1]:<24}{row[2]}")
print("  设计算法时优先选择『可增量 + 可撤回』的聚合语义")

print("\n== 小结 ==")
for line in (
    "  批与流是同一计算的两种调度方式，语义应当一致",
    "  乱序/迟到让流式的『当下结果』不完整 —— 这是本章所有机制要解的题",
    "  Lambda 双代码之痛催生 Kappa：一切皆流",
    "  下一课：事件时间与处理时间的偏差 —— 流语义的起点",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「批流对账」：定期比较流式视图与批式视图，输出差异窗口清单。
# 2. 把 88 章的 Count-Min Sketch 接到 StreamingAggregator 上，对比精确计数
#    与 sketch 估计的误差。
# 3. 模拟「口径变更重放」：过滤条件改变后，从动作日志重算全部窗口。
# 4. 思考：什么业务适合 Lambda（批层兜底），什么业务可以纯 Kappa？
