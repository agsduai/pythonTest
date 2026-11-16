# ===== 第928课：流处理与事件时间-复杂事件处理（CEP）模式匹配 =====
# 知识点：
#   - CEP：在事件流上匹配「模式」—— A 之后 1 分钟内出现 B、连续 3 次失败…
#   - 本质是流上的 NFA：模式 = 状态机，事件驱动状态转移（87 章 NFA 的流式版）
#   - 部分匹配（pending）要有超时回收 —— 依然是水印/时间驱动
#   - 连续性语义：STRICT（紧邻）/ SKIP_TILL_NEXT（跳过无关事件）
#   - 应用：风控（连续失败登录）、IoT（温度骤升）、运维（告警升级链）
# 依赖：无（标准库）
from collections import defaultdict


class PatternMatcher:
    """模式：事件序列 [A, B, C]，每个阶段带时限（时间单位）。
    语义：SKIP_TILL_NEXT —— 跳过不相关事件，直到出现下一阶段所需事件。"""

    def __init__(self, stages, timeout_per_stage=10):
        self.stages = stages                   # [(谓词名, 事件类型)]
        self.timeout = timeout_per_stage
        self.pending = []                      # 每项 = {"step": 已匹配阶段数, "start": 起始事件时间, "events": [...]}
        self.matches = []
        self.expired = 0

    def process(self, et, event):
        out = []
        alive = []
        for pm in self.pending:
            if et - pm["start"] > self.timeout * len(self.stages):
                self.expired += 1                 # 整体超时回收
                continue
            need = self.stages[pm["step"]]
            if event["type"] == need:
                pm["step"] += 1
                pm["events"].append((et, event))
                if pm["step"] == len(self.stages):
                    self.matches.append(pm)
                    out.append(("match", list(pm["events"])))
                    continue                      # 匹配完成 -> 移出 pending
            alive.append(pm)
        if event["type"] == self.stages[0]:
            alive.append({"step": 1, "start": et, "events": [(et, event)]})
        self.pending = alive
        return out


def run_stream(matcher, events):
    out_all = []
    for et, event in events:
        for kind, matched in matcher.process(et, event):
            out_all.append((et, matched))
    return out_all


print("== 模式：连续 3 次登录失败（1 分钟窗口）==")
login_events = []
for base, fails in ((10, 1), (20, 3), (45, 1), (60, 3), (100, 1)):
    for i in range(fails):
        login_events.append((base + i, {"type": "fail", "user": "bob"}))
    login_events.append((base + fails, {"type": "success", "user": "bob"}))
login_events.sort()
print(f"  事件流（fail/success 交错）:")
for et, e in login_events:
    print(f"    t={et:>3}: {e['type']}")

m = PatternMatcher(["fail", "fail", "fail"], timeout_per_stage=10)
matches = run_stream(m, login_events)
print(f"\n  命中的模式实例 = {len(matches)}")
for et, matched in matches:
    seq = " -> ".join(f"{e['type']}@{t}" for t, e in matched)
    print(f"    起点 t={matched[0][0]}: {seq}")
print(f"  未完成即超时的部分匹配 = {m.expired}")
print("  SKIP_TILL_NEXT 会跳过 success 继续找 fail —— 跨 success 的组合也算命中")
print("  若业务要求『中间无成功登录』，需加否定条件（见练习 2）")

print("\n== 模式 2：支付失败 -> 立即重试 -> 成功（6 秒内）==")


class StrictPatternMatcher(PatternMatcher):
    """STRICT 语义：下一阶段事件必须在 timeout 内紧随出现。"""

    def process(self, et, event):
        out = []
        alive = []
        for pm in self.pending:
            if et - pm["last_et"] > self.timeout:
                self.expired += 1
                continue
            need = self.stages[pm["step"]]
            if event["type"] == need:
                pm["step"] += 1
                pm["events"].append((et, event))
                pm["last_et"] = et
                if pm["step"] == len(self.stages):
                    self.matches.append(pm)
                    out.append(("match", list(pm["events"])))
                    continue
            alive.append(pm)
        if event["type"] == self.stages[0]:
            alive.append({"step": 1, "start": et, "last_et": et,
                          "events": [(et, event)]})
        self.pending = alive
        return out


pay_events = [
    (1, {"type": "pay_fail"}),
    (2, {"type": "heartbeat"}),          # 干扰事件（STRICT 下会打断）
    (3, {"type": "pay_retry"}),
    (4, {"type": "pay_success"}),
    (10, {"type": "pay_fail"}),
    (12, {"type": "pay_retry"}),
    (13, {"type": "pay_success"}),
]
print("  事件流: fail@1, heartbeat@2, retry@3, success@4 | fail@10, retry@12, success@13")
strict = StrictPatternMatcher(["pay_fail", "pay_retry", "pay_success"], 6)
loose = PatternMatcher(["pay_fail", "pay_retry", "pay_success"], 6)
m_strict = run_stream(strict, pay_events)
m_loose = run_stream(loose, pay_events)
print(f"  STRICT（紧邻）命中: {len(m_strict)} 次"
      f"  -> {[t for t, _ in m_strict]}")
print(f"  SKIP_TILL_NEXT 命中: {len(m_loose)} 次"
      f"  -> {[t for t, _ in m_loose]}")
print("  heartbeat 挡住了 STRICT 的第一次匹配，但挡不住 SKIP 语义 —— 语义即产品决策")

print("\n== 部分匹配的状态成本 ==")
print(f"  当前未完成的部分匹配 = {len(strict.pending)}")
print("  状态规模 ≈ 并发进行中的模式实例数 × 模式长度")
print("  风控场景（每天百万用户 × 多种模式）→ 状态管理是 CEP 引擎的核心")
print("  超时回收（本课简化）在工程上由 watermark/定时器驱动（925 课）")

print("\n== CEP 与 NFA/模型检测的关系 ==")
for line in (
    "  87 章 NFA：静态文本上的状态机；本章：事件流上的状态机 + 时间约束",
    "  100 章模型检测：验证『所有行为』；CEP：在线发现『正在发生的行为』",
    "  三者共享同一抽象：状态 + 转移 + 接受条件，只是输入源不同",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  CEP 模式 = 流上的带时限 NFA；部分匹配是主要状态成本",
    "  STRICT/SKIP 语义是产品决策：紧邻告警 vs 宽松告警",
    "  超时回收让模式状态不会无限累积（又是 watermark 的功劳）",
    "  929 课：流处理的『最后一公里』—— 恰一次语义",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Kleene-plus 阶段（A 后跟 1 个或多个 B），统计每次匹配捕获的 B 数量。
# 2. 实现「否定阶段」：A 与 B 之间不得出现 C（出现即作废该部分匹配）。
# 3. 把超时回收改为 watermark 驱动（925 课），验证与逐事件回收结果一致。
# 4. 思考：为什么 CEP 引擎不直接用正则表达式？时间约束与乱序带来了哪些
#    正则没有的复杂度？
