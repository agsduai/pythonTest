# ===== 第760课：计算几何与空间算法-Delaunay 三角剖分与 Voronoi =====
# 知识点：
#   - Delaunay 三角剖分：任意三角形外接圆内不含其他点（空圆特性）
#   - 空圆特性让三角形尽量「饱满」，避免狭长三角形，网格质量好
#   - Bowyer-Watson：逐点插入，删掉外接圆含新点的「坏三角形」，重连空腔边界
#   - Voronoi 图：平面按「离哪个站点最近」划分；与 Delaunay 互为对偶
#   - Voronoi 顶点 = Delaunay 三角形外心；Voronoi 边 = Delaunay 边的垂直平分线
#   - 应用：最近设施查询、有限元网格、地形 TIN、插值（自然邻域）
#   - 本课用标准库实现 Bowyer-Watson 与对偶边提取，教学用小规模点集
# 依赖：无（标准库）
import math
import random

EPS = 1e-9


def circumcircle(a, b, c):
    """返回 (圆心, 半径²)；共线返回 None。"""
    d = 2*(a[0]*(b[1]-c[1]) + b[0]*(c[1]-a[1]) + c[0]*(a[1]-b[1]))
    if abs(d) < EPS:
        return None
    a2, b2, c2 = a[0]**2+a[1]**2, b[0]**2+b[1]**2, c[0]**2+c[1]**2
    ux = (a2*(b[1]-c[1]) + b2*(c[1]-a[1]) + c2*(a[1]-b[1])) / d
    uy = (a2*(c[0]-b[0]) + b2*(a[0]-c[0]) + c2*(b[0]-a[0])) / d
    center = (ux, uy)
    return center, (a[0]-ux)**2 + (a[1]-uy)**2


def in_circumcircle(p, tri):
    cc = circumcircle(*tri)
    if cc is None: return False
    (cx, cy), r2 = cc
    return (p[0]-cx)**2 + (p[1]-cy)**2 <= r2 + EPS


def delaunay(points):
    """Bowyer-Watson：先建超级三角形，逐点插入，最后剔除含超级顶点的三角形。"""
    pts = list(points)
    if len(pts) < 3:
        return []
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    dx, dy = max(xs)-min(xs), max(ys)-min(ys)
    m = max(dx, dy, 1.0)
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    super_v = [(cx-20*m, cy-m), (cx, cy+20*m), (cx+20*m, cy-m)]
    all_pts = pts + super_v
    s0, s1, s2 = len(pts), len(pts)+1, len(pts)+2
    triangles = [tuple(sorted((s0, s1, s2)))]

    for i, p in enumerate(pts):
        bad = [t for t in triangles if in_circumcircle(p, tuple(all_pts[k] for k in t))]
        # 找空腔边界：只出现一次的边
        edge_count = {}
        for t in bad:
            for e in ((t[0],t[1]),(t[1],t[2]),(t[0],t[2])):
                key = tuple(sorted(e))
                edge_count[key] = edge_count.get(key, 0) + 1
        boundary = [e for e, c in edge_count.items() if c == 1]
        triangles = [t for t in triangles if t not in bad]
        for a, b in boundary:
            triangles.append(tuple(sorted((a, b, i))))
    # 剔除含超级顶点的三角形
    return [t for t in triangles if all(k < len(pts) for k in t)]


def voronoi_edges(tris, pts):
    """Delaunay 对偶：每条内部边的两个相邻三角形外心连成 Voronoi 边。"""
    edge_tris = {}
    for t in tris:
        cc = circumcircle(*(pts[k] for k in t))
        if cc is None: continue
        center = cc[0]
        for e in ((t[0],t[1]),(t[1],t[2]),(t[0],t[2])):
            edge_tris.setdefault(tuple(sorted(e)), []).append(center)
    return [(a, b) for e, cs in edge_tris.items() if len(cs) == 2
            for a, b in [tuple(cs)]]


def triangle_quality(t, pts):
    """质量度量：越接近等边越接近 1。"""
    a, b, c = (pts[k] for k in t)
    sides = [math.dist(a,b), math.dist(b,c), math.dist(c,a)]
    s = sum(sides)/2
    area = math.sqrt(max(0, s*(s-sides[0])*(s-sides[1])*(s-sides[2])))
    r = sides[0]*sides[1]*sides[2] / (4*area) if area > EPS else float("inf")
    r_in = area / s if s > EPS else 0
    return r_in / r if r else 0


print("== 简单点集的 Delaunay 三角剖分 ==")
pts = [(0,0),(1,0),(0,1),(1,1),(0.5,0.5)]
tris = delaunay(pts)
print(f"  输入 {len(pts)} 点，得到 {len(tris)} 个三角形")
for t in tris:
    print("   ", t, [pts[k] for k in t], f"质量={triangle_quality(t,pts):.3f}")

print("\n== 空圆特性校验 ==")
ok = True
for t in tris:
    cc = circumcircle(*(pts[k] for k in t))
    if cc is None: continue
    (cx,cy), r2 = cc
    for i, p in enumerate(pts):
        if i in t: continue
        if (p[0]-cx)**2 + (p[1]-cy)**2 < r2 - EPS:
            ok = False
            print(f"  违反: 三角形 {t} 的外接圆含点 {i}")
print(f"  所有三角形满足空圆特性: {ok}")

print("\n== Voronoi 对偶边 ==")
edges = voronoi_edges(tris, pts)
print(f"  {len(edges)} 条 Voronoi 边（连接相邻三角形外心）")
for a, b in edges[:5]:
    print(f"    ({a[0]:.2f},{a[1]:.2f}) -- ({b[0]:.2f},{b[1]:.2f})")

print("\n== 随机点集：规模与三角形数 ==")
for n in (10, 50, 200, 500):
    r = random.Random(n)
    cloud = [(r.uniform(0,100), r.uniform(0,100)) for _ in range(n)]
    tr = delaunay(cloud)
    qs = [triangle_quality(t, cloud) for t in tr]
    print(f"  n={n:>4}: 三角形={len(tr):>4}（理论约 2n）, "
          f"平均质量={sum(qs)/len(qs):.3f} 最差={min(qs):.3f}")

print("\n== Delaunay vs 任意剖分的质量 ==")
r = random.Random(5)
cloud = [(r.uniform(0,10), r.uniform(0,10)) for _ in range(30)]
# 一种朴素剖分：固定一个点扇形连接（仅作对照）
fan = [(0, i, i+1) for i in range(1, len(cloud)-1)]
fd = [triangle_quality(t, cloud) for t in fan if triangle_quality(t,cloud) > 0]
dd = [triangle_quality(t, cloud) for t in delaunay(cloud)]
print(f"  扇形剖分平均质量={sum(fd)/len(fd):.3f}, Delaunay={sum(dd)/len(dd):.3f}")
print("  Delaunay 最大化最小角，显著减少狭长三角形")

print("\n== 退化情况 ==")
for name, cloud in (("共线 3 点", [(0,0),(1,0),(2,0)]),
                    ("重复点", [(0,0),(1,1),(0,0),(2,2),(1,0)]),
                    ("正方形 4 点", [(0,0),(1,0),(1,1),(0,1)])):
    tr = delaunay(cloud)
    print(f"  {name}: {len(tr)} 个三角形")
print("  四点共圆时剖分不唯一，任一对角线都满足空圆特性")

print("\n== 应用 ==")
for line in [
    "  有限元/地形 TIN：三角形质量直接影响数值稳定性",
    "  最近邻：Voronoi 单元里离哪个站点最近一目了然",
    "  自然邻域插值、空间聚类、无线基站覆盖划分",
    "  与第66章地理空间、第759课最近点对串联",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "  超级三角形要足够大，否则边界点被误判在圆外",
    "  浮点 incircle 判定用自适应精度（Shewchuk）才稳",
    "  生产用 scipy.spatial.Delaunay / CGAL / Triangle",
    "  三维 Delaunay 四面体化复杂度与退化处理都更难",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Voronoi 单元裁剪（把无限边裁到边界框内）。
# 2. 用 Delaunay 做「自然邻域插值」，估计未知点的值。
# 3. 检测并处理四点共圆时的剖分不唯一性。
# 4. 思考：为什么空圆特性等价于「最大化最小角」？
