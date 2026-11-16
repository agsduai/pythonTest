# ===== 第672课：有限状态机与工作流-超时、补偿与Saga =====
# 知识点：
#   - 长事务不能靠数据库锁跨服务持有，改用 Saga：一串本地事务 + 补偿事务
#   - 每步 T_i 配一个 C_i（逆操作）；失败时按反向顺序执行已成功的补偿
#   - 补偿必须幂等（可能重放）、可重试、且允许「补偿失败」进入人工介入
#   - 超时：给每步设 deadline，用可注入时钟判断，不真实 sleep
#   - 向前恢复 vs 向后恢复：重试继续往前 / 补偿回滚已完成的步骤
#   - 与第639课重试、第44章可靠性、第53章 Outbox 串联
# 依赖：无（标准库）
from dataclasses import dataclass, field


@dataclass
class Clock:
    now: float = 0.0
    def advance(self, dt): self.now += dt


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str = ""


class Saga:
    def __init__(self, clock=None):
        self.clock = clock or Clock()
        self.completed = []          # 已成功、需要补偿的步骤
        self.log = []

    def execute(self, steps, fail_at=None, timeout_at=None, deadline=10.0):
        """steps: [(name, forward_fn, compensate_fn, duration)]。"""
        for i, (name, forward, compensate, duration) in enumerate(steps):
            if timeout_at == i:
                self.clock.advance(deadline + 1)
            self.clock.advance(duration)
            if self.clock.now > deadline and timeout_at == i:
                self.log.append(f"TIMEOUT 步骤 {name} 超时（t={self.clock.now}）")
                return self.compensate(compensate, reason="超时")
            try:
                if fail_at == i:
                    raise RuntimeError("模拟下游失败")
                detail = forward()
                self.completed.append((name, compensate))
                self.log.append(f"OK      {name} t={self.clock.now} {detail}")
            except Exception as e:
                self.log.append(f"FAIL    {name} t={self.clock.now} {e}")
                return self.compensate(reason="失败")
        self.log.append(f"DONE    全部 {len(steps)} 步成功")
        return True

    def compensate(self, extra=None, reason=""):
        self.log.append(f"--- 向后恢复：倒序补偿 {len(self.completed)} 步（{reason}）---")
        if extra:
            self.log.append(f"COMP    （失败步骤自身无需补偿，仅补偿已成功的）")
        for name, comp in reversed(self.completed):
            try:
                self.log.append(f"COMP    {name} -> {comp()}")
            except Exception as e:
                self.log.append(f"COMPERR {name} 补偿失败，转人工介入: {e}")
                return False
        self.completed.clear()
        return False

    @property
    def succeeded(self):
        return self.log[-1].startswith("DONE") if self.log else False


def make_steps():
    state = {"inventory": 10, "payment": 0, "points": 0}
    return [
        ("扣库存", lambda: (state.__setitem__("inventory", state["inventory"] - 1),
                            f"库存={state['inventory']}")[1],
         lambda: (state.__setitem__("inventory", state["inventory"] + 1),
                  f"库存还原={state['inventory']}")[1], 1),
        ("扣款", lambda: (state.__setitem__("payment", 199),
                          "扣款 199")[1],
         lambda: (state.__setitem__("payment", 0), "退款 199")[1], 2),
        ("加积分", lambda: (state.__setitem__("points", 199),
                            "积分 +199")[1],
         lambda: (state.__setitem__("points", 0), "积分回收")[1], 1),
    ], state

print("== 场景 1：全部成功 ==")
steps, state = make_steps()
s = Saga(); ok = s.execute(steps)
print("\n".join("  " + x for x in s.log))
print("  成功:", ok, "| 终态:", state)

print("\n== 场景 2：第 3 步失败 -> 倒序补偿前两步 ==")
steps, state = make_steps()
s2 = Saga(); ok2 = s2.execute(steps, fail_at=2)
print("\n".join("  " + x for x in s2.log))
print("  成功:", ok2, "| 补偿后终态:", state, "（回到初始）")

print("\n== 场景 3：超时触发补偿 ==")
steps, state = make_steps()
s3 = Saga(); ok3 = s3.execute(steps, timeout_at=1, deadline=5)
print("\n".join("  " + x for x in s3.log))
print("  成功:", ok3, "| 库存已还原:", state["inventory"] == 10)

print("\n== 场景 4：补偿失败 -> 人工介入 ==")
steps, state = make_steps()
def bad_comp():
    raise RuntimeError("退款接口不可用")
steps[1] = (steps[1][0], steps[1][1], bad_comp, steps[1][3])
s4 = Saga(); ok4 = s4.execute(steps, fail_at=2)
print("\n".join("  " + x for x in s4.log))
print("  成功:", ok4, "| 已标记人工介入")

print("\n== 补偿的设计约束 ==")
for line in [
    "  幂等：补偿可能重放多次，退款不能退两遍（第638课幂等键）",
    "  可重试：补偿失败进死信/人工，不能静默吞掉（第639课）",
    "  语义逆：C_i 抵消 T_i 的业务效果，不是「撤销数据库行」",
    "  不可补偿步骤（发短信）要放在最后，或改为「可忽略」步骤",
]:
    print("  -", line)

print("\n== 向前恢复 vs 向后恢复 ==")
for line in (
    "  向前恢复 forward: 失败就重试/换路继续，适合必须完成的步骤",
    "  向后恢复 backward: 倒序补偿，适合可撤销的预留类操作",
    "  混合: 前几步重试，超过阈值再整体补偿",
    "  选型取决于「步骤能否撤销」与「业务对最终一致性的要求」",
):
    print(" ", line)

print("\n== Saga vs 分布式事务 ==")
print(f"  {'维度':<10}{'2PC/XA':<20}{'Saga'}")
for row in (("锁", "跨服务持有，阻塞", "无全局锁"),
            ("一致性", "强一致", "最终一致"),
            ("复杂度", "协调者 + 回滚日志", "补偿逻辑 + 幂等"),
            ("适用", "同库/短事务", "微服务/长流程")):
    print(f"  {row[0]:<10}{row[1]:<20}{row[2]}")

# ===== 练习题 =====
# 1. 给每个步骤加「最多重试 3 次」的向前恢复，再决定何时转补偿。
# 2. 实现补偿幂等：用 event_id 集合避免同一补偿执行两次。
# 3. 把 Saga 状态持久化到 JSON，模拟进程重启后继续补偿。
# 4. 思考：为什么「不可补偿」的步骤要尽量排在流程末尾？
