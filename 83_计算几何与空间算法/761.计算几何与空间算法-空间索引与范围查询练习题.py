# ===== 第761课：计算几何与空间算法-空间索引与范围查询 =====
# 知识点：
#   - 点/矩形数据的范围查询：给定查询框，快速找出与之相交的对象
#   - 均匀网格：按 cell 哈希，均摊 O(1) 查询，但分布不均会退化
#   - 四叉树 QuadTree：递归四等分，稀疏区域浅、密集区域深
#   - KD-tree：按维度轮流切分，点数据近邻/范围查询高效
#   - R-tree（概念）：用最小包围矩形 MBR 聚合，适合线面对象与磁盘页
#   - 与第624课网格/geohash、第66章地理查询共享「空间划分」思想
#   - 本课实现网格、四叉树、KD-tree 三种索引并对比查询候选数
# 依赖：无（标准库）
import random

Point = tuple
Rect = tuple        # (xmin, ymin, xmax, ymax)


def in_rect(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


def rects_overlap(a, b):
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


class Grid:
    def __init__(self, cell, bounds):
        self.cell, self.bounds = cell, bounds
        self.buckets = {}
    def key(self, p):
        return (int((p[0]-self.bounds[0])//self.cell),
                int((p[1]-self.bounds[1])//self.cell))
    def insert(self, i, p):
        self.buckets.setdefault(self.key(p), []).append(i)
    def query(self, r):
        out = []
        for cx in range(int((r[0]-self.bounds[0])//self.cell),
                        int((r[2]-self.bounds[0])//self.cell)+1):
            for cy in range(int((r[1]-self.bounds[1])//self.cell),
                            int((r[3]-self.bounds[1])//self.cell)+1):
                out.extend(self.buckets.get((cx,cy), ()))
        return out


class QuadNode:
    def __init__(self, bounds, depth=0):
        self.bounds, self.depth = bounds, depth
        self.points = []
        self.children = None
    def subdivide(self):
        x0,y0,x1,y1 = self.bounds
        xm, ym = (x0+x1)/2, (y0+y1)/2
        self.children = [QuadNode((x0,y0,xm,ym), self.depth+1),
                         QuadNode((xm,y0,x1,ym), self.depth+1),
                         QuadNode((x0,ym,xm,y1), self.depth+1),
                         QuadNode((xm,ym,x1,y1), self.depth+1)]
    def child_for(self, p):
        x0,y0,x1,y1 = self.bounds
        xm, ym = (x0+x1)/2, (y0+y1)/2
        return (0 if p[1] < ym else 2) + (0 if p[0] < xm else 1)
    def insert(self, i, p, cap=8, max_depth=8):
        if self.children:
            self.children[self.child_for(p)].insert(i, p, cap, max_depth)
            return
        self.points.append((i,p))
        if len(self.points) > cap and self.depth < max_depth:
            self.subdivide()
            for j, q in self.points:
                self.children[self.child_for(q)].insert(j, q, cap, max_depth)
            self.points = []
    def query(self, r, out):
        if not rects_overlap(self.bounds, r): return
        if not self.children:
            out.extend(i for i,p in self.points if in_rect(p, r))
            return
        for c in self.children: c.query(r, out)


class KDNode:
    def __init__(self, idx, pts, depth=0):
        self.axis = depth % 2
        if not idx:
            self.point = None; return
        order = sorted(idx, key=lambda i: pts[i][self.axis])
        m = len(order)//2
        self.point = (order[m], pts[order[m]])
        self.left = KDNode(order[:m], pts, depth+1) if order[:m] else None
        self.right = KDNode(order[m+1:], pts, depth+1) if order[m+1:] else None
    def query(self, r, out):
        if self.point is None: return
        i, p = self.point
        if in_rect(p, r): out.append(i)
        a = self.axis
        lo, hi = (r[0],r[2]) if a == 0 else (r[1],r[3])
        if self.left and lo <= p[a]: self.left.query(r, out)
        if self.right and hi >= p[a]: self.right.query(r, out)


print("== 构造数据 ==")
rng = random.Random(11)
N = 3000
points = [(rng.uniform(0,100), rng.uniform(0,100)) for _ in range(N)]
bounds = (0,0,100,100)
queries = [(10,10,25,25),(40,40,60,60),(0,0,100,100),(48,48,52,52),(90,90,100,100)]
print(f"  {N} 个随机点，边界 {bounds}")

print("\n== 三种索引的范围查询（命中数应一致）==")
g = Grid(5, bounds)
for i,p in enumerate(points): g.insert(i,p)
q = QuadNode(bounds)
for i,p in enumerate(points): q.insert(i,p)
kdt = KDNode(list(range(N)), points)

for r in queries:
    brute = [i for i,p in enumerate(points) if in_rect(p,r)]
    hg = set(g.query(r))
    hq = []
    q.query(r, hq); hq = set(hq)
    hk = []
    kdt.query(r, hk); hk = set(hk)
    print(f"  查询框 {r}: 暴力={len(brute)} 网格={len(hg)} 四叉树={len(hq)} KD树={len(hk)} "
          f"一致={hg==hq==hk==set(brute)}")

print("\n== 候选数 vs 实际命中（衡量剪枝效率）==")
for cell in (2, 5, 10, 25):
    g2 = Grid(cell, bounds)
    for i,p in enumerate(points): g2.insert(i,p)
    r = (10,10,25,25)
    cand = g2.query(r)
    hit = [i for i in cand if in_rect(points[i], r)]
    print(f"  cell={cell:>3}: 扫描候选={len(cand):>4} 实际命中={len(hit):>3} "
          f"过滤率={1-len(hit)/max(1,len(cand)):.1%}")
print("  格子太大 -> 候选多；太小 -> 桶数多、跨格查询范围大")

print("\n== 四叉树节点/深度分布 ==")
def tree_stats(node):
    if node.children:
        sizes = [tree_stats(c) for c in node.children]
        return (1+sum(s[0] for s in sizes), 1+max(s[1] for s in sizes),
                sum(s[2] for s in sizes))
    return (1, node.depth, len(node.points))
nodes, depth, leaves = tree_stats(q)
print(f"  节点总数={nodes} 最大深度={depth} 叶节点存点总数={leaves}")

print("\n== 非均匀分布对网格的影响 ==")
clustered = [(rng.gauss(50,3), rng.gauss(50,3)) for _ in range(N)]
gc = Grid(5, bounds)
for i,p in enumerate(clustered): gc.insert(i,p)
max_bucket = max(len(v) for v in gc.buckets.values())
print(f"  聚簇分布下最大桶大小={max_bucket}（均匀分布约 {N/(100/5)**2:.0f}）")
print("  聚簇严重 -> 网格退化成线性扫描，此时四叉树/KD-tree 更稳")

print("\n== 索引选型 ==")
print(f"  {'索引':<12}{'构造':<12}{'查询':<14}{'适合'}")
for row in (("均匀网格", "O(n)", "O(1) 均摊", "分布均匀、实时"),
            ("四叉树", "O(n log n)", "O(log n+k)", "2D、分布不均"),
            ("KD-tree", "O(n log n)", "O(√n+k)", "点数据、近邻"),
            ("R-tree", "O(n log n)", "O(log n+k)", "线面/MBR、磁盘")):
    print(f"  {row[0]:<12}{row[1]:<12}{row[2]:<14}{row[3]}")

print("\n== 应用 ==")
for line in [
    "  地图：框选范围内 POI（第66章）、电子围栏批量判定",
    "  游戏：视锥剔除、碰撞宽相位、粒子邻域搜索",
    "  数据库：PostGIS GiST / SQLite R*Tree / GeoHash 索引",
    "  与第624课空间索引、第759课最近点对互补",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给四叉树增加「删除/移动」与节点合并（少于阈值时回收子节点）。
# 2. 实现 KD-tree 的 k 近邻查询（带剪枝的 best-first）。
# 3. 用 R-tree 的 MBR 思路索引矩形对象，支持「与查询框相交」。
# 4. 思考：为什么聚簇分布会让均匀网格退化，而四叉树不会？
