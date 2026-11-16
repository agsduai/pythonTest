# ===== 第829课：网络流与图匹配-最小割与图像分割 =====
# 知识点：
#   - 最小割：把节点分为 S 侧和 T 侧，使跨割边的容量之和最小
#   - 最大流最小割定理：最大流值 = 最小割容量
#   - 图像分割 Graph Cut：像素为节点，能量函数转为流网络的边
#   - 能量函数：E(L) = Σ 数据项 D_p(L_p) + Σ 平滑项 V(p,q)
#   - 数据项 = 与前景/背景的相似度；平滑项 = 相邻像素标号不同的惩罚
#   - 本课用最小割实现简单的二值图像分割
# 依赖：无（标准库）
from collections import defaultdict, deque
import math
import random


class FlowNetwork:
    def __init__(self):
        self.cap = defaultdict(lambda: defaultdict(float))
        self.nodes = set()

    def add_edge(self, u, v, cap):
        self.cap[u][v] += cap
        self.nodes.add(u); self.nodes.add(v)

    def max_flow(self, s, t):
        residual = defaultdict(lambda: defaultdict(float))
        for u in self.cap:
            for v, c in self.cap[u].items():
                residual[u][v] += c
                residual[v][u] += 0
        flow = 0.0
        while True:
            parent = {s: None}
            q = deque([s])
            found = False
            while q and not found:
                u = q.popleft()
                for v in list(residual[u]):
                    if v not in parent and residual[u][v] > 1e-9:
                        parent[v] = u
                        if v == t: found = True; break
                        q.append(v)
            if not found: break
            # 沿路径更新残余
            path, cur = [], t
            while cur != s:
                path.append(cur); cur = parent[cur]
            path.reverse(); path.insert(0, s)
            bottleneck = min(residual[path[i]][path[i+1]]
                           for i in range(len(path)-1))
            for i in range(len(path)-1):
                residual[path[i]][path[i+1]] -= bottleneck
                residual[path[i+1]][path[i]] += bottleneck
            flow += bottleneck
        return flow, residual


print("== 图像分割建模 ==")
# 4x4 像素图像，每个像素有前景得分 fg_score 和背景得分 bg_score
W, H = 4, 4
rng = random.Random(7)
pixels = [(r, c) for r in range(H) for c in range(W)]
fg_scores = {p: rng.uniform(0, 10) for p in pixels}
bg_scores = {p: rng.uniform(0, 10) for p in pixels}

# 构造流网络：
# 超源 S -> 每个像素（容量 = bg_score，表示分给背景的代价）
# 每个像素 -> 超汇 T（容量 = fg_score，表示分给前景的代价）
# 相邻像素之间：双向边（容量 = λ，平滑项）
SOURCE, SINK = "S", "T"
LAMBDA = 2.0

net = FlowNetwork()
for p in pixels:
    net.add_edge(SOURCE, f"px{p}", bg_scores[p])
    net.add_edge(f"px{p}", SINK, fg_scores[p])

# 相邻像素之间的平滑项边
for r in range(H):
    for c in range(W):
        p = (r, c)
        for dr, dc in ((0,1),(1,0)):
            q = (r+dr, c+dc)
            if q in fg_scores:
                net.add_edge(f"px{p}", f"px{q}", LAMBDA)
                net.add_edge(f"px{q}", f"px{p}", LAMBDA)

print(f"  像素数={len(pixels)} 源=S 汇=T λ(平滑系数)={LAMBDA}")
print(f"  网络节点={len(net.nodes)}")

print("\n== 求最小割（= 最大流）==")
flow, residual = net.max_flow(SOURCE, SINK)
S_side = {SOURCE}
q = deque([SOURCE])
while q:
    u = q.popleft()
    for v in net.cap[u]:
        if v not in S_side and residual.get(u, {}).get(v, 0) > 1e-9:
            S_side.add(v); q.append(v)

print(f"  最大流（最小割容量）= {flow:.3f}")
print(f"  S 侧节点数 = {len(S_side)}")

# 提取分割结果：S 侧 = 前景，T 侧 = 背景
segmentation = {}
for p in pixels:
    node = f"px{p}"
    seg = "前景" if node in S_side else "背景"
    segmentation[p] = seg

print("\n== 分割结果 ==")
print(f"  {'':>6}" + "".join(f"  col{c:<4}" for c in range(W)))
for r in range(H):
    row = f"  row{r:<2}"
    for c in range(W):
        seg = segmentation[(r,c)]
        fg = fg_scores[(r,c)]
        bg = bg_scores[(r,c)]
        symbol = "F" if seg == "前景" else "B"
        row += f"  {symbol}({fg:.0f}/{bg:.0f})"
    print(row)

fg_count = sum(1 for v in segmentation.values() if v == "前景")
print(f"\n  前景像素={fg_count}/{len(pixels)} 背景像素={len(pixels)-fg_count}")

print("\n== λ（平滑系数）对分割的影响 ==")
for lam in (0.5, 2.0, 10.0):
    net_l = FlowNetwork()
    for p in pixels:
        net_l.add_edge(SOURCE, f"px{p}", bg_scores[p])
        net_l.add_edge(f"px{p}", SINK, fg_scores[p])
    for r in range(H):
        for c in range(W):
            p = (r, c)
            for dr, dc in ((0,1),(1,0)):
                q2 = (r+dr, c+dc)
                if q2 in fg_scores:
                    net_l.add_edge(f"px{p}", f"px{q2}", lam)
                    net_l.add_edge(f"px{q2}", f"px{p}", lam)
    f_l, r_l = net_l.max_flow(SOURCE, SINK)
    S_side_l = {SOURCE}
    q_l = deque([SOURCE])
    while q_l:
        u = q_l.popleft()
        for v in net_l.cap[u]:
            if v not in S_side_l and r_l.get(u, {}).get(v, 0) > 1e-9:
                S_side_l.add(v); q_l.append(v)
    fg_c = sum(1 for p in pixels if f"px{p}" in S_side_l)
    print(f"  λ={lam:>5}: 前景像素={fg_c}/{len(pixels)}")

print("  λ 越大，相邻像素越倾向于标同一个标签（分割更平滑）")
print("  λ=0 时每个像素独立按数据项分类（可能有噪声）")

print("\n== Graph Cut 与能量函数 ==")
for line in (
    "  E(L) = Σ D_p(L_p) + λ·Σ V(L_p, L_q)   [逐像素标号]",
    "  D_p(前景) = bg_score   D_p(背景) = fg_score  （交叉编码）",
    "  V(前景,背景) = λ        V(相同) = 0           （平滑项）",
    "  最小割把能量最小化问题转化为最大流问题，多项式时间求解",
    "  Graph Cut 是图像分割的经典方法（Boykov-Jolly 2001）",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  医学图像：器官/肿瘤分割",
    "  照片编辑：前景提取（Photoshop 的快速选择）",
    "  遥感：土地利用分类",
    "  立体匹配：像素视差估计",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "  像素数很大时（百万级）需要 maxflow 库（BK 算法）加速",
    "  多标签分割（>2 类）用 α-expansion 迭代最小割",
    "  λ 需按图像特征自适应（噪声大 → λ 大）",
    "  深度学习方案（U-Net）在精度上已超越 Graph Cut",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现带「用户标记的种子点」的交互式分割：种子点强制分给指定类。
# 2. 把图像扩展到 8×8，测试性能（40+ 像素，更多边）。
# 3. 实现 α-expansion 多标签分割（3 种标签：前景/背景/边界）。
# 4. 思考：为什么「数据项」要交叉编码（前景代价 = 背景得分）？
