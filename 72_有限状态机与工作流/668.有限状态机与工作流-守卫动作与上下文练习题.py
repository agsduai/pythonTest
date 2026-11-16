# ===== 第668课：有限状态机与工作流-守卫、动作与上下文 =====
# 知识点：
#   - 转移三要素：guard（能否转）、action（转时做什么）、target（转到哪）
#   - 上下文 ctx 携带业务数据（余额、次数、审批人），守卫读它、动作改它
#   - 同一事件在不同状态下可绑定不同转移，避免调用方写 if 判断
#   - action 应尽量幂等/可重放；失败时不改变状态（先校验再提交）
#   - 内部转移（internal transition）：执行动作但状态不变
#   - entry/exit 动作：进入与离开状态时各触发一次，用于日志/资源申请
# 依赖：无（标准库）
from dataclasses import dataclass, field


@dataclass
class Ctx:
    balance: int = 0
    attempts: int = 0
    log: list = field(default_factory=list)


@dataclass
class Transition:
    target: str
    guard: object = None   # (ctx, payload) -> bool
    action: object = None  # (ctx, payload) -> None
    desc: str = ""


def T(target, desc="", guard=None, action=None):
    return Transition(target, guard, action, desc)


class Machine:
    def __init__(self, table, initial, ctx=None, entry=None, exit_=None):
        self.table, self.state, self.ctx = table, initial, ctx or Ctx()
        self.entry, self.exit = entry or {}, exit_ or {}
        self.trace = []
        self._on_enter(initial)

    def _on_enter(self, s):
        if s in self.entry:
            self.entry[s](self.ctx)

    def _on_exit(self, s):
        if s in self.exit:
            self.exit[s](self.ctx)

    def send(self, event, **payload):
        tr = self.table.get((self.state, event))
        if tr is None:
            self.trace.append((self.state, event, self.state, "无转移"))
            return False
        if tr.guard and not tr.guard(self.ctx, payload):
            self.trace.append((self.state, event, self.state, "守卫拒绝"))
            return False
        old = self.state
        if tr.action:
            tr.action(self.ctx, payload)
        if tr.target != old:
            self._on_exit(old)
            self.state = tr.target
            self._on_enter(self.state)
        self.trace.append((old, event, self.state, tr.desc or "OK"))
        return True

    def allowed(self, event, **payload):
        tr = self.table.get((self.state, event))
        return tr is not None and (tr.guard is None or tr.guard(self.ctx, payload))


# ---- 一个「账户充值 + 提现」流程 ----
def enough(ctx, p):
    return p.get("amount", 0) <= ctx.balance

def positive(ctx, p):
    return p.get("amount", 0) > 0

def deposit(ctx, p):
    ctx.balance += p["amount"]
    ctx.log.append(f"充值 +{p['amount']}")

def withdraw(ctx, p):
    ctx.balance -= p["amount"]
    ctx.log.append(f"提现 -{p['amount']}")

def fail_count(ctx, p):
    ctx.attempts += 1
    ctx.log.append("密码错误")

def on_lock(ctx):
    ctx.log.append("账户已锁定")

TABLE = {
    ("正常", "充值"): T("正常", "充值成功", guard=positive, action=deposit),
    ("正常", "提现"): T("正常", "提现成功", guard=enough, action=withdraw),
    ("正常", "提现失败"): T("正常", "余额不足", action=lambda c, p: c.log.append("余额不足")),
    ("正常", "密码错误"): T("正常", "记一次错误", action=fail_count),
    ("正常", "锁定"): T("锁定", "人工锁定"),
    ("正常", "错误过多"): T("锁定", "3 次错误自动锁定",
                       guard=lambda c, p: c.attempts >= 3),
    ("锁定", "解锁"): T("正常", "客服解锁",
                     action=lambda c, p: c.log.append("已解锁")),
    ("锁定", "查询"): T("锁定", "锁定态仅可查询（内部转移）"),
}

m = Machine(TABLE, "正常", Ctx(balance=100),
            entry={"锁定": on_lock},
            exit_={"正常": lambda c: c.log.append("离开正常态")})

print("== 事件序列与状态变化 ==")
seq = [
    ("充值", {"amount": 50}),
    ("提现", {"amount": 30}),
    ("提现", {"amount": 999}),     # 余额不足，被 enough 守卫拒绝
    ("密码错误", {}), ("密码错误", {}), ("密码错误", {}),
    ("错误过多", {}),
    ("提现", {"amount": 10}),      # 锁定态无此转移
    ("查询", {}),
    ("解锁", {}),
    ("提现", {"amount": 20}),
]
for ev, payload in seq:
    ok = m.send(ev, **payload)
    print(f"  {ev:<8} {str(payload):<20} -> state={m.state:<5} 接受={ok} "
          f"余额={m.ctx.balance}")

print("\n== 完整轨迹 ==")
for a, e, b, note in m.trace:
    print(f"  {a:<5} --{e:<10}--> {b:<5}  {note}")

print("\n== 上下文日志 ==")
for line in m.ctx.log:
    print("  -", line)
print(f"  最终余额={m.ctx.balance}  错误次数={m.ctx.attempts}")

print("\n== 守卫与动作分离 ==")
print("  守卫只读 ctx，返回 bool；动作可写 ctx。先守卫后动作 -> 失败不改状态")
m2 = Machine(TABLE, "正常", Ctx(balance=10))
print("  余额 10 提现 999:", m2.send("提现", amount=999), "余额=", m2.ctx.balance)
print("  守卫拒绝时 action 未执行，余额保持不变")

print("\n== entry / exit 触发次数 ==")
print("  进入锁定触发 on_lock:", sum("账户已锁定" == x for x in m.ctx.log), "次")
print("  exit 仅在真正离开状态时触发，内部转移不触发")

print("\n== 内部转移 ==")
m3 = Machine(TABLE, "锁定", Ctx())
print("  锁定态查询:", m3.send("查询"), "状态仍为", m3.state)
print("  状态未变，故不触发 entry/exit")

print("\n== 工程要点 ==")
for line in [
    "  动作要幂等：事件可能重放（第638课），重复扣款是灾难",
    "  守卫失败要有可观测原因，别静默吞掉",
    "  状态与 ctx 一起持久化，重启后才能恢复到一致位置",
    "  生产用 transitions / XState 等库；本课手写便于理解语义",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给「提现」增加「单笔上限」与「日累计上限」两个守卫。
# 2. 实现 action 失败回滚：动作抛异常时状态与 ctx 都保持不变。
# 3. 把 TABLE 序列化成 JSON 配置，并写个加载器还原转移表。
# 4. 思考：为什么「先守卫、后动作、最后改状态」的顺序不能颠倒？
