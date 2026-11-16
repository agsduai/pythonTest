# ===== 第749课：编译原理与代码优化-控制流图与基本块 =====
# 知识点：
#   - 基本块 basic block：单入口单出口的最长连续指令序列，块内无跳转
#   - leader 识别：第一条指令、跳转目标、跳转后一条指令
#   - CFG：节点=基本块，边=控制转移；回边表示循环，自然循环由回边+支配关系确定
#   - 支配树 / 支配边界（第748课）都建立在 CFG 上
#   - 循环优化：不变量外提、强度削弱、循环展开都先要识别循环
#   - 本课从线性三地址码切分基本块、构造 CFG、用 DFS 找回边与自然循环
# 依赖：无（标准库）
from collections import defaultdict


def find_leaders(code):
    """leader = 第一条 / 跳转目标 / 跳转或 return 之后的一条。"""
    leaders = {0}
    for i, ins in enumerate(code):
        op = ins.split()[0]
        if op in ("goto", "if_false", "if_true", "return"):
            if i + 1 < len(code):
                leaders.add(i + 1)
        if ins.rstrip().endswith(":"):       # 标签行本身是跳转目标
            leaders.add(i)
    return sorted(leaders)


def build_blocks(code):
    leaders = find_leaders(code)
    blocks = []
    for k, start in enumerate(leaders):
        end = leaders[k + 1] if k + 1 < len(leaders) else len(code)
        body = code[start:end]
        label = body[0].rstrip(":") if body[0].rstrip().endswith(":") else f"B{len(blocks)}"
        blocks.append({"name": label, "start": start, "body": body})
    return blocks


def build_cfg(blocks, code):
    """根据每个块最后一条指令连边。"""
    label_to_block = {}
    for i, b in enumerate(blocks):
        label_to_block[b["name"]] = i
        label_to_block[f"B{i}"] = i
    edges = defaultdict(list)
    for i, b in enumerate(blocks):
        last = b["body"][-1]
        op = last.split()[0]
        if op == "goto":
            tgt = last.split()[-1].rstrip(":")
            edges[i].append(label_to_block.get(tgt, -1))
        elif op in ("if_false", "if_true"):
            tgt = last.split()[-1].rstrip(":")
            edges[i].append(label_to_block.get(tgt, -1))
            if i + 1 < len(blocks):
                edges[i].append(i + 1)
        elif op == "return":
            pass
        elif i + 1 < len(blocks):
            edges[i].append(i + 1)
    return {i: [x for x in v if x >= 0] for i, v in edges.items()}


CODE = [
    "L0:", "  i = 0", "  s = 0",
    "L1:", "  if_false i < 10 goto L3", "  t = i * 2", "  s = s + t",
    "  i = i + 1", "  goto L1",
    "L3:", "  return s",
]

print("== 线性 IR ==")
for i, ins in enumerate(CODE):
    print(f"  {i:>2}: {ins}")

leaders = find_leaders(CODE)
print("\n== leaders ==")
print("  ", leaders)
for i in leaders:
    print(f"    {i}: {CODE[i]}")

blocks = build_blocks(CODE)
print("\n== 基本块 ==")
for i, b in enumerate(blocks):
    print(f"  B{i} ({b['name']}): 行 {b['start']}..{b['start']+len(b['body'])-1}")
    for ins in b["body"]:
        print("     ", ins)

edges = build_cfg(blocks, CODE)
print("\n== CFG 边 ==")
for i, succs in edges.items():
    print(f"  B{i} -> {[f'B{s}' for s in succs]}")

print("\n== 回边与自然循环（DFS）==")
def find_back_edges(edges, entry=0):
    color, stack, back = {}, [], []
    def dfs(u):
        color[u] = 1
        stack.append(u)
        for v in edges.get(u, []):
            if color.get(v, 0) == 1:              # 指向栈上节点 = 回边
                back.append((u, v))
            elif color.get(v, 0) == 0:
                dfs(v)
        stack.pop(); color[u] = 2
    dfs(entry)
    return back

back = find_back_edges(edges)
print("  回边:", [(f"B{u}", f"B{v}") for u, v in back])
for tail, head in back:
    # 自然循环 = 从 tail 沿前驱反向可达、且不越过 head 的节点集合
    preds = defaultdict(list)
    for u, succs in edges.items():
        for v in succs: preds[v].append(u)
    loop, q = {head, tail}, [tail]
    while q:
        x = q.pop()
        for p in preds.get(x, []):
            if p not in loop:
                loop.add(p); q.append(p)
    print(f"  自然循环(回边 B{tail}->B{head}): {sorted(f'B{x}' for x in loop)}")

print("\n== 循环优化机会 ==")
for line in (
    "  循环不变量外提: i*2 里的 2 是常量，但 i 变；若有 n*2 可提到循环外",
    "  强度削弱: i*2 可改成累加 +2（第752课）",
    "  归纳变量: i 与 t=i*2 同步变化，可只保留一个",
    "  循环展开: 减少分支次数，代价是代码体积",
):
    print(" ", line)

print("\n== 基本块内优化 vs 全局优化 ==")
for line in (
    "  局部(块内): 常量折叠、公共子表达式、死代码，简单且安全",
    "  全局(CFG): 需要数据流分析（第750课）跨块传播信息",
    "  循环级: 依赖支配/回边信息，收益通常最大",
    "  过程间: 跨函数内联与逃逸分析，成本最高",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  基本块边界处寄存器可能要 spill（跨块活跃变量）",
    "  不可达块要先删掉，否则数据流分析会传播无用信息",
    "  异常/try 会引入额外的 CFG 边，别漏掉",
    "  LLVM 的 BasicBlock/Pass Manager 就是这套抽象",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「删除不可达基本块」并重编号 CFG。
# 2. 用支配关系精确计算自然循环，替代本例的反向可达近似。
# 3. 识别循环不变量并把它们外提到 preheader。
# 4. 思考：为什么 jump 之后的那条指令一定是新基本块的 leader？
