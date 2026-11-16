# ===== 第895课：模型检测与形式化验证-线性时序逻辑与性质检查 =====
# 知识点：
#   - 模型检测 = 「系统模型 + 性质公式」自动验证：模型给全部行为，公式给要求
#   - 系统模型：Kripke 结构（状态 + 转移 + 原子命题标注）
#   - LTL 算子：X p（下一状态）、F p（最终）、G p（永远）、p U q（直到）
#   - 有限迹上的 LTL 检查：把「性质」变成迹上的递归求值
#   - 不变量（G p）检查 = 可达性搜索；反例 = 到达违反点的具体迹
# 依赖：无（标准库）
from collections import deque


class Kripke:
    """状态机模型：states + transitions + 标注。"""

    def __init__(self):
        self.labels = {}                # state -> set(原子命题)
        self.trans = {}                 # state -> set(后继)

    def add_state(self, s, props):
        self.labels[s] = set(props)
        self.trans.setdefault(s, set())

    def add_trans(self, a, b):
        self.trans[a].add(b)
        self.trans.setdefault(b, set())


def eval_ltl_trace(trace, formula):
    """在有限迹上求值 LTL 公式（bounded 语义）。
    trace: [set(命题)]；formula: 嵌套元组。"""
    n = len(trace)

    def ev(f, i):
        if isinstance(f, str):                       # 原子命题
            return f in trace[i]
        op = f[0]
        if op == "not":
            return not ev(f[1], i)
        if op == "and":
            return ev(f[1], i) and ev(f[2], i)
        if op == "or":
            return ev(f[1], i) or ev(f[2], i)
        if op == "X":
            return i + 1 < n and ev(f[1], i + 1)
        if op == "F":
            return any(ev(f[1], j) for j in range(i, n))
        if op == "G":
            return all(ev(f[1], j) for j in range(i, n))
        if op == "U":                                # p U q
            return any(ev(f[2], j) and all(ev(f[1], k) for k in range(i, j))
                       for j in range(i, n))
        raise ValueError(op)

    return ev(formula, 0)


def reachable_states(k, initial):
    seen = {initial}
    queue = deque([initial])
    while queue:
        v = queue.popleft()
        for w in k.trans[v]:
            if w not in seen:
                seen.add(w)
                queue.append(w)
    return seen


def check_invariant(k, initial, prop_fn):
    """G p：BFS 可达状态全满足谓词。返回 (通过?, 反例迹)。"""
    seen = {initial: None}
    queue = deque([initial])
    while queue:
        v = queue.popleft()
        if not prop_fn(k.labels[v]):
            path = [v]
            while seen[v] is not None:
                v = seen[v]
                path.append(v)
            return False, list(reversed(path))
        for w in k.trans[v]:
            if w not in seen:
                seen[w] = v
                queue.append(w)
    return True, None


print("== 红绿灯模型 ==")
k = Kripke()
for state, props, nexts in (
    ("红1", ["red"], ["绿1"]),
    ("绿1", ["green"], ["黄1"]),
    ("黄1", ["yellow"], ["红2"]),
    ("红2", ["red"], ["绿2"]),
    ("绿2", ["green"], ["黄2"]),
    ("黄2", ["yellow"], ["红1"]),
):
    k.add_state(state, props)
    for nxt in nexts:
        k.add_trans(state, nxt)
print("  状态: 红1→绿1→黄1→红2→绿2→黄2→红1（周期）")

print("\n== 有限迹上的 LTL 求值 ==")
trace = [k.labels[s] for s in ("红1", "绿1", "黄1", "红2", "绿2", "黄2")]
tests = [
    (("X", "green"), "下一状态是绿灯"),
    (("F", "green"), "最终会出现绿灯"),
    (("not", ("G", "yellow")), "并非始终黄灯"),
    (("G", ("not", ("and", "red", "green"))), "红绿不同亮"),
    (("U", "red", "green"), "红灯保持直到绿灯"),
]
print(f"  {'公式':<28}{'结果':>8}  含义")
for f, desc in tests:
    result = eval_ltl_trace(trace, f)
    def render(g):
        if isinstance(g, str):
            return g
        op = g[0]
        if op == "not":
            return f"¬{render(g[1])}"
        if op in ("and", "or"):
            return f"({render(g[1])} {'∧' if op == 'and' else '∨'} {render(g[2])})"
        if op == "X":
            return f"X {render(g[1])}"
        if op == "F":
            return f"F {render(g[1])}"
        if op == "G":
            return f"G {render(g[1])}"
        if op == "U":
            return f"({render(g[1])} U {render(g[2])})"
        return "?"
    print(f"  {render(f):<28}{str(result):>8}  {desc}")
print("  注意：G/F 在『有限迹』上只看到迹的有限前缀 —— 完整语义需无限迹（lasso）")

print("\n== 不变量检查：反例自动生成 ==")
ok_safe, cex_safe = check_invariant(
    k, "红1", lambda labels: not ("red" in labels and "green" in labels))
print(f"  G ¬(red∧green)（无红绿同亮）: {'通过' if ok_safe else f'违反，反例 {cex_safe}'}")
ok_red, cex_red = check_invariant(k, "红1", lambda labels: "red" in labels)
print(f"  G red（永远红灯）: {'通过' if ok_red else '违反'}")
print(f"  反例迹: {cex_red} —— 红1 之后就是绿1，性质不成立，模型检测直接给出路径")

print("\n== 有 bug 的红绿灯 ==")
k2 = Kripke()
for state, props, nexts in (
    ("红1", ["red"], ["绿1"]),
    ("绿1", ["green"], ["黄1"]),
    ("黄1", ["yellow"], ["红2", "绿1"]),       # 黄灯会跳回绿灯（错误设计）
    ("绿2", ["green"], ["红2"]),
    ("红2", ["red"], ["绿2"]),
):
    k2.add_state(state, props)
    for nxt in nexts:
        k2.add_trans(state, nxt)
ok3, cex3 = check_invariant(k2, "红1", lambda labels: not ("yellow" in labels and "green" in labels))
print(f"  性质: G ¬(yellow∧green) -> {'通过' if ok3 else '违反'}（黄1 本身只有一个标注，通过）")
ok4, cex4 = check_invariant(k2, "红1", lambda labels: "yellow" not in labels or "green" not in labels)
deadlock_states = [s for s in k2.trans if not k2.trans[s]]
print(f"  无死锁检查（每个状态有后继）: {'通过' if not deadlock_states else f'死锁状态 {deadlock_states}'}")
print("  模型检测的价值：自动给出「怎么走到的」—— 人只需读反例改设计")

print("\n== 活性直觉：F green ==")
print("  G→F green（每个红灯后最终有绿灯）在两个模型上都成立")
print("  完整的 LTL 模型检测把性质转成 Büchi 自动机再查积空语言")
print("  —— 复杂度高但自动化程度也高；不变量/可达性检查是 90% 的日常用法")

print("\n== 与第71章 FSM 的分工 ==")
for line in (
    "  71 章 FSM：描述『业务流程怎么走』（建模）",
    "  本章：验证『走的每条路都满足性质』（检查）",
    "  组合拳：FSM 建模 + LTL 性质 + 自动反例 = 可信设计的闭环",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  LTL 把时序需求写成公式：X/F/G/U 四个算子覆盖绝大多数需求",
    "  不变量检查 = 可达性搜索 + 反例回溯，实现只要几十行",
    "  反例是模型检测对工程师最友好的输出 —— 不用猜 bug 在哪",
    "  896 课：分支时序 CTL 与不动点计算",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「lasso 反例」检查：在可达图中找「颈 + 环」结构近似无限迹语义。
# 2. 把 LTL 检查扩展到多条迹（所有初始状态的迹都要满足），统计违反比例。
# 3. 为自动售货机建模（投币/出货/退币），验证「投币后最终出货或退币」。
# 4. 思考：为什么 G p 在无限迹上需要检查「所有时刻」而实现只需一次 BFS？
#    可达性闭包起了什么作用？
