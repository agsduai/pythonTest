# ===== 第896课：模型检测与形式化验证-CTL与不动点计算 =====
# 知识点：
#   - CTL：路径量词（A/E）+ 时序算子（X/F/G/U）成对出现，如 EF/AG/AU
#   - CTL 的语义是「状态集上的不动点」：EF φ = 最小不动点 μZ. φ ∪ pre(Z)
#   - 不动点计算 = 反复做前驱运算直到状态集不再变化 —— 又是循环求解
#   - AG φ 与 EF ¬φ 互补：验证 AG p 等价于 EF ¬p 是否为空
#   - 反例与正例：EF/EX 给路径，EG/AF 给不同形状的证人
# 依赖：无（标准库）
from collections import deque


class Model:
    def __init__(self):
        self.labels = {}
        self.trans = {}

    def add(self, s, props, nexts):
        self.labels[s] = set(props)
        self.trans[s] = set(nexts)

    def pre(self, states):
        """pre: 有边通向 states 的状态集。"""
        return {s for s, nexts in self.trans.items() if nexts & states}

    def sat_atoms(self, prop):
        return {s for s, labels in self.labels.items() if prop in labels}

    # ---- CTL 算子 ----
    def sat_EX(self, states):
        return self.pre(states)

    def sat_EF(self, states):
        z = set(states)
        while True:
            new = z | self.pre(z)
            if new == z:
                return z
            z = new

    def sat_EG(self, states):
        z = set(states)                       # 最大不动点：νZ. S ∩ pre(Z)
        while True:
            new = z & self.pre(z)
            if new == z:
                return z
            z = new

    def sat_AF(self, states):
        z = set(states)
        while True:
            # μZ. φ ∪ {s | s 的所有后继 ∈ Z}
            new = z | {s for s, nexts in self.trans.items()
                       if nexts and nexts <= z}
            if new == z:
                return z
            z = new

    def sat_AG(self, states):
        z = set(states)
        while True:
            # νZ. φ ∩ {s | s 的所有后继 ∈ Z}
            new = z & {s for s, nexts in self.trans.items()
                       if not nexts or nexts <= z}
            if new == z:
                return z
            z = new

    def sat(self, formula):
        """递归求值。formula: ('atom', p) / ('not', f) / ('and', f, g)
        / ('EX', f) / ('EF', f) / ('EG', f) / ('AF', f) / ('AG', f)"""
        op = formula[0]
        if op == "atom":
            return self.sat_atoms(formula[1])
        if op == "not":
            return set(self.labels) - self.sat(formula[1])
        if op == "and":
            return self.sat(formula[1]) & self.sat(formula[2])
        if op == "or":
            return self.sat(formula[1]) | self.sat(formula[2])
        if op == "EX":
            return self.sat_EX(self.sat(formula[1]))
        if op == "EF":
            return self.sat_EF(self.sat(formula[1]))
        if op == "EG":
            return self.sat_EG(self.sat(formula[1]))
        if op == "AF":
            return self.sat_AF(self.sat(formula[1]))
        if op == "AG":
            return self.sat_AG(self.sat(formula[1]))
        raise ValueError(op)

    def witness_path(self, start, target_set):
        """EX/EF 的证人：从 start 到 target_set 的路径。"""
        if start not in target_set:
            return None
        if any(nxt in target_set for nxt in self.trans[start]):
            for nxt in self.trans[start]:
                if nxt in target_set:
                    return [start, nxt]
        for nxt in self.trans[start]:
            sub = self.witness_path(nxt, target_set)
            if sub is not None:
                return [start] + sub
        return None


def render(f):
    op = f[0]
    if op == "atom":
        return f[1]
    if op == "not":
        return f"¬{render(f[1])}"
    if op in ("and", "or"):
        return f"({render(f[1])} {'∧' if op == 'and' else '∨'} {render(f[2])})"
    return f"{op} {render(f[1])}"


print("== 协议状态机 ==")
m = Model()
m.add("idle", ["idle"], ["try1"])
m.add("try1", ["try"], ["crit1", "backoff"])
m.add("crit1", ["crit", "p1"], ["idle"])
m.add("backoff", ["wait"], ["try1"])
m.add("try2", ["try", "p2"], ["crit2"])
m.add("crit2", ["crit"], ["idle"])
# p2 与 p1 抢占：try1 也可以去 crit2? 简化：只有 try2->crit2; 加一条竞争边
m.trans["try1"].add("crit2")
print("  状态: idle -> try1 -> {crit1, crit2, backoff}; try2 -> crit2 -> idle")
print(f"  标注: {m.labels}")

print("\n== 基本算子 ==")
crit = m.sat(("atom", "crit"))
print(f"  sat(crit) = {sorted(crit)}")
print(f"  sat(EX crit) = {sorted(m.sat(('EX', ('atom', 'crit'))))}")
print(f"  sat(EF crit) = {sorted(m.sat(('EF', ('atom', 'crit'))))}")
print(f"  sat(AF crit) = {sorted(m.sat(('AF', ('atom', 'crit'))))}")
print("  EF = 存在某条路能到（可能）；AF = 所有路都最终到（必然）—— 差别一目了然")

print("\n== 不变量：AG ¬(p1 ∧ p2)===")
safe = m.sat(("AG", ("not", ("and", ("atom", "p1"), ("atom", "p2")))))
print(f"  AG¬(p1∧p2) 成立的状态 = {sorted(safe)}")
print(f"  等价检查 EF(p1∧p2) = {sorted(m.sat(('EF', ('and', ('atom', 'p1'), ('atom', 'p2')))))}")
print("  AG φ 的满足集 = 全集 − EF¬φ 的状态 —— 互补性一目了然")
if crit & m.sat(("and", ("atom", "p1"), ("atom", "p2"))):
    print("  违反！存在同时处于两个临界区的状态 -> 安全性质被破坏")

print("\n== 不动点迭代过程 ==")
target = m.sat_atoms("crit")
z = set(target)
print(f"  EF crit 不动点迭代: 初始 = {sorted(z)}")
it = 0
while True:
    new = z | m.pre(z)
    it += 1
    if new == z:
        break
    z = new
    print(f"    第 {it} 轮加入前驱: {sorted(new)}")
print(f"  {it} 轮收敛 -> {sorted(z)}")
print("  最小不动点 = 「不断向前驱扩展」；最大不动点 = 「不断剪掉不合格状态」")

print("\n== EG：存在一条永远满足 φ 的路 ==")
non_crit = m.sat(("EG", ("or", ("atom", "idle"),
                             ("or", ("atom", "wait"), ("atom", "try")))))
print(f"  sat(EG(idle∨wait∨try)) = {sorted(non_crit)}")
print("  try1 -> backoff -> try1 是一个全程满足 (idle∨wait∨try) 的环")
print("  最大不动点的直觉：反复删掉『下一步可能不满足 φ』的状态，剩下的都有环")

print("\n== AG：对 everywhere 性质给出证人 ==")
ag_states = m.sat(("AG", ("or", ("atom", "idle"), ("atom", "wait"))))
print(f"  sat(AG(idle∨wait)) = {sorted(ag_states)}")
print("  （空集 = 没有任何状态能保证永远只处于 idle/wait —— 系统总能离开）")

print("\n== EF 的证人路径 ==")
target_p2 = m.sat(("and", ("atom", "crit"), ("atom", "p2")))
path = m.witness_path("idle", target_p2)
print(f"  从 idle 到『p2 临界区』的路径: {path}")
print("  模型检测不仅说『能到达』，还能给出怎么到达 —— 反例/证人一体两面")

print("\n== 复合公式 ==")
formulas = [
    ("AG", ("atom", "idle")),                            # 没有状态能永远空闲（假）
    ("EF", ("and", ("atom", "crit"), ("atom", "p2"))),   # 能进 p2 临界区（真）
    ("AF", ("atom", "idle")),                            # 4 个状态必然回 idle
    ("AG", ("not", ("atom", "p2"))),                     # 没有状态保证永不进 p2（假）
]
print(f"  {'公式':<44}{'满足状态数':>10}")
for f in formulas:
    result = m.sat(f)
    print(f"  {render(f):<44}{len(result):>10}")

print("\n== 小结 ==")
for line in (
    "  CTL 检查 = 状态集上的不动点方程，实现就是 while 循环 + 前驱运算",
    "  μ（最小）/ν（最大）不动点的区别对应 EF/EG 的『可能 vs 永远』",
    "  AG φ = 补集上的 EF —— 工程中不变量检查都走这条捷径",
    "  897 课：从「模型检测」走向「程序验证」—— 循环不变量",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 AU 算子（μZ. φ ∪ (q ∧ pre_all(Z))）并验证 AG ↔ ¬EF¬ 的互补性。
# 2. 给 sat_EF 加「反例/证人路径提取」，从 idle 输出到 crit2 的具体路径。
# 3. 在 895 课的红绿灯模型上求 EG yellow，解释为什么结果为空。
# 4. 思考：为什么 EG 用最大不动点而 EF 用最小不动点？交换会得到什么错误结果？
