# ===== 第748课：编译原理与代码优化-SSA 与 Phi 函数 =====
# 知识点：
#   - SSA（静态单赋值）：每个变量只被赋值一次，每次使用对应唯一定义
#   - 好处：def-use 链显式，常量传播/死代码消除/寄存器分配都变简单
#   - 分支汇聚时同一变量有多个前驱定义 -> 插入 φ 函数：x3 = φ(x1, x2)
#   - φ 是「并行」语义：同一基本块开头的所有 φ 同时读取前驱值
#   - 支配 dominance：D 支配 N 当且仅当所有到 N 的路径都经过 D
#   - 支配 frontier：正好是需要放 φ 的位置（迭代求不动点）
#   - 本课手写支配树、支配边界与最小 SSA 构造，并解释执行带 φ 的 IR
# 依赖：无（标准库）
from collections import defaultdict


def build_cfg(edges, entry="B0"):
    """edges: {块: [后继块]}；返回前驱表与全部块。"""
    preds = defaultdict(list)
    blocks = set([entry])
    for b, succs in edges.items():
        blocks.add(b)
        for s in succs:
            preds[s].append(b)
            blocks.add(s)
    return preds, sorted(blocks)


def dominators(preds, blocks, entry="B0"):
    """迭代求支配集合：Dom(b) = {b} ∪ ∩ Dom(pred)。"""
    dom = {b: set(blocks) for b in blocks}
    dom[entry] = {entry}
    changed = True
    while changed:
        changed = False
        for b in blocks:
            if b == entry: continue
            ps = preds.get(b, [])
            new = set.intersection(*(dom[p] for p in ps)) if ps else set()
            new = new | {b}
            if new != dom[b]:
                dom[b] = new; changed = True
    return dom


def idom(dom, blocks, entry="B0"):
    """直接支配者：Dom(b)-{b} 里被其余所有支配者支配的那个。"""
    out = {}
    for b in blocks:
        if b == entry: continue
        strict = dom[b] - {b}
        cand = [d for d in strict
                if all(d in dom[x] or x == d for x in strict)]
        out[b] = cand[0] if cand else entry
    return out


def dom_frontier(preds, blocks, idom_map, entry="B0"):
    """DF(b) = { y | b 支配 y 的某个前驱，但 b 不严格支配 y }。"""
    df = {b: set() for b in blocks}
    for b in blocks:
        if len(preds.get(b, [])) >= 2:      # 只有多前驱块才可能是汇聚点
            for p in preds[b]:
                runner = p
                while runner != idom_map.get(b, entry):
                    df[runner].add(b)
                    runner = idom_map.get(runner, entry)
    return df


EDGES = {
    "B0": ["B1"],
    "B1": ["B2", "B3"],
    "B2": ["B4"],
    "B3": ["B4"],
    "B4": ["B5"],
    "B5": ["B1", "B6"],        # 循环回边
    "B6": [],
}
preds, blocks = build_cfg(EDGES)
dom = dominators(preds, blocks)
idm = idom(dom, blocks)
df = dom_frontier(preds, blocks, idm)

print("== 控制流图 ==")
for b in blocks:
    print(f"  {b}: -> {EDGES.get(b, [])}   前驱={preds.get(b, [])}")

print("\n== 支配集合 Dom(b) ==")
for b in blocks:
    print(f"  {b}: {sorted(dom[b])}")

print("\n== 直接支配者 idom（支配树）==")
for b in blocks:
    if b != "B0":
        print(f"  idom({b}) = {idm[b]}")
print("  支配树里父->子:", {p: [c for c, x in idm.items() if x == p]
                        for p in set(idm.values())})

print("\n== 支配边界 DF（该放 φ 的地方）==")
for b in blocks:
    print(f"  DF({b}) = {sorted(df[b])}")


# ---------- SSA 构造：给变量在汇聚点插 φ ----------
def insert_phi(defs, df_map, preds_map, blocks):
    """defs: 变量 -> 定义它的块列表；返回 {块: {变量: [前驱版本...]}}。"""
    phi = defaultdict(dict)
    for var, def_blocks in defs.items():
        work = list(def_blocks)
        processed = set()
        while work:
            b = work.pop()
            for y in df_map[b]:
                if y not in processed and var not in phi[y]:
                    phi[y][var] = [f"{var}@{p}" for p in preds_map.get(y, [])]
                    processed.add(y)
                    if y not in def_blocks:
                        work.append(y)
    return dict(phi)

DEFS = {"x": ["B0", "B2", "B3", "B5"], "i": ["B0", "B5"]}
phis = insert_phi(DEFS, df, preds, blocks)
print("\n== 插入的 φ 函数 ==")
for b in blocks:
    if phis.get(b):
        for var, args in phis[b].items():
            print(f"  {b}: {var}_φ = φ({', '.join(args)})")
    else:
        print(f"  {b}: （无 φ）")

print("\n== SSA 版本的示例程序 ==")
ssa = [
    "B0:  x1 = 1;  i1 = 0;  goto B1",
    "B1:  x2 = φ(x1, x5);  i2 = φ(i1, i3)   # 循环头，DF 要求在此插 φ",
    "     if i2 < 10 goto B2 else goto B3",   # 与上方 CFG 的 B1->B2/B3 一致
    "B2:  x3 = x2 + 1;  goto B4",
    "B3:  x4 = x2 * 2;  goto B4",
    "B4:  x5 = φ(x3, x4);  goto B5",
    "B5:  i3 = i2 + 1;  if i3 < 10 goto B1 else goto B6",
    "B6:  return x5",
]
for line in ssa:
    print("  ", line)

print("\n== φ 的并行语义（易错点）==")
a, b = 1, 2
print(f"  交换前 a={a}, b={b}")
# 错误：顺序赋值会用到已更新的值
a2, b2 = a, b
a2, b2 = b2, a2        # Python 元组赋值是并行的，正确
print(f"  并行交换 (a,b)=(b,a) -> a={a2}, b={b2}")
a3, b3 = 1, 2
a3 = b3; b3 = a3       # 顺序执行出错
print(f"  若逐条顺序执行 a=b; b=a -> a={a3}, b={b3}（错误）")
print("  所以 SSA 里同一块的所有 φ 必须同时读前驱的值")

print("\n== SSA 带来的优化便利 ==")
for line in (
    "  常量传播: 定义唯一，遇到 x=φ(3,3) 直接替成 3",
    "  死代码消除: 没有 use 的定义可安全删（第751课）",
    "  寄存器分配: 干扰图更小，可转为图着色（第753课）",
    "  LLVM IR / JVM / V8 TurboFan 都以 SSA 为核心",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 实现「剪枝 SSA」：只为活跃变量插 φ，减少无用 φ 节点。
# 2. 把第747课的三地址码自动重命名成 SSA 形式（含版本号）。
# 3. 实现 φ 的「消除」：在出边插入 copy，把 SSA 降级回普通 IR。
# 4. 思考：为什么 φ 必须放在基本块开头且并行求值？
