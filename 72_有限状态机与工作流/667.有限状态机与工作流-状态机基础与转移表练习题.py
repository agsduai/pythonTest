# ===== 第667课：有限状态机与工作流-状态机基础与转移表 =====
# 知识点：
#   - FSM = 有限状态集合 + 事件集合 + 转移函数 δ(state, event) -> state
#   - 转移表用 dict[(state, event)] = (next_state, action)，比一堆 if/else 清晰
#   - 非法转移要显式拒绝（抛错或忽略），不要让状态机进入未定义态
#   - 进入/退出动作（on_enter/on_exit）与守卫条件（guard）让 FSM 可表达业务规则
#   - 终态（accepting）用于判定「流程是否走完」
#   - 用 dataclass + 纯转移表实现，状态可枚举、可测试、可可视化
# 依赖：无（标准库）
from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    IDLE = "空闲"
    RUNNING = "运行中"
    PAUSED = "已暂停"
    DONE = "已完成"


class Event(Enum):
    START = "启动"
    PAUSE = "暂停"
    RESUME = "恢复"
    FINISH = "完成"
    RESET = "重置"


TRANSITIONS = {
    (State.IDLE, Event.START): State.RUNNING,
    (State.RUNNING, Event.PAUSE): State.PAUSED,
    (State.RUNNING, Event.FINISH): State.DONE,
    (State.PAUSED, Event.RESUME): State.RUNNING,
    (State.PAUSED, Event.RESET): State.IDLE,
    (State.DONE, Event.RESET): State.IDLE,
}
TERMINAL = {State.DONE}


@dataclass
class FSM:
    state: State = State.IDLE
    history: list = field(default_factory=list)

    def allowed(self, event):
        return (self.state, event) in TRANSITIONS

    def send(self, event, strict=True):
        key = (self.state, event)
        if key not in TRANSITIONS:
            if strict:
                raise ValueError(f"非法转移: {self.state.value} --{event.value}--> ?")
            self.history.append((self.state, event, self.state, "拒绝"))
            return self.state
        nxt = TRANSITIONS[key]
        self.history.append((self.state, event, nxt, "OK"))
        self.state = nxt
        return nxt

    def available_events(self):
        return [e for (s, e) in TRANSITIONS if s == self.state]

    @property
    def is_terminal(self):
        return self.state in TERMINAL


print("== 转移表 ==")
for (s, e), nxt in TRANSITIONS.items():
    print(f"  {s.value:<6} --{e.value:<4}--> {nxt.value}")

print("\n== 正常运行轨迹 ==")
fsm = FSM()
for ev in (Event.START, Event.PAUSE, Event.RESUME, Event.FINISH):
    old = fsm.state
    new = fsm.send(ev)
    print(f"  {old.value:<6} --{ev.value:<4}--> {new.value}")
print("  是否终态:", fsm.is_terminal)

print("\n== 非法转移 ==")
f2 = FSM()
for ev in (Event.PAUSE, Event.FINISH):
    try:
        f2.send(ev)
    except ValueError as e:
        print("  ", e)
print("  宽松模式（忽略非法事件）:", end=" ")
f3 = FSM()
print(f3.send(Event.PAUSE, strict=False).value, "状态不变")

print("\n== 当前可用事件 ==")
for s in State:
    probe = FSM(s)
    print(f"  {s.value:<6}: {[e.value for e in probe.available_events()]}")

print("\n== 历史轨迹（可审计）==")
f4 = FSM()
for ev in (Event.START, Event.PAUSE, Event.RESUME, Event.FINISH, Event.RESET, Event.START):
    f4.send(ev)
print(f"  {'从':<8}{'事件':<8}{'到':<8}{'结果'}")
for a, e, b, r in f4.history:
    print(f"  {a.value:<8}{e.value:<8}{b.value:<8}{r}")

print("\n== 可达性分析（BFS）==")
from collections import deque
reachable, q = {State.IDLE}, deque([State.IDLE])
while q:
    s = q.popleft()
    for (src, _), dst in TRANSITIONS.items():
        if src == s and dst not in reachable:
            reachable.add(dst); q.append(dst)
print("  从 IDLE 可达:", [s.value for s in reachable])
unreachable = set(State) - reachable
print("  不可达状态:", [s.value for s in unreachable] or "无")

print("\n== 死端检测（无出边的非终态）==")
for s in State:
    if s not in TERMINAL and not any(src == s for src, _ in TRANSITIONS):
        print("  死端:", s.value)
print("  以上若有输出说明设计有漏洞；本例应为空")

print("\n== 转移表 vs if/else ==")
for line in (
    "  表驱动: 状态/事件组合一目了然，可自动生成图、可做完备性检查",
    "  if/else: 分支散落，加状态时容易漏改、难审计",
    "  表还能序列化成配置，交给非程序员维护流程",
    "  复杂动作/守卫可挂回调函数，表只管结构",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 给转移表增加 guard（条件）与 action（副作用），实现带副作用的 send。
# 2. 用 BFS 求从 IDLE 到 DONE 的最短事件序列。
# 3. 检测转移表的「不确定性」：同一 (state,event) 是否出现多个目标。
# 4. 思考：为什么终态也要显式定义 RESET 转移，而不是让它永远停住？
