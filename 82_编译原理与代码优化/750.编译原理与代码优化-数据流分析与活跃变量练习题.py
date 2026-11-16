# ===== 第750课：编译原理与代码优化-数据流分析与活跃变量 =====
# 知识点：
#   - 数据流分析：在 CFG 上迭代求解不动点，为每个程序点算「事实」
#   - 活跃变量 liveness：某变量在程序点之后还会被读吗（用于寄存器分配/死代码消除）
#   - 反向分析：LiveIn(b) = Use(b) ∪ (LiveOut(b) - Def(b))；LiveOut = ∪ LiveIn(succ)
#   - 到达定义 reaching definitions：正向分析，哪些定义可能到达某点
#   - 可用表达式 available expressions：正向 must 分析，用于公共子表达式消除
#   - 单调框架 + 有限格 => 迭代必然收敛；交/并取决于 may/must
#   - 本课实现活跃变量与到达定义，并演示用活跃信息删死代码
# 依赖：无（标准库）
from collections import defaultdict


KEYWORDS = {"if", "goto", "return", "if_false", "if_true"}


def is_var(tok):
    """标识符但不是关键字，也不是 L/B 开头的跳转标签。"""
    return (tok.isidentifier() and tok not in KEYWORDS
            and not (tok.startswith(("L", "B")) and tok[1:].isdigit()))


def parse_block(body):
    """从指令文本提取 (def集合, use集合)；use 只算「本块内先定义前」的读取。"""
    defs = set()
    for ins in body:
        parts = ins.replace("=", " = ").split()
        if "=" in parts:
            eq = parts.index("=")
            if eq > 0:
                defs.add(parts[eq - 1])
    ordered_use = set()
    defined_so_far = set()
    for ins in body:
        parts = ins.replace("=", " = ").split()
        if "=" in parts:
            eq = parts.index("="); dst = parts[eq-1] if eq > 0 else None
            for tok in parts[eq+1:]:
                if is_var(tok) and tok not in defined_so_far:
                    ordered_use.add(tok)
            if dst: defined_so_far.add(dst)
        else:
            for tok in parts[1:]:
                if is_var(tok) and tok not in defined_so_far:
                    ordered_use.add(tok)
    return defs, ordered_use


BLOCKS = {
    "B0": ["i = 0", "s = 0"],
    "B1": ["t = i * 2", "s = s + t", "i = i + 1", "if i < 10 goto B1"],
    "B2": ["x = s + 1", "y = 99", "return x"],     # y 定义后从未使用 = 死代码
}
EDGES = {"B0": ["B1"], "B1": ["B1", "B2"], "B2": []}

print("== 基本块与 def/use ==")
du = {}
for b, body in BLOCKS.items():
    du[b] = parse_block(body)
    print(f"  {b}: def={sorted(du[b][0])} use={sorted(du[b][1])}")
    for ins in body:
        print("     ", ins)


def liveness(blocks, edges, du):
    """反向 may 分析：迭代求 LiveIn/LiveOut 不动点。"""
    preds = defaultdict(list)
    for b, succs in edges.items():
        for s in succs: preds[s].append(b)
    live_in = {b: set() for b in blocks}
    live_out = {b: set() for b in blocks}
    it = 0
    while True:
        it += 1
        changed = False
        for b in reversed(list(blocks)):
            d, u = du[b]
            new_out = set()
            for s in edges.get(b, []):
                new_out |= live_in[s]
            new_in = u | (new_out - d)
            if new_in != live_in[b] or new_out != live_out[b]:
                live_in[b], live_out[b] = new_in, new_out
                changed = True
        if not changed or it > 100:
            break
    return live_in, live_out, it


lin, lout, iters = liveness(BLOCKS, EDGES, du)
print(f"\n== 活跃变量（{iters} 轮收敛）==")
for b in BLOCKS:
    print(f"  {b}: LiveIn={sorted(lin[b])}  LiveOut={sorted(lout[b])}")
print("  y 只在 B2 被定义、不在任何 LiveOut 里 -> 可判定为死代码")

print("\n== 到达定义（正向 may 分析）==")
def reaching_defs(blocks, edges, du):
    """每个块的 gen = 本块定义，kill = 其它地方对同一变量的定义。"""
    all_defs = {}
    for b, (d, _) in du.items():
        for v in d: all_defs.setdefault(v, set()).add(b)
    gen = {b: {(b, v) for v in du[b][0]} for b in blocks}
    kill = defaultdict(set)
    for b, (d, _) in du.items():
        for v in d:
            kill[b] |= {(other, v) for other in all_defs[v] if other != b}
    rd_in = {b: set() for b in blocks}
    entry = next(iter(blocks))
    it = 0
    while True:
        it += 1; changed = False
        for b in blocks:
            new_in = set()
            for p, succs in edges.items():
                if b in succs:
                    new_in |= (rd_in[p] - kill[p]) | gen[p]
            if b == entry:
                new_in = set()          # 入口无外来定义
            if new_in != rd_in[b]:
                rd_in[b] = new_in; changed = True
        if not changed or it > 100: break
    return rd_in, it

rd, it2 = reaching_defs(BLOCKS, EDGES, du)
print(f"  {it2} 轮收敛")
for b in BLOCKS:
    print(f"  {b} 入口到达定义: {sorted(rd[b])}")

print("\n== 用活跃信息删除死代码 ==")
def dce(blocks, du, live_out):
    kept = {}
    for b, body in blocks.items():
        live = set(live_out[b])
        new_body = []
        for ins in reversed(body):
            parts = ins.replace("=", " = ").split()
            if "=" in parts:
                eq = parts.index("="); dst = parts[eq-1]
                if dst not in live and not ins.strip().startswith(("return","if","goto")):
                    print(f"    删除 {b}: {ins.strip()}（{dst} 之后不再被读）")
                    continue
                live.discard(dst)
                for tok in parts[eq+1:]:
                    if tok.isidentifier(): live.add(tok)
            new_body.append(ins)
        kept[b] = list(reversed(new_body))
    return kept

kept = dce(BLOCKS, du, lout)
print("  优化后:")
for b, body in kept.items():
    print(f"    {b}: {[i.strip() for i in body]}")

print("\n== 四种经典数据流分析 ==")
print(f"  {'分析':<18}{'方向':<8}{'交汇':<10}{'用途'}")
for row in (("活跃变量", "反向", "并(may)", "寄存器分配/死代码"),
            ("到达定义", "正向", "并(may)", "常量传播"),
            ("可用表达式", "正向", "交(must)", "公共子表达式消除"),
            ("非常忙表达式", "反向", "交(must)", "代码提升")):
    print(f"  {row[0]:<18}{row[1]:<8}{row[2]:<10}{row[3]}")

print("\n== 工程要点 ==")
for line in [
    "  格有限 + 转移函数单调 => 迭代必收敛，最坏 O(n²) 轮",
    "  用位向量 + worklist 算法可把实际迭代次数压到很低",
    "  SSA 形式下 def-use 显式，很多数据流分析可省掉",
    "  过程间分析需要调用图，指针/别名分析是最难的一块",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用 worklist 算法重写活跃分析，统计访问的块次数。
# 2. 实现可用表达式分析，删除块内重复计算。
# 3. 给活跃分析加「跨块 φ 参数」的正确处理（SSA 版）。
# 4. 思考：为什么 may 分析用并、must 分析用交？
