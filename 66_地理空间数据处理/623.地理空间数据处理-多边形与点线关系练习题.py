# ===== 第623课：地理空间数据处理-多边形与点线关系 =====
# 知识点：
#   - 射线法（Ray Casting）：从点向右发射水平射线，数穿过多边形边的次数，奇数在内
#   - 边界点需单独判定（点在边上算在内或外，取决于业务约定）
#   - 带孔多边形：在外环内且不在任何内环内才算命中
#   - 线长度：把各段距离累加（球面用 Haversine，平面用勾股）
#   - 点到线段最短距离：投影 + 夹紧参数 t 到 [0,1]
#   - 凸包：Andrew monotone chain，O(n log n)，用于圈出点集范围
# 依赖：无（标准库）
import math

EARTH_R = 6371008.8


def on_segment(p, a, b, eps=1e-9):
    cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
    if abs(cross) > eps:
        return False
    return (min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps and
            min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps)


def point_in_ring(p, ring):
    """射线法；边界点算作内部。"""
    x, y = p
    inside = False
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        if on_segment(p, a, b):
            return True
        if (a[1] > y) != (b[1] > y):
            x_int = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x < x_int:
                inside = not inside
    return inside


def point_in_polygon(p, outer, holes=()):
    return point_in_ring(p, outer) and not any(point_in_ring(p, h) for h in holes)


def poly_area(ring):
    """鞋带公式（带符号，逆时针为正）。"""
    return sum(ring[i][0] * ring[i + 1][1] - ring[i + 1][0] * ring[i][1]
               for i in range(len(ring) - 1)) / 2


def haversine(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    h = (math.sin((lat2 - lat1) / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * EARTH_R * math.asin(math.sqrt(h))


def line_length(points, spherical=False):
    fn = haversine if spherical else math.dist
    return sum(fn(points[i], points[i + 1]) for i in range(len(points) - 1))


def point_to_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == dy == 0:
        return math.dist(p, a), a
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    proj = (a[0] + t * dx, a[1] + t * dy)
    return math.dist(p, proj), proj


def convex_hull(points):
    """Andrew monotone chain，返回逆时针凸包顶点。"""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


# ---- 一个带正方形洞的多边形 ----
outer = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
hole = [(4, 4), (6, 4), (6, 6), (4, 6), (4, 4)]

print("== 点在面内（射线法 + 洞）==")
tests = [(5, 5), (1, 1), (10, 5), (11, 5), (-1, 5), (5, 0), (4.5, 4.5)]
for p in tests:
    print(f"  {str(p):<12} 外环={point_in_ring(p, outer)!s:<5} 洞={point_in_ring(p, hole)!s:<5} "
          f"最终={point_in_polygon(p, outer, [hole])}")

print("\n== 面积与方向 ==")
print(f"  外环带符号面积: {poly_area(outer):+.1f}（逆时针为正）")
print(f"  洞带符号面积  : {poly_area(hole):+.1f}")
print(f"  实际区域面积  : {abs(poly_area(outer)) - abs(poly_area(hole)):.1f}")
print(f"  反向外环面积  : {poly_area(list(reversed(outer))):+.1f}")

print("\n== 凹多边形（L 形）==")
L = [(0, 0), (6, 0), (6, 2), (2, 2), (2, 6), (0, 6), (0, 0)]
for p in ((1, 1), (4, 1), (4, 4), (1, 4), (8, 8)):
    print(f"  {str(p):<8} 在内={point_in_ring(p, L)}")

print("\n== 折线长度（平面 vs 球面）==")
route = [(116.4074, 39.9042), (117.2, 39.1), (118.8, 32.1), (121.4737, 31.2304)]
print(f"  平面经纬度距离: {line_length(route):.4f} 度（无实际单位）")
print(f"  球面 Haversine: {line_length(route, spherical=True) / 1000:.1f} km")
print(f"  直线大圆距离  : {haversine(route[0], route[-1]) / 1000:.1f} km")

print("\n== 点到线段最短距离 ==")
a, b = (0, 0), (10, 0)
for p in ((5, 3), (-3, 4), (12, 2), (5, 0)):
    d, proj = point_to_segment(p, a, b)
    print(f"  {str(p):<10} 距离={d:.3f} 投影点=({proj[0]:.1f},{proj[1]:.1f})")

print("\n== 凸包 ==")
cloud = [(0, 0), (1, 1), (2, 0), (2, 2), (0, 2), (1, 0.5), (3, 1), (1, 3), (-1, 1)]
hull = convex_hull(cloud)
print("  原始点数:", len(cloud), "凸包顶点:", hull)
print(f"  凸包面积: {abs(poly_area(hull + [hull[0]])):.1f}")
print("  所有点都在凸包内:", all(point_in_ring(p, hull + [hull[0]]) for p in cloud))

# ===== 练习题 =====
# 1. 实现线段相交判定，并用它统计射线穿边次数（替代 x_int 比较）。
# 2. 给 point_in_polygon 加 include_boundary 参数，控制边界点的归属。
# 3. 用凸包实现「一组 GPS 点的大致覆盖范围」，并计算其球面面积。
# 4. 思考：为什么 GeoJSON 要求外环逆时针、内环顺时针？射线法依赖它吗？
