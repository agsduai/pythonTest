# ===== 第891课：模型检测与形式化验证-布尔可满足性与DPLL =====
# 知识点：
#   - SAT：是否存在变量赋值使 CNF 公式全真 —— NP 完全问题的「母问题」
#   - CNF = 子句的合取，子句 = 文字的析取；文字 = 变量或其否定
#   - DPLL：单元传播 + 纯文字消除 + 分支回溯 —— 现代求解器的骨架
#   - 实际求解器还加：子句学习(CDCL)、VSIDS 启发式、重启
#   - 应用极广：芯片验证、调度、密码分析、依赖解析
# 依赖：无（标准库）
from itertools import product as iproduct


def brute_force_sat(cnf, nvars):
    """暴力枚举：真值参照与小规模验证。"""
    solutions = []
    for combo in iproduct((False, True), repeat=nvars):
        assign = {i + 1: combo[i] for i in range(nvars)}
        if clause_ok(cnf, assign):
            solutions.append(assign)
    return solutions


def clause_ok(cnf, assign):
    for clause in cnf:
        if not any(assign.get(abs(l), False) == (l > 0) for l in clause):
            return False
    return True


def simplify(cnf, var, value):
    """赋值 var=value 后化简：真子句移除，假文字删除。"""
    new = []
    for clause in cnf:
        if any(l == (var if value else -var) for l in clause):
            continue                                  # 子句已满足
        reduced = [l for l in clause if l != (-var if value else var)]
        if not reduced:
            return None                               # 空子句 = 冲突
        new.append(reduced)
    return new


def pure_literals(cnf):
    """纯文字：只以一种极性出现 -> 直接赋成真。"""
    counts = {}
    for clause in cnf:
        for l in clause:
            counts[l] = counts.get(l, 0) + 1
    pures = []
    for l in counts:
        if (-l) not in counts:
            pures.append(l)
    return pures


def dpll(cnf, assign, stats):
    stats["calls"] += 1
    if cnf == []:
        return dict(assign)
    if None in cnf or any(c == [] for c in cnf):
        return None
    # ---- 单元传播 ----
    unit = next((c[0] for c in cnf if len(c) == 1), None)
    while unit is not None:
        stats["units"] += 1
        var, value = abs(unit), unit > 0
        assign[var] = value
        cnf = simplify(cnf, var, value)
        if cnf is None:
            return None
        if cnf == []:
            return dict(assign)
        unit = next((c[0] for c in cnf if len(c) == 1), None)
    # ---- 纯文字消除 ----
    pures = pure_literals(cnf)
    if pures:
        l = pures[0]
        stats["pures"] += 1
        assign[abs(l)] = l > 0
        cnf = simplify(cnf, abs(l), l > 0)
        if cnf is None:
            return None
        return dpll(cnf, assign, stats)
    # ---- 分支 ----
    var = min(abs(l) for c in cnf for l in c)
    for value in (True, False):
        stats["branches"] += 1
        sub = simplify(cnf, var, value)
        if sub is not None:
            assign[var] = value
            result = dpll(sub, assign, stats)
            if result is not None:
                return result
            del assign[var]
    return None


def solve(cnf, nvars):
    stats = {"calls": 0, "units": 0, "pures": 0, "branches": 0}
    model = dpll([list(c) for c in cnf], {}, stats)
    return model, stats


def render_cnf(cnf):
    def lit(l):
        return ("¬" if l < 0 else "") + f"x{abs(l)}"
    return " ∧ ".join("(" + " ∨ ".join(lit(l) for l in c) + ")" for c in cnf)


print("== SAT 与 CNF 表示 ==")
cnf1 = [(1, 2), (-1, 3), (-2, -3)]
print(f"  公式: {render_cnf(cnf1)}")
model, stats = solve(cnf1, 3)
print(f"  可满足: {model is not None}")
print(f"  模型:   { {f'x{k}': v for k, v in sorted(model.items())} }")
print(f"  验证:   {clause_ok(cnf1, model)}")

print("\n== 全解枚举 ==")
sols = brute_force_sat(cnf1, 3)
print(f"  {render_cnf(cnf1)} 共有 {len(sols)} 个解")

print("\n== 鸽笼原理：不可满足的经典例子 ==")
def pigeonhole(pigeons, holes):
    """p 只鸽子进 h 个洞：每鸽一洞 + 每洞最多一鸽 -> h < p 时无解。"""
    cnf = []
    for p in range(pigeons):                      # 每只鸽子至少一个洞
        cnf.append(tuple(p * holes + h + 1 for h in range(holes)))
    for h in range(holes):                        # 每个洞最多一只鸽子
        for p1 in range(pigeons):
            for p2 in range(p1 + 1, pigeons):
                cnf.append((-(p1 * holes + h + 1), -(p2 * holes + h + 1)))
    return cnf


for pigeons, holes in ((3, 3), (4, 3)):
    cnf_p = pigeonhole(pigeons, holes)
    model, stats = solve(cnf_p, pigeons * holes)
    print(f"  {pigeons} 鸽 {holes} 洞 ({len(cnf_p)} 子句): "
          f"{'可满足' if model else '不可满足 ✓'}"
          f"   DPLL 调用 {stats['calls']}, 分支 {stats['branches']}")

print("\n== 单元传播的威力 ==")
cnf2 = [(1, 2), (-1, 2), (1, -2), (-1, -2), (3, 4), (-3, 4)]
model, stats = solve(cnf2, 4)
print(f"  公式: {render_cnf(cnf2)}")
print(f"  模型: {model}")
print(f"  统计: 单元传播 {stats['units']} 次（大量分支被确定性推理替代）")

print("\n== 相位忘带问题（unsat 演示）==")
cnf3 = [(1,), (-1,)]
model, stats = solve(cnf3, 1)
print(f"  (x1) ∧ (¬x1): {'可满足' if model else '不可满足 ✓（空子句冲突）'}")

print("\n== DPLL 搜索树可视化 ==")
print("  分支 = 试 True/False；冲突 = 回溯；单元传播 = 免费的确定性赋值")
print(f"  本课公式的搜索统计: {stats}")

print("\n== 小结 ==")
for line in (
    "  SAT 是验证/规划/组合设计的通用底座：问题编码成 CNF 即可求解",
    "  DPLL 三件套：单元传播、纯文字、分支回溯 —— 200 行内可见全貌",
    "  不可满足证明本身有价值：找到「为什么不行」的子句组合",
    "  892 课：把真实问题（着色/数独/皇后）编码成 CNF",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「解计数」版 DPLL（枚举所有解而不提前停止），与暴力枚举对照。
# 2. 实现子句学习雏形：冲突时记录导致冲突的赋值组合为学习子句，统计分支减少。
# 3. 编码「5 鸽 4 洞」并观察 DPLL 调用数的增长，体会 NP 难的实际表现。
# 4. 思考：为什么单元传播没有分支却能传播出「逻辑必然」？它和人类解数独的
#    「唯余法」有何对应？
