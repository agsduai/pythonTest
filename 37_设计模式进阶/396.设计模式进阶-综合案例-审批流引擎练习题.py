# ===== 第396课：设计模式进阶-综合案例-审批流引擎 =====
# 知识点：
#   - 综合运用：责任链（391）+ 状态机（392）+ 命令/撤销（390）
#   - 申请单：DRAFT（草稿）→ SUBMITTED（已提交）→ APPROVED/REJECTED
#   - 提交时按金额走审批链；审批链结果驱动状态迁移
#   - 每个操作记录历史，支持“撤销上一步”
#   - 实际 OA/BPM 系统的核心骨架就是这三者的组合
from dataclasses import dataclass, field
from enum import Enum


class State(Enum):
    DRAFT = "草稿"
    SUBMITTED = "已提交"
    APPROVED = "已批准"
    REJECTED = "已驳回"


# 状态机：动作 → (允许的起始状态, 目标状态)
ACTIONS = {
    "submit": (State.DRAFT, State.SUBMITTED),
    "approve": (State.SUBMITTED, State.APPROVED),
    "reject": (State.SUBMITTED, State.REJECTED),
    "withdraw": (State.SUBMITTED, State.DRAFT),
}


@dataclass
class Request:
    req_id: str
    applicant: str
    amount: float
    state: State = State.DRAFT
    history: list[str] = field(default_factory=list)

    def log(self, text: str):
        self.history.append(text)


# ---------------- 责任链：按金额决定审批人 ----------------
class Approver:

    def __init__(self, name: str, limit: float):
        self.name, self.limit = name, limit
        self.next: "Approver | None" = None

    def set_next(self, nxt: "Approver"):
        self.next = nxt
        return nxt

    def find(self, amount: float) -> "Approver | None":
        if amount <= self.limit:
            return self
        return self.next.find(amount) if self.next else None


chain = Approver("组长", 1000)
chain.set_next(Approver("经理", 10000)).set_next(Approver("总监", 100000))


# ---------------- 引擎：状态迁移 + 历史 + 撤销 ----------------
class ApprovalEngine:

    def __init__(self, chain: Approver):
        self.chain = chain
        self.undo_stack: list[tuple] = []          # (request, 快照)

    def _transition(self, req: Request, action: str, note: str = ""):
        start, target = ACTIONS[action]
        if req.state != start:
            raise RuntimeError(
                f"{req.req_id} 当前为「{req.state.value}」，不能执行「{action}」"
            )
        self.undo_stack.append((req, req.state, len(req.history)))
        req.state = target
        req.log(f"{start.value} --{action}--> {target.value} {note}".strip())
        return req.state

    # ---- 业务动作 ----
    def submit(self, req: Request):
        """提交后保持 SUBMITTED，等待审批（提交与审批分离）。"""
        self._transition(req, "submit")
        approver = self.chain.find(req.amount)
        req.log(f"待审批人：{approver.name if approver else '无（将驳回）'}")
        return req.state

    def approve(self, req: Request):
        """按金额走责任链：超权限直接驳回，否则批准。"""
        approver = self.chain.find(req.amount)
        if approver is None:
            req.log(f"金额 {req.amount:.0f} 超出全部审批权限")
            return self._transition(req, "reject", note="（超权限）")
        return self._transition(req, "approve", note=f"（{approver.name}）")

    def withdraw(self, req: Request):
        return self._transition(req, "withdraw")

    # ---- 撤销上一步 ----
    def undo(self):
        if not self.undo_stack:
            print("  没有可撤销的操作")
            return None
        req, prev_state, prev_hist_len = self.undo_stack.pop()
        req.state = prev_state
        del req.history[prev_hist_len:]           # 回滚历史记录
        print(f"  撤销完成：{req.req_id} 回到「{prev_state.value}」")
        return req


engine = ApprovalEngine(chain)

# ---- 案例 1：正常提交并通过 ----
print("== 案例 1：3000 元 ==")
r1 = Request("R001", "小明", 3000)
engine.submit(r1)
print("提交后状态：", r1.state.value)
engine.approve(r1)
print("审批后状态：", r1.state.value)
for line in r1.history:
    print("  ", line)

# ---- 案例 2：提交后撤回，再修改金额重新提交 ----
print("\n== 案例 2：撤回后重新提交 ==")
r2 = Request("R002", "小红", 80000)
engine.submit(r2)
print("首次提交状态：", r2.state.value)
engine.withdraw(r2)
print("撤回后状态：", r2.state.value)
r2.amount = 800                              # 改小金额
engine.submit(r2)
engine.approve(r2)
print("重新提交并审批后状态：", r2.state.value)

# ---- 案例 3：超权限 → 驳回 ----
print("\n== 案例 3：超权限 ==")
r3 = Request("R003", "小刚", 500000)
engine.submit(r3)
print("提交后状态：", r3.state.value)
engine.approve(r3)
print("审批后状态：", r3.state.value)
for line in r3.history:
    print("  ", line)

# ---- 撤销最后一步 ----
print("\n== 撤销 ==")
engine.undo()
print("R003 当前状态：", r3.state.value)
engine.undo()
print("再撤一步，R003 当前状态：", r3.state.value)
print("R003 历史：", r3.history)

# ---- 非法操作拦截 ----
print("\n== 非法操作 ==")
try:
    engine.withdraw(r1)          # 已批准，不能撤回
except RuntimeError as exc:
    print("  拦截：", exc)

# ===== 练习题 =====
# 1. 增加“转交”动作：SUBMITTED → SUBMITTED，但审批人换成下一级。
# 2. 让 undo 支持连续撤销（现在每次调用撤一步，验证多次调用）。
# 3. 把审批规则（金额→审批人）改成从 JSON 配置加载。
# 4. 思考：真实审批流还需要哪些能力？（并行会签、加签、超时提醒）
