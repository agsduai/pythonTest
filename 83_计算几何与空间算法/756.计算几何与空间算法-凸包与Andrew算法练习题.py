# ===== 第756课：计算几何与空间算法-凸包与 Andrew 算法 =====
# 知识点：
#   - 凸包 convex hull：包住所有点的最小凸多边形，顶点来自原点集
#   - Andrew monotone chain：按 (x,y) 排序，分别构造下凸壳与上凸壳再拼接，O(n log n)
#   - 构造时用栈：新点若让栈顶「非左转」则弹出，直到恢复凸性
#   - 与 Graham 扫描对比：Andrew 不需极角排序、实现更简单、数值更稳
#   - 共线点处理：保留端点（严格凸）或保留全部（看 pop 条件用 <=0 还是 <0）
#   - 应用：碰撞检测包围盒、形状近似、最远点对、计算几何预处理
# 依赖：无（标准库）
import math
import random

Point = tuple
EPS = 1e-9


def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])


def convex_hull(points, keep_collinear=False):
    """Andrew monotone chain，返回逆时针凸包顶点（不含重复的起点）。"""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    def build(seq):
        stack = []
        for p in seq:
            while len(stack) >= 2:
                c = cross(stack[-2], stack[-1], p)
                if (c < -EPS) if keep_collinear else (c <= EPS):
                    stack.pop()
                else:
                    break
            stack.append(p)
        return stack
    lower = build(pts)
    upper = build(reversed(pts))
    return lower[:-1] + upper[:-1]


def polygon_area(poly):
    """鞋带公式，逆时针为正。"""
    return sum(poly[i][0]*poly[(i+1)%len(poly)][1] -
               poly[(i+1)%len(poly)][0]*poly[i][1]
               for i in range(len(poly))) / 2


def point_in_convex(p, hull):
    """凸多边形内判定：所有边都在同侧（O(n)），要求 hull 逆时针。"""
    for i in range(len(hull)):
        if cross(hull[i], hull[(i+1)%len(hull)], p) < -EPS:
            return False
    return True


def rotating_calipers_diameter(hull):
    """旋转卡壳求凸包直径（最远点对距离），O(n)。"""
    n = len(hull)
    if n < 2: return 0.0, None
    j, best = 1, 0.0
    pair = None
    for i in range(n):
        ni, nj = (i+1) % n, (j+1) % n
        while abs(cross(hull[i], hull[ni], hull[nj])) > abs(cross(hull[i], hull[ni], hull[j])):
            j = nj; nj = (j+1) % n
            if j == i: break
        d = math.dist(hull[i], hull[j])
        if d > best:
            best, pair = d, (hull[i], hull[j])
    return best, pair


print("== 简单点集凸包 ==")
pts = [(0,0),(1,1),(2,0),(2,2),(0,2),(1,0.5),(1,1.5)]
h = convex_hull(pts)
print("  原点:", pts)
print("  凸包:", h)
print(f"  凸包顶点数={len(h)} 面积={polygon_area(h):.3f}")
print("  是否逆时针:", polygon_area(h) > 0)

print("\n== 共线点处理：严格凸 vs 保留全部 ==")
collinear_pts = [(0,0),(1,0),(2,0),(3,0),(2,2),(1,2)]
print("  严格凸(弹共线):", convex_hull(collinear_pts, keep_collinear=False))
print("  保留共线点    :", convex_hull(collinear_pts, keep_collinear=True))

print("\n== 凸包内点判定 ==")
for p in ((1,1), (0.1,0.1), (3,3), (2,1), (-1,1)):
    print(f"  p={str(p):<10} in_convex={point_in_convex(p, h)}")

print("\n== 随机点集：规模与耗时趋势 ==")
for n in (10, 100, 1000, 5000):
    r = random.Random(n)
    cloud = [(r.uniform(0, 100), r.uniform(0, 100)) for _ in range(n)]
    hull = convex_hull(cloud)
    print(f"  n={n:>5}: 凸包顶点={len(hull):>3} 面积={polygon_area(hull):>9.1f} "
          f"（凸包远小于原点集，O(n log n) 主要花在排序）")

print("\n== 旋转卡壳求直径 ==")
r = random.Random(3)
cloud = [(r.uniform(0,50), r.uniform(0,50)) for _ in range(60)]
hull = convex_hull(cloud)
d, pair = rotating_calipers_diameter(hull)
# 暴力校验
brute = max(math.dist(a,b) for i,a in enumerate(cloud) for b in cloud[i+1:])
print(f"  旋转卡壳直径={d:.3f} 点对={pair}")
print(f"  暴力 O(n²) 直径={brute:.3f} 一致={abs(d-brute) < 1e-6}")

print("\n== Andrew 算法栈过程（小例子）==")
demo = [(0,0),(1,2),(2,1),(3,3),(4,0),(2,0.5)]
stack = []
for p in sorted(demo):
    while len(stack) >= 2 and cross(stack[-2], stack[-1], p) <= EPS:
        print(f"    弹出 {stack[-1]}（加入 {p} 会右转/共线）")
        stack.pop()
    stack.append(p)
    print(f"    压入 {p}: 下凸壳={stack}")
print("  最终下凸壳:", stack)

print("\n== 复杂度对比 ==")
for line in (
    "  暴力枚举 O(n³)：枚举所有点对判断是否所有点在同侧",
    "  Jarvis 步进 O(nh)：h 为凸包顶点数，h 小时快",
    "  Graham / Andrew O(n log n)：排序主导，通用首选",
    "  三维凸包 O(n log n) 但实现复杂（QuickHull）",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  碰撞检测：先用凸包做粗筛，再做精确相交",
    "  最远点对必定在凸包上，旋转卡壳 O(n) 求出",
    "  图像轮廓、点云边界、地理围栏简化",
    "  与第66章 GeoJSON 多边形、第78章优化结合",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Jarvis 步进（礼品包装）算法，与 Andrew 结果对比。
# 2. 用凸包做「点集是否在一条直线同侧」的快速判定。
# 3. 实现动态凸包：逐点插入并维护凸壳。
# 4. 思考：为什么 pop 条件用 <=0 还是 <0 会决定共线点是否保留？
