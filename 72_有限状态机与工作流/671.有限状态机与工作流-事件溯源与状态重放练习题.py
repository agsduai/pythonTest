# ===== 第671课：有限状态机与工作流-事件溯源与状态重放 =====
# 知识点：
#   - 事件溯源：不存「当前状态」，只存不可变的事件日志；状态 = fold(events)
#   - 快照 snapshot：定期存一次聚合结果，重放时从最近快照开始，避免 O(n) 全量
#   - 事件要带 version（乐观锁）与 event_id（幂等去重，第638课）
#   - 时间旅行：重放到第 k 条事件即可查看任意历史时刻的状态
#   - 重放必须确定：apply 是纯函数，不能读当前时间/随机数/外部服务
#   - 与 CRUD 对比：天然审计、可回溯、可重建读模型，但查询需额外投影
# 依赖：无（标准库）
import json
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Event:
    event_id: str
    type: str
    payload: dict
    version: int = 0


@dataclass
class Account:
    balance: int = 0
    status: str = "正常"
    version: int = 0
    applied: list = field(default_factory=list)


def apply(state: Account, ev: Event) -> Account:
    """纯函数：给定状态与事件，返回新状态（不修改入参）。"""
    s = Account(state.balance, state.status, ev.version, state.applied + [ev.type])
    if ev.type == "开户":
        s.balance = ev.payload.get("initial", 0)
    elif ev.type == "存入":
        s.balance += ev.payload["amount"]
    elif ev.type == "取出":
        if ev.payload["amount"] > s.balance:
            raise ValueError(f"余额不足: {s.balance} < {ev.payload['amount']}")
        s.balance -= ev.payload["amount"]
    elif ev.type == "冻结":
        s.status = "冻结"
    elif ev.type == "解冻":
        s.status = "正常"
    else:
        raise ValueError(f"未知事件: {ev.type}")
    return s


def replay(events, upto=None):
    state = Account()
    seen = set()
    for i, ev in enumerate(events):
        if upto is not None and i >= upto:
            break
        if ev.event_id in seen:
            continue                       # 幂等：重复 event_id 跳过
        seen.add(ev.event_id)
        state = apply(state, ev)
    return state


EVENTS = [
    Event("e1", "开户", {"initial": 100}, 1),
    Event("e2", "存入", {"amount": 500}, 2),
    Event("e3", "取出", {"amount": 200}, 3),
    Event("e4", "冻结", {}, 4),
    Event("e5", "存入", {"amount": 50}, 5),
    Event("e6", "解冻", {}, 6),
    Event("e3", "取出", {"amount": 200}, 3),   # 重复投递，应被去重
]

print("== 事件日志 ==")
for e in EVENTS:
    print(f"  v{e.version} {e.event_id} {e.type:<4} {e.payload}")

print("\n== 全量重放 ==")
final = replay(EVENTS)
print(f"  余额={final.balance} 状态={final.status} 版本={final.version}")
print(f"  已应用事件={final.applied}")
print("  重复的 e3 被 event_id 去重，未重复扣款")

print("\n== 时间旅行（重放到第 k 条）==")
for k in range(len(EVENTS) + 1):
    s = replay(EVENTS, upto=k)
    print(f"  重放前 {k} 条: 余额={s.balance:<4} 状态={s.status:<4} 版本={s.version}")

print("\n== 快照 + 增量重放 ==")
with tempfile.TemporaryDirectory() as tmp:
    snap = Path(tmp) / "snapshot.json"
    snap_at = 3
    s = replay(EVENTS, upto=snap_at)
    seen_ids = [ev.event_id for ev in EVENTS[:snap_at]]
    snap.write_text(json.dumps({"balance": s.balance, "status": s.status,
                                "version": s.version, "offset": snap_at,
                                "seen_ids": seen_ids}, ensure_ascii=False), "utf-8")
    print(f"  快照保存于 offset={snap_at}: 余额={s.balance} 版本={s.version}")
    doc = json.loads(snap.read_text("utf-8"))
    restored = Account(doc["balance"], doc["status"], doc["version"])
    seen = set(doc["seen_ids"])
    for ev in EVENTS[doc["offset"]:]:
        if ev.event_id in seen:           # 幂等去重（含快照前事件的重复投递）
            continue
        seen.add(ev.event_id)
        restored = apply(restored, ev)
    print(f"  从快照恢复: 余额={restored.balance} 状态={restored.status} "
          f"版本={restored.version}")
    print(f"  与全量重放一致: {restored.balance == final.balance and restored.status == final.status}")

print("\n== 乐观锁（version 冲突）==")
def append(log, ev, expected_version):
    if expected_version != log[-1].version:
        raise ValueError(f"版本冲突: 期望 {expected_version}, 实际 {log[-1].version}")
    log.append(ev)

log = list(EVENTS[:3])                 # 当前版本 3
# 模拟两个并发写入方都基于版本 3 提交：第一个成功，第二个应被拒绝
append(log, Event("e7", "存入", {"amount": 10}, 4), expected_version=3)
print(f"  第一路写入成功，版本推进到 {log[-1].version}")
try:
    append(log, Event("e8", "取出", {"amount": 10}, 4), expected_version=3)
except ValueError as e:
    print("  第二路被拒绝:", e)

print("\n== 确定性要求 ==")
for line in (
    "  apply 不能调用 now() / random() / 网络，否则重放结果漂移",
    "  副作用（发邮件、扣外部款项）放在事件持久化之后，且要幂等",
    "  事件只追加不修改；修正用「补偿事件」而非改历史",
    "  读模型（报表）由投影器异步构建，可与写模型分离",
):
    print("  -", line)

print("\n== 事件溯源 vs CRUD ==")
print(f"  {'维度':<10}{'CRUD':<20}{'事件溯源'}")
for row in (("存储", "当前状态一行", "不可变事件序列"),
            ("审计", "需额外日志表", "日志本身就是事实"),
            ("回溯", "难", "重放到任意版本"),
            ("查询", "直接", "需构建读模型/投影")):
    print(f"  {row[0]:<10}{row[1]:<20}{row[2]}")

# ===== 练习题 =====
# 1. 实现「补偿事件」：撤销一笔取出，而不修改原始事件。
# 2. 写投影器 projector(events) 生成「每日余额变动」报表。
# 3. 给快照加哈希校验，检测事件日志被篡改（第601课）。
# 4. 思考：为什么事件里不能存「当前时间」，而要存「发生时间」字段？
