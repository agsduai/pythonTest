# ===== 第753课：编译原理与代码优化-寄存器分配与图着色 =====
# 知识点：
#   - 寄存器分配：把无限多的虚拟寄存器映射到有限的物理寄存器 R 个
#   - 干扰图 interference graph：两个变量若同时活跃则连边，不能共用寄存器
#   - 图着色：用 R 种颜色给干扰图着色；k 色问题是 NP 完全，用启发式
#   - 简化 simplify：反复删度数 < R 的节点压栈；溢出 spill：度数都 ≥ R 时选一个放内存
#   - 选择 select：弹栈时给节点挑一个邻居没用过的颜色
#   - 合并 coalescing：把 copy 相关的变量尽量合并，减少搬运指令
#   - 本课实现 Chaitin-Briggs 风格的分配器，并统计 spill 数量
# 依赖：无（标准库）
from collections import defaultdict


def liveness_intervals(prog):
    """极简活跃区间：变量从首次 def 到最后一次 use 的指令序号范围。"""
    first, last = {}, {}
    for i, (dst, op, x, y) in enumerate(prog):
        for t in (x, y):
            if isinstance(t, str):
                last[t] = i
        if dst not in first:
            first[dst] = i
        last.setdefault(dst, i)
    return {v: (first[v], last[v]) for v in first}


def build_interference(intervals):
    """区间重叠 => 干扰边（同时活跃）。"""
    names = sorted(intervals)
    graph = {v: set() for v in names}
    for i, a in enumerate(names):
        lo_a, hi_a = intervals[a]
        for b in names[i+1:]:
            lo_b, hi_b = intervals[b]
            if lo_a <= hi_b and lo_b <= hi_a:     # 区间相交
                graph[a].add(b); graph[b].add(a)
    return graph


def color(graph, R):
    """Chaitin 风格：simplify 栈 + spill 决策 + select 着色。"""
    degrees = {v: len(graph[v]) for v in graph}
    work = set(graph)
    stack, spills = [], []
    while work:
        low = [v for v in work if degrees[v] < R]
        if low:
            v = min(low, key=lambda x: (degrees[x], x))
            stack.append(v); work.remove(v)
            for nb in graph[v] & work:
                degrees[nb] -= 1
        else:
            # 全都是高度数节点：选「度数最大但使用次数少」的溢出（这里用度数最小启发式）
            v = max(work, key=lambda x: (degrees[x], x))
            spills.append(v); work.remove(v)
            for nb in graph[v] & work:
                degrees[nb] -= 1
    assign = {}
    while stack:
        v = stack.pop()
        used = {assign[nb] for nb in graph[v] if nb in assign}
        for c in range(R):
            if c not in used:
                assign[v] = c; break
        else:
            spills.append(v)     # 无可用颜色，也溢出
    return assign, spills


PROG = [
    ("a", "const", 1, None),
    ("b", "const", 2, None),
    ("c", "+", "a", "b"),
    ("d", "*", "c", "c"),
    ("e", "+", "a", "d"),
    ("f", "-", "e", "b"),
    ("out", "copy", "f", None),
]

print("== 程序与活跃区间 ==")
for i, ins in enumerate(PROG):
    print(f"  {i}: {ins}")
iv = liveness_intervals(PROG)
for v in sorted(iv):
    print(f"    {v:<5}: {iv[v]}")

graph = build_interference(iv)
print("\n== 干扰图 ==")
for v in sorted(graph):
    print(f"  {v:<5}: {sorted(graph[v])}")
print(f"  边数 = {sum(len(x) for x in graph.values()) // 2}")
print(f"  最大度数 = {max(len(x) for x in graph.values())}")

print("\n== 寄存器数量 vs 溢出 ==")
for R in (2, 3, 4, 5, 6):
    assign, spills = color(graph, R)
    print(f"  R={R}: 着色成功 {len(assign)} 个变量, 溢出 {len(spills)} 个 "
          f"{sorted(spills) if spills else ''}")
    if assign:
        print(f"      分配: {dict(sorted(assign.items()))}")

print("\n== 图着色复杂度与色数 ==")
print("  求最小寄存器数 = 求图的色数（chromatic number），NP 完全")
print("  弦图/区间图可在多项式时间最优着色；一般 CFG 干扰图不行")
for R in range(1, 8):
    _, spills = color(graph, R)
    print(f"  R={R}: {'无溢出' if not spills else f'{len(spills)} 个溢出'}")
    if not spills:
        break

print("\n== Spill 的代价 ==")
for line in (
    "  溢出变量放到栈帧（内存），每次读写变成 load/store",
    "  选择溢出对象要考虑：使用频率、是否在循环内、重算成本",
    "  循环内的高频变量优先保寄存器（第752课循环优化联动）",
    "  重新分配：插入 spill 代码后活跃区间变短，可再跑一遍着色",
):
    print(" ", line)

print("\n== 合并 Coalescing ==")
print("  x = y 这类 copy 若两端不干扰，可合并成一个寄存器，省掉一条 move")
print("  激进合并可能让图不可着色，需要保守判据（Briggs/George）")

print("\n== 线性扫描 vs 图着色 ==")
print(f"  {'算法':<16}{'速度':<12}{'质量':<12}{'适用'}")
for row in (("图着色", "慢", "好", "AOT 编译器 -O2"),
            ("线性扫描", "快", "一般", "JIT / 快速编译"),
            ("PBQP/ILP", "最慢", "最好", "研究/极致优化")):
    print(f"  {row[0]:<16}{row[1]:<12}{row[2]:<12}{row[3]}")

print("\n== 工程要点 ==")
for line in [
    "  SSA 形式下干扰图是弦图，可多项式最优着色（第748课）",
    "  调用约定要保留 callee-saved/参数寄存器，不能全部分配",
    "  寄存器对（如 64 位值占两个 32 位寄存器）需要别名约束",
    "  x86 寄存器少且不规则，RISC 寄存器多，分配难度差异大",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现带「使用频率权重」的溢出选择，减少热循环里的 spill。
# 2. 加入 copy coalescing，并验证不会让 R=3 的图变得不可着色。
# 3. 实现线性扫描分配器，对比与图着色的分配结果与耗时。
# 4. 思考：为什么 SSA 的干扰图是弦图，能让着色变简单？
