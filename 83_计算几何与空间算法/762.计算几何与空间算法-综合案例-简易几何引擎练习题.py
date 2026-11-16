# ===== 第762课：计算几何与空间算法-综合案例-简易几何引擎 =====
# 知识点：
#   - 综合串起本章：向量/叉积 -> 凸包 -> 线段相交 -> 多边形 -> 空间索引 -> 查询
#   - 引擎分层：几何原语（点/线/面）、空间索引（网格）、关系谓词（contains/intersects/distance）
#   - 支持：批量点注册、矩形范围查询、点在多边形、线段与多边形求交、最近点
#   - 所有结果用暴力法交叉验证，确保索引剪枝没有漏解
#   - 应用：地图围栏、CAD 选区、游戏碰撞宽相位、空间数据分析
#   - 全部标准库 + 可注入 rng，纯内存、离线可运行
# 依赖：无（标准库）
import math
import random

EPS = 1e-9
Point = tuple


def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
def sub(a,b): return (a[0]-b[0], a[1]-b[1])
def add(a,b): return (a[0]+b[0], a[1]+b[1])
def mul(a,k): return (a[0]*k, a[1]*k)
def dot(a,b): return a[0]*b[0]+a[1]*b[1]
def cross2(a,b): return a[0]*b[1]-a[1]*b[0]
def orient(a,b,c):
    v = cross(a,b,c)
    return 0 if abs(v)<EPS else (1 if v>0 else -1)
def dist(a,b): return math.dist(a,b)
def sign(v): return 0 if abs(v)<EPS else (1 if v>0 else -1)


def on_segment(p,a,b):
    return (orient(a,b,p)==0 and
            min(a[0],b[0])-EPS <= p[0] <= max(a[0],b[0])+EPS and
            min(a[1],b[1])-EPS <= p[1] <= max(a[1],b[1])+EPS)


def seg_intersect(a,b,c,d):
    o1,o2,o3,o4 = orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
    if o1==0 and on_segment(c,a,b): return True
    if o2==0 and on_segment(d,a,b): return True
    if o3==0 and on_segment(a,c,d): return True
    if o4==0 and on_segment(b,c,d): return True
    return o1!=o2 and o3!=o4


def seg_intersection_point(a,b,c,d):
    r,s = sub(b,a), sub(d,c)
    den = cross2(r,s)
    if abs(den)<EPS: return None
    t = cross2(sub(c,a), s)/den
    return add(a, mul(r,t))


def point_in_poly(p, poly):
    x,y = p; inside=False; n=len(poly)
    for i in range(n):
        a,b = poly[i], poly[(i+1)%n]
        if on_segment(p,a,b): return True
        if (a[1]>y)!=(b[1]>y):
            xi = a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])
            if x < xi: inside = not inside
    return inside


def polygon_area(poly):
    return abs(sum(poly[i][0]*poly[(i+1)%len(poly)][1] -
                   poly[(i+1)%len(poly)][0]*poly[i][1]
                   for i in range(len(poly)))/2)


def convex_hull(pts):
    pts = sorted(set(pts))
    if len(pts)<=2: return pts
    def build(seq):
        st=[]
        for p in seq:
            while len(st)>=2 and cross(st[-2],st[-1],p)<=EPS: st.pop()
            st.append(p)
        return st
    return build(pts)[:-1]+build(reversed(pts))[:-1]


class GeometryEngine:
    """点集 + 网格索引 + 一组关系谓词。"""
    def __init__(self, cell=10, bounds=(0,0,100,100)):
        self.points = []
        self.cell, self.bounds = cell, bounds
        self.grid = {}
    def _key(self,p):
        return (int((p[0]-self.bounds[0])//self.cell),
                int((p[1]-self.bounds[1])//self.cell))
    def add_point(self, name, p):
        idx = len(self.points)
        self.points.append((name,p))
        self.grid.setdefault(self._key(p), []).append(idx)
        return idx
    def in_rect(self, r):
        """矩形范围查询：网格剪枝后再精确判定。"""
        cand = []
        for cx in range(int((r[0]-self.bounds[0])//self.cell),
                        int((r[2]-self.bounds[0])//self.cell)+1):
            for cy in range(int((r[1]-self.bounds[1])//self.cell),
                            int((r[3]-self.bounds[1])//self.cell)+1):
                cand.extend(self.grid.get((cx,cy),()))
        return [(self.points[i][0], self.points[i][1]) for i in cand
                if r[0]<=self.points[i][1][0]<=r[2] and r[1]<=self.points[i][1][1]<=r[3]]
    def in_polygon(self, poly):
        return [(n,p) for n,p in self.points if point_in_poly(p, poly)]
    def nearest(self, q):
        best, name = float("inf"), None
        for n,p in self.points:
            d = dist(q,p)
            if d < best: best, name = d, n
        return name, best
    def segment_crossings(self, a, b, edges):
        out=[]
        for i,(c,d) in enumerate(edges):
            if seg_intersect(a,b,c,d):
                p = seg_intersection_point(a,b,c,d)
                out.append((i,p))
        return out
    def stats(self):
        return {"点数": len(self.points), "网格桶数": len(self.grid),
                "最大桶": max((len(v) for v in self.grid.values()), default=0)}


print("== 构建几何引擎 ==")
eng = GeometryEngine(cell=10, bounds=(0,0,100,100))
rng = random.Random(7)
for i in range(500):
    eng.add_point(f"P{i}", (rng.uniform(0,100), rng.uniform(0,100)))
# 几个固定地标
eng.add_point("CENTER", (50,50))
eng.add_point("ORIGIN", (5,5))
print("  ", eng.stats())

print("\n== 矩形范围查询（索引 vs 暴力一致性）==")
for r in ((0,0,20,20),(40,40,60,60),(0,0,100,100),(48,48,52,52)):
    got = eng.in_rect(r)
    brute = [(n,p) for n,p in eng.points
             if r[0]<=p[0]<=r[2] and r[1]<=p[1]<=r[3]]
    print(f"  框 {r}: 索引命中={len(got)} 暴力={len(brute)} 一致={set(got)==set(brute)}")

print("\n== 多边形围栏判定 ==")
FENCE = [(20,20),(80,20),(80,80),(20,80)]
inside = eng.in_polygon(FENCE)
brute = [(n,p) for n,p in eng.points if point_in_poly(p,FENCE)]
print(f"  正方形围栏面积={polygon_area(FENCE):.0f}，内部点={len(inside)}，"
      f"与暴力一致={set(inside)==set(brute)}")
print("  CENTER 在围栏内:", any(n=="CENTER" for n,_ in inside))
print("  ORIGIN 在围栏内:", any(n=="ORIGIN" for n,_ in inside))

print("\n== 最近点查询 ==")
for q in ((50,50),(0,0),(100,100)):
    name, d = eng.nearest(q)
    print(f"  q={q}: 最近={name} 距离={d:.3f}")

print("\n== 线段与多边形边界求交 ==")
edges = list(zip(FENCE, FENCE[1:]+FENCE[:1]))
for a,b in (((0,50),(100,50)), ((10,10),(30,30)), ((50,50),(50,90))):
    hits = eng.segment_crossings(a,b,edges)
    print(f"  线段 {a}->{b}: 与围栏边界交点 {[(i, (round(p[0],1),round(p[1],1)) if p else None) for i,p in hits]}")

print("\n== 点集凸包（形状概览）==")
cloud = [p for _,p in eng.points]
hull = convex_hull(cloud)
print(f"  {len(cloud)} 点 -> 凸包 {len(hull)} 个顶点，"
      f"面积={polygon_area(hull):.0f}（外接形状）")
print("  凸包顶点（前 6）:", hull[:6])

print("\n== 引擎分层回顾 ==")
for line in [
    "  原语层  : 叉积/orient、点线距离、线段相交（第755/757课）",
    "  形状层  : 凸包、多边形面积与点包含（第756/758课）",
    "  索引层  : 均匀网格加速范围查询（第761课）",
    "  关系层  : in_rect / in_polygon / nearest / segment_crossings",
    "  验证层  : 每个索引查询都与暴力结果交叉校验（防剪枝漏解）",
    "  扩展点  : KD-tree、Delaunay、最近点对（第759/760/761课）",
]:
    print("  -", line)

print("\n== 与真实几何库的差距 ==")
for line in [
    "  只支持 2D 点/线段/简单多边形，无圆弧、带洞复杂面、拓扑操作",
    "  无精确几何谓词（浮点 incircle 可能误判）",
    "  无缓冲区/并交差布尔运算（Shapely/GEOS 的核心能力）",
    "  目标是串起本章算法并提供可验证的查询接口",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加「多边形缓冲/偏移」的简化实现（按边法向平移）。
# 2. 用四叉树替换均匀网格，对比聚簇分布下的查询候选数。
# 3. 实现两个多边形的交/并判定（基于边求交与点包含）。
# 4. 思考：为什么每个索引查询都必须与暴力法做一致性校验？
