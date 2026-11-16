# ===== 第892课：模型检测与形式化验证-SAT建模：着色/数独/皇后 =====
# 知识点：
#   - SAT 建模三步：设计变量含义 -> 写约束（必有一个/至多一个/互斥）-> 解码解
#   - 「恰一」编码：至少一个 (x∨y∨z) + 两两不同 (¬x∨¬y...)
#   - 图着色：x_{v,c} = 顶点 v 用颜色 c；约束 = 每点恰一色 + 相邻不同色
#   - N 皇后：每行/列/对角线互斥；数独同理加宫约束
#   - 编码质量直接决定求解速度：变量数、子句数、传播强度都要权衡
# 依赖：无（标准库）
from itertools import combinations


def clause_ok(cnf, assign):
    return all(any(assign.get(abs(l), False) == (l > 0) for l in c) for c in cnf)


def simplify(cnf, var, value):
    new = []
    for clause in cnf:
        if (var if value else -var) in clause:
            continue
        reduced = [l for l in clause if l != (-var if value else var)]
        if not reduced:
            return None
        new.append(reduced)
    return new


def dpll(cnf, assign):
    cnf = [list(c) for c in cnf]
    while True:                                  # 单元传播
        unit = next((c[0] for c in cnf if len(c) == 1), None)
        if unit is None:
            break
        assign[abs(unit)] = unit > 0
        cnf = simplify(cnf, abs(unit), unit > 0)
        if cnf is None:
            return None
    if not cnf:
        return dict(assign)
    if any(len(c) == 0 for c in cnf):
        return None
    var = min(abs(l) for c in cnf for l in c)
    for value in (True, False):
        sub = simplify(cnf, var, value)
        if sub is not None:
            assign[var] = value
            result = dpll(sub, assign)
            if result is not None:
                return result
            del assign[var]
    return None


def render_cnf(cnf):
    def lit(l):
        return ("¬" if l < 0 else "") + f"x{abs(l)}"
    return " ∧ ".join("(" + " ∨ ".join(lit(l) for l in c) + ")" for c in cnf)


def exactly_one(vars_, var_id):
    """恰一约束的 CNF：至少一 + 两两至多一。"""
    cnf = [tuple(var_id(v) for v in vars_)]
    for a, b in combinations(vars_, 2):
        cnf.append((-var_id(a), -var_id(b)))
    return cnf


print("== 图着色 ==")
graph = {0: [1, 2], 1: [2, 3], 2: [3], 3: []}
colors = ["红", "绿", "蓝"]
vid = lambda v, c: v * len(colors) + c + 1
nv = len(graph) * len(colors)
cnf = []
for v in graph:
    cnf += exactly_one(range(len(colors)), lambda c, v=v: vid(v, c))
for u in graph:
    for w in graph[u]:
        if u < w:
            for c in range(len(colors)):
                cnf.append((-vid(u, c), -vid(w, c)))
print(f"  图: {graph}   颜色: {colors}")
print(f"  编码: {nv} 个变量 / {len(cnf)} 条子句")
model = dpll(cnf, {})
if model:
    coloring = {v: colors[next(c for c in range(len(colors))
                                  if model.get(vid(v, c)))]
                for v in graph}
    print(f"  着色方案: {coloring}")
    ok = all(coloring[u] != coloring[w] for u in graph for w in graph[u] if u < w)
    print(f"  相邻不同色验证: {ok}")
else:
    print("  不可满足")

print("\n== 颜色数不够时 ==")
vid2 = lambda v, c: v * 2 + c + 1
cnf2 = []
for v in graph:
    cnf2 += exactly_one(range(2), lambda c, v=v: vid2(v, c))
for u in graph:
    for w in graph[u]:
        if u < w:
            for c in range(2):
                cnf2.append((-vid2(u, c), -vid2(w, c)))
model2 = dpll(cnf2, {})
print(f"  2 色方案: {'存在' if model2 else '不可满足 ✓（该图含奇环，需要 3 色）'}")

print("\n== 4 皇后 ==")
n = 4
qvar = lambda r, c: r * n + c + 1
cnf_q = []
for r in range(n):                                   # 每行恰一
    cnf_q += exactly_one(range(n), lambda c, r=r: qvar(r, c))
for c in range(n):                                   # 每列恰一
    cnf_q += exactly_one(range(n), lambda r, c=c: qvar(r, c))
for r in range(n):                                   # 对角互斥
    for c in range(n):
        for r2 in range(n):
            for c2 in range(n):
                if (r, c) < (r2, c2) and (abs(r - r2) == abs(c - c2)
                                          or c == c2 or r == r2):
                    cnf_q.append((-qvar(r, c), -qvar(r2, c2)))
print(f"  编码: {n * n} 变量 / {len(cnf_q)} 子句")
model_q = dpll(cnf_q, {})
if model_q:
    queens = [(r, c) for r in range(n) for c in range(n) if model_q.get(qvar(r, c))]
    print(f"  皇后位置: {queens}")
    for r in range(n):
        print("    " + " ".join("♛" if (r, c) in queens else "." for c in range(n)))
    conflict = any(abs(r1 - r2) == abs(c1 - c2) or r1 == r2 or c1 == c2
                   for (r1, c1) in queens for (r2, c2) in queens
                   if (r1, c1) < (r2, c2))
    print(f"  互斥验证: {'通过' if not conflict else '冲突!'}")

print("\n== 4x4 数独 ==")
puzzle = [[1, 0, 3, 0],
          [0, 4, 0, 2],
          [2, 0, 0, 3],
          [0, 3, 2, 0]]
svar = lambda r, c, d: (r * 4 + c) * 4 + d + 1
cnf_s = []
for r in range(4):                                   # 给定数字
    for c in range(4):
        if puzzle[r][c]:
            cnf_s.append((svar(r, c, puzzle[r][c] - 1),))
        else:
            cnf_s += exactly_one(range(4), lambda d, r=r, c=c: svar(r, c, d))
for r in range(4):                                   # 行互斥
    for d in range(4):
        cnf_s += [(-svar(r, c, d), -svar(r, c2, d))
                  for c in range(4) for c2 in range(c + 1, 4)]
for c in range(4):                                   # 列互斥
    for d in range(4):
        cnf_s += [(-svar(r, c, d), -svar(r2, c, d))
                  for r in range(4) for r2 in range(r + 1, 4)]
for br in range(2):                                  # 2x2 宫互斥
    for bc in range(2):
        cells = [(br * 2 + r, bc * 2 + c) for r in range(2) for c in range(2)]
        for d in range(4):
            cnf_s += [(-svar(r1, c1, d), -svar(r2, c2, d))
                      for (r1, c1), (r2, c2) in combinations(cells, 2)]
print(f"  编码: {64} 变量 / {len(cnf_s)} 子句")
model_s = dpll(cnf_s, {})
if model_s:
    print("  解:")
    for r in range(4):
        print("    " + " ".join(
            str(next(d + 1 for d in range(4) if model_s.get(svar(r, c, d))))
            for c in range(4)))
else:
    print("  不可满足 —— 给定值自身矛盾（谜题出错了）")
print("  数独/皇后/着色共用同一套约束模板 —— SAT 建模的复用性")

print("\n== 小结 ==")
for line in (
    "  建模 = 把『问题的自然语言约束』翻译成布尔逻辑",
    "  恰一/互斥/传递等模板可以组合出绝大多数组合问题",
    "  约束强度影响传播：两两互斥比「计数」弱但简单够用",
    "  893 课：函数级复用 —— BDD 把布尔函数压缩成规范图",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 用「序列编码」（顺序编码）重写恰一约束（递归 ∀i: x_i → ¬x_{i+1}...），
#    对比子句数与求解时间。
# 2. 编码 8 皇后并统计 DPLL 分支次数，与「逐行深度优先」原生搜索对比。
# 3. 实现「求所有解」的数独计数器（Unique 数独验证：解数恰为 1）。
# 4. 思考：为什么两两互斥编码在 n 大时子句数爆炸？O(n log n) 的命令式编码
#    （辅助变量 + 电路）如何解决？
