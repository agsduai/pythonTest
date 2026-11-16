# ===== 第926课：流处理与事件时间-撤回与增量修正 =====
# 知识点：
#   - 撤回（retraction）：已发布的结果允许被修正 —— 下游收到 (撤回, 新值) 对
#   - 两种流形态：upsert 流（key+值，覆盖语义）与 retract 流（−旧 +新 明细对）
#   - 窗口生命周期扩展：首次发布（触发）→ 迟到修正（re-触发）→ 最终封板
#   - 允许迟到（allowed lateness）= 窗口状态保留时长，用完才真正销毁
#   - 撤回让下游 SQL/BI 可维护正确视图 —— 但下游必须支持更新语义
# 依赖：无（标准库）
import random
from collections import defaultdict


class RetractableWindow:
    """带撤回能力的 5 秒计数窗口。窗口状态：pending → published → sealed。"""

    def __init__(self, width=5, allowed_lateness=8):
        self.width = width
        self.lateness = allowed_lateness
        self.tracker_max_et = None
        self.windows = defaultdict(lambda: {"values": [], "state": "pending",
                                            "published": None, "revisions": 0})

    def watermark(self):
        if self.tracker_max_et is None:
            return None
        return self.tracker_max_et - 2           # 固定 2 秒乱序容忍

    def process(self, et, uid):
        self.tracker_max_et = et if self.tracker_max_et is None \
            else max(self.tracker_max_et, et)
        start = et // self.width * self.width
        self.windows[start]["values"].append(uid)
        out = []
        wm = self.watermark()
        for start, win in list(self.windows.items()):
            end = start + self.width
            if win["state"] == "pending" and wm is not None and end <= wm:
                win["published"] = len(win["values"])
                win["state"] = "published"
                out.append(("publish", start, win["published"]))
            elif (win["state"] == "published" and et <= start + self.lateness
                  and len(win["values"]) != win["published"]):
                # 迟到数据到达已发布窗口 → 发出撤回对
                old = win["published"]
                new = len(win["values"])
                win["published"] = new
                win["revisions"] += 1
                out.append(("retract", start, -old))   # 撤回旧值
                out.append(("update", start, +new))    # 补上新值
            elif win["state"] == "published" and wm > end + self.lateness:
                win["state"] = "sealed"               # 最终封板
                out.append(("seal", start, win["published"]))
        return out, wm


rng = random.Random(113)

print("== 构造带迟到的流 ==")
base = [(t, t % 5 + 1) for t in range(25)]
arrived = []
for et, uid in base:
    arrived.append((et + rng.randint(0, 4), et, uid))
# 手工注入两个明显迟到的事件（属于已发布窗口）
arrived.append((30, 3, 9))        # et=3 的窗口 [0,5) 在处理时间 30 才补到
arrived.append((32, 7, 4))        # et=7 的窗口 [5,10) 同样
arrived.sort()
print(f"  27 个事件，其中 2 个严重迟到（处理时间 30/32 才到）")

print("\n== 逐事件处理：观察发布/撤回/封板 ==")
rw = RetractableWindow(width=5, allowed_lateness=8)
downstream = defaultdict(int)                 # 下游维护的（可更新）视图
events_out = []
for pt, et, uid in arrived:
    outputs, wm = rw.process(et, uid)
    for kind, start, delta in outputs:
        events_out.append((pt, kind, start, delta))
        if kind in ("publish", "update"):
            downstream[start] += delta
        elif kind == "retract":
            downstream[start] += delta        # delta 为负
print(f"  {'处理时':>6}{'动作':>10}{'窗口':>6}{'载荷':>8}")
for pt, kind, start, delta in events_out:
    print(f"  {pt:>6}{kind:>10}{start:>6}{delta:>+8}")

print("\n== 下游视图的演化（部分展示）==")
print(f"  最终下游视图: {dict(sorted(downstream.items()))}")

print("\n== 真值对照 ==")
truth = defaultdict(int)
for _, et, uid in arrived:
    truth[et // 5 * 5] += 1
truth = dict(sorted(truth.items()))
print(f"  真值（含迟到全部计入）: {truth}")
mismatches = [k for k in truth if downstream[k] != truth[k]]
print(f"  下游视图与真值一致的窗口: {len(truth) - len(mismatches)}/{len(truth)}")
if mismatches:
    print(f"  不一致窗口 {mismatches}: 封板后迟到 → 侧输出处理（本章简化为忽略）")
print("  允许迟到内到达的修正都已通过撤回对送达下游")

print("\n== 撤回流的形态 ==")
print(f"  {'形态':<12}{'样例'}")
print(f"  {'upsert 流':<12}{'+(窗口[0,5), 6) 覆盖语义'}")
print(f"  {'retract 流':<12}{'-([0,5), 5) 然后 +([0,5), 6) 明细对'}")
print("  upsert 需要下游按主键覆盖；retract 更通用（Flink 的 changelog 模式）")

print("\n== 窗口状态机 ==")
for line in (
    "  pending：还在收数，不出结果",
    "  published：水印触发，发出首版结果（可被撤回修正）",
    "  sealed：超过 allowed_lateness，状态可销毁（内存回收点）",
    "  状态保留时长 = allowed_lateness —— 与 925 课的丢弃策略互为两极",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  撤回把『结果错了怎么办』纳入流处理的正常语义",
    "  发布/撤回/封板三阶段让窗口状态有明确的回收时机",
    "  下游必须支持更新语义（upsert 或 changelog）—— 生态配套",
    "  927 课：窗口之外的另一个难点 —— 流与流的 Join",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现聚合版撤回：只发 (窗口, 增量) 而非全量重算，减少下游压力。
# 2. 实现「两级撤回」：撤回对又被修正时的链式处理（retract-of-retract）。
# 3. 把 allowed_lateness 扫描 0~10，绘制「修正次数 vs 结果延迟」曲线。
# 4. 思考：为什么数据库 UPDATE 可以直接覆盖，而流系统需要显式撤回对？
