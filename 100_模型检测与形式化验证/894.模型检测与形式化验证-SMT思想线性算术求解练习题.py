# ===== 第894课：模型检测与形式化验证-SMT思想：线性算术求解 =====
# 知识点：
#   - SAT 只懂布尔；真实问题含算术 -> SMT = SAT 骨架 + 理论求解器（T-solver）
#   - 本课实现线性整数算术的最小 T-solver：区间传播 + 二分分支
#   - 区间传播：由约束反推每个变量的可行范围，迭代到不动点
#   - 分支：取最小域变量劈成两半 —— 与 DPLL 完全同构
#   - 析取（或）约束 = 分支出多个子问题，SAT 管选择、T 管一致性
# 依赖：无（标准库）
import math


class Problem:
    def __init__(self, domains):
        self.domains = dict(domains)          # var -> (lo, hi) 含两端
        self.constraints = []                 # (terms, op, rhs)

    def add(self, terms, op, rhs):
        """terms: [(系数, 变量)]；op ∈ {'<=', '>=', '=='}"""
        self.constraints.append((terms, op, rhs))

    def copy(self):
        p = Problem(self.domains)
        p.constraints = list(self.constraints)
        return p

    # ---- 区间传播 ----
    def propagate(self):
        changed = True
        while changed:
            changed = False
            for terms, op, rhs in self.constraints:
                for coef, var in terms:
                    rest_min = rest_max = 0.0
                    for c2, v2 in terms:
                        if v2 == var:
                            continue
                        lo, hi = self.domains[v2]
                        rest_min += min(c2 * lo, c2 * hi)
                        rest_max += max(c2 * lo, c2 * hi)
                    lo, hi = self.domains[var]
                    targets = []
                    if op in ("<=", "=="):
                        # coef·var <= rhs - rest_min
                        bound = (rhs - rest_min) / coef
                        targets.append(("hi" if coef > 0 else "lo",
                                        math.floor(bound) if coef > 0 else math.ceil(bound)))
                    if op in (">=", "=="):
                        bound = (rhs - rest_max) / coef
                        targets.append(("lo" if coef > 0 else "hi",
                                        math.ceil(bound) if coef > 0 else math.floor(bound)))
                    for side, value in targets:
                        nlo, nhi = lo, hi
                        if side == "lo":
                            nlo = max(nlo, value)
                        else:
                            nhi = min(nhi, value)
                        if (nlo, nhi) != (lo, hi):
                            if nlo > nhi:
                                return False        # 冲突
                            self.domains[var] = (nlo, nhi)
                            lo, hi = nlo, nhi
                            changed = True
        return True

    # ---- 分支求解 ----
    def solve_all(self, limit=20):
        if not self.propagate():
            return []
        fixed = [v for v, (lo, hi) in self.domains.items() if lo == hi]
        if len(fixed) == len(self.domains):
            a = {v: self.domains[v][0] for v in self.domains}
            if self._verify(a):
                return [a]
            return []
        var = min(self.domains, key=lambda v: self.domains[v][1] - self.domains[v][0])
        lo, hi = self.domains[var]
        mid = (lo + hi) // 2
        results = []
        for sub_range in ((lo, mid), (mid + 1, hi)):
            p = self.copy()
            p.domains[var] = sub_range
            for sol in p.solve_all(limit - len(results)):
                results.append(sol)
                if len(results) >= limit:
                    return results
        return results

    def _verify(self, a):
        for terms, op, rhs in self.constraints:
            total = sum(c * a[v] for c, v in terms)
            if op == "<=" and total > rhs:
                return False
            if op == ">=" and total < rhs:
                return False
            if op == "==" and total != rhs:
                return False
        return True


def show_solutions(title, sols):
    print(f"  {title}: {len(sols)} 个解")
    for s in sols[:8]:
        print(f"    {s}")


print("== 最小例子：x + y = 10, x - y = 2 ==")
p = Problem({"x": (0, 20), "y": (0, 20)})
p.add([(1, "x"), (1, "y")], "==", 10)
p.add([(1, "x"), (-1, "y")], "==", 2)
sols = p.solve_all()
show_solutions("解", sols)
print("  区间传播链：x∈[6,6] 反推出 y∈[4,4] —— 零分支直达唯一解")

print("\n== 传播过程展示 ==")
p2 = Problem({"x": (0, 20), "y": (0, 20)})
p2.add([(1, "x"), (1, "y")], "==", 10)
p2.add([(1, "x"), (-1, "y")], "==", 2)
step = 0
while True:
    before = dict(p2.domains)
    if not p2.propagate() or p2.domains == before:
        break
    step += 1
    print(f"  传播第 {step} 轮: {p2.domains}")

print("\n== 经典应用：百钱买百鸡 ==")
print("  公鸡 5 元/只 x，母鸡 3 元/只 y，小鸡 1 元 3 只 z；共 100 元买 100 只")
p3 = Problem({"x": (0, 100), "y": (0, 100), "z": (0, 100)})
p3.add([(1, "x"), (1, "y"), (1, "z")], "==", 100)
p3.add([(15, "x"), (9, "y"), (1, "z")], "==", 300)     # 金额×3 消去分数
sols3 = p3.solve_all()
show_solutions("百鸡解", sols3)
print("  无分支爆搜 101³ ≈ 百万次；传播+分支通常几十次就收敛")

print("\n== 不等式与优化味：买票预算 ==")
print("  票A 30 元 x 张、票B 50 元 y 张，总预算 ≤ 200，y ≥ 2 且 x + y ≥ 5")
p4 = Problem({"x": (0, 10), "y": (0, 10)})
p4.add([(30, "x"), (50, "y")], "<=", 200)
p4.add([(1, "y")], ">=", 2)
p4.add([(1, "x"), (1, "y")], ">=", 5)
sols4 = p4.solve_all(limit=100)
best = max(sols4, key=lambda s: s["x"] + s["y"]) if sols4 else None
print(f"  可行解 {len(sols4)} 个，其中张数最多: {best}")
print("  这就是整数规划的雏形：线性约束 + 可行域搜索（无目标函数时是 CSP）")

print("\n== DPLL(T) 思想：析取约束 ==")
print("  任务 t1 满足 (t1 < 5) 或 (t1 > 8)；t2 = t1 + 3；t2 ≤ 12")
total = []
for case, (lo, hi) in enumerate(((0, 4), (9, 20))):
    p5 = Problem({"t1": (lo, hi), "t2": (0, 20)})
    p5.add([(1, "t2"), (-1, "t1")], "==", 3)
    p5.add([(1, "t2")], "<=", 12)
    sub = p5.solve_all()
    print(f"  分支{case}: t1∈[{lo},{hi}] -> {sub}")
    total += sub
print(f"  两个布尔分支各交给算术求解器验证 —— 这正是 DPLL(T) 的分工")
print(f"  若两分支都 UNSAT，则整体 UNSAT（理论冲突可反哺 SAT 学习子句）")

print("\n== 冲突检测演示 ==")
p6 = Problem({"a": (1, 3), "b": (1, 3)})
p6.add([(1, "a"), (1, "b")], "==", 1)
print(f"  a+b=1 但 a,b≥1: 传播后域 = "
      f"{p6.domains if not p6.propagate() else '（无冲突）'} -> 冲突: {not p6.propagate()}")
print("  区间一旦变空立即 UNSAT —— 不需要搜索到底")

print("\n== 小结 ==")
for line in (
    "  SMT = SAT 的布尔搜索 + 理论求解器的一致性检查，两层各司其职",
    "  区间传播是「免费的推理」：能推出必然性就不必分支",
    "  百鸡/调度/预算同一套求解器：线性约束建模能力极强",
    "  895 课：从『状态对不对』升级到『行为对不对』—— 时序逻辑",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「最小化目标」：在可行解中找目标线性函数最小的解（分支定界剪枝）。
# 2. 把区间传播扩展到乘法约束 x·y ≤ k，并用于「面积固定的矩形最大化周长」。
# 3. 给求解器加「冲突子句学习」：记录冲突时的变量界组合，避免重复冲突。
# 4. 思考：为什么整数比实数更容易传播（floor/ceil 削掉区间端点）？分数解的
#    存在如何让问题更难？
