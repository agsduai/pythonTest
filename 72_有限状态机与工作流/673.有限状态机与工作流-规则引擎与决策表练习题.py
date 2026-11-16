# ===== 第673课：有限状态机与工作流-规则引擎与决策表 =====
# 知识点：
#   - 规则引擎：把「if 条件 then 动作」从代码里抽成数据，可配置、可审计
#   - 决策表：条件列 × 规则行，命中哪行就执行对应动作，避免嵌套 if
#   - 冲突消解：优先级 priority / 首条命中 first / 全部命中 all /  specificity
#   - 条件用受限表达式（字典取值 + 比较），不执行任意代码
#   - 规则可导出成表格供业务人员 review，改动无需发版
#   - Rete 算法是生产级优化（大量事实+规则时避免 O(F×R) 全匹配）
# 依赖：无（标准库）
from dataclasses import dataclass, field
import operator

OPS = {
    "==": operator.eq, "!=": operator.ne, ">": operator.gt, ">=": operator.ge,
    "<": operator.lt, "<=": operator.le, "in": lambda a, b: a in b,
    "not in": lambda a, b: a not in b,
}


@dataclass
class Condition:
    field: str
    op: str
    value: object


@dataclass
class Rule:
    name: str
    when: list = field(default_factory=list)
    then: str = ""
    priority: int = 0
    stop: bool = False


def eval_condition(facts, cond):
    left = facts.get(cond.field)
    if left is None:
        return False
    return OPS[cond.op](left, cond.value)


def match(facts, rules, mode="first"):
    """返回命中的规则动作列表。mode: first / all / priority。"""
    hits = [r for r in rules if all(eval_condition(facts, c) for c in r.when)]
    if mode == "priority" and hits:
        best = max(r.priority for r in hits)
        hits = [r for r in hits if r.priority == best]
    if mode == "first":
        out = []
        for r in hits:
            out.append(r)
            if r.stop:
                break
        return out
    return hits


RULES = [
    Rule("新客首单", [Condition("is_new", "==", True),
                   Condition("amount", ">=", 100)], "发 20 元券", priority=10, stop=True),
    Rule("大额订单", [Condition("amount", ">=", 1000)], "转人工审核", priority=20),
    Rule("VIP 折扣", [Condition("level", "==", "VIP")], "打 9 折", priority=5),
    Rule("黑名单", [Condition("risk", "in", ("high", "blocked"))],
         "拒绝下单", priority=100, stop=True),
    Rule("普通订单", [], "无额外动作", priority=0),   # 兜底：条件为空恒真
]

CASES = [
    {"is_new": True, "amount": 150, "level": "普通", "risk": "low"},
    {"is_new": False, "amount": 2000, "level": "VIP", "risk": "low"},
    {"is_new": False, "amount": 300, "level": "普通", "risk": "high"},
    {"is_new": False, "amount": 50, "level": "普通", "risk": "low"},
]

print("== 决策表 ==")
print(f"  {'规则':<10}{'优先级':<7}{'条件':<38}{'动作':<12}{'stop'}")
for r in RULES:
    cond = ", ".join(f"{c.field}{c.op}{c.value!r}" for c in r.when) or "(兜底)"
    print(f"  {r.name:<10}{r.priority:<7}{cond[:36]:<38}{r.then:<12}{r.stop}")

for i, facts in enumerate(CASES, 1):
    print(f"\n== 案例 {i}: {facts} ==")
    for mode in ("first", "all", "priority"):
        hits = match(facts, RULES, mode)
        print(f"  {mode:<9}: {[r.then for r in hits]}")

print("\n== 冲突消解策略 ==")
for line in (
    "  first   : 按表顺序，遇到 stop 规则即停（适合互斥规则）",
    "  all     : 全部命中都执行（适合叠加优惠）",
    "  priority: 只执行最高优先级的一组（适合覆盖关系）",
    "  specificity: 条件更多者胜（更具体的规则优先）",
):
    print(" ", line)

print("\n== 命中明细（可审计）==")
facts = CASES[1]
for r in RULES:
    checks = [(f"{c.field}{c.op}{c.value!r}", eval_condition(facts, c)) for c in r.when]
    print(f"  {r.name:<10} {checks} -> {'命中' if all(v for _, v in checks) else '否'}")

print("\n== 规则即数据：导出 JSON ==")
import json
export = [{"name": r.name, "when": [vars(c) for c in r.when],
           "then": r.then, "priority": r.priority, "stop": r.stop} for r in RULES]
text = json.dumps(export, ensure_ascii=False)
print(f"  {len(text)} 字符，前 120: {text[:120]}...")
print("  业务系统可从 DB/配置中心加载这张表，代码不改")

print("\n== 受限表达式：不执行任意代码 ==")
print("  条件只支持字段取值 + 白名单运算符，无法调用 __import__ 等")
print("  反例：把条件写成字符串再 eval，等于开放远程代码执行")

print("\n== 复杂度与 Rete ==")
F, R = 10000, 500
print(f"  朴素全匹配: {F} 事实 × {R} 规则 = {F*R:,} 次条件判断")
print("  Rete: 把条件编成网络，事实变化只重算受影响的节点")
print("  规则少（几十条）时朴素实现完全够用，别过早优化")

print("\n== 工程要点 ==")
for line in [
    "  规则要有名字与版本号，命中日志留痕，便于事后解释「为什么拒单」",
    "  必须有兜底规则，避免任何事实都不命中时行为未定义",
    "  条件求值要处理缺字段（本例返回 False，也可显式报错）",
    "  规则变更要走评审 + 灰度，和代码发布同样严肃",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 specificity 消解：条件条数多的规则优先。
# 2. 增加「动作参数」：then 支持带数值的折扣，而不是纯字符串。
# 3. 给规则加生效时间窗（start/end），并写个按日期过滤的加载器。
# 4. 思考：为什么规则引擎必须禁用 eval？业务人员编辑的条件如何保证安全？
