# ===== 第758课：计算几何与空间算法-多边形面积与点包含 =====
# 知识点：
#   - 鞋带公式：面积 A = ½|Σ(x_i·y_{i+1} - x_{i+1}·y_i)|，对任意简单多边形有效
#   - 有向面积符号判方向：逆时针为正；顺时针为负
#   - 点在多边形内：射线法（穿边奇偶）、绕数法 winding number（更稳健，支持带洞）
#   - 边界点单独判定（on_segment），避免射线法在边上出错
#   - 带洞多边形：外环内 且 不在任何内环内
#   - 重心公式：C = (1/6A)·Σ(x_i+x_{i+1})·cross_i，可用于标注/网格划分
# 依赖：无（标准库）
import math

EPS = 1e-9
Point = tuple


def cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])


def signed_area(poly):
    return sum(poly[i][0]*poly[(i+1)%len(poly)][1] -
               poly[(i+1)%len(poly)][0]*poly[i][1]
               for i in range(len(poly))) / 2


def area(poly): return abs(signed_area(poly))


def on_segment(p, a, b):
    return (abs(cross(a,b,p)) < EPS and
            min(a[0],b[0])-EPS <= p[0] <= max(a[0],b[0])+EPS and
            min(a[1],b[1])-EPS <= p[1] <= max(a[1],b[1])+EPS)


def point_in_ring(p, ring):
    """射线法；边界点算内部。"""
    x, y = p
    inside = False
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i+1)%n]
        if on_segment(p, a, b):
            return True
        # 半开区间避免顶点被数两次
        if (a[1] > y) != (b[1] > y):
            x_int = a[0] + (y - a[1])*(b[0]-a[0])/(b[1]-a[1])
            if x < x_int:
                inside = not inside
    return inside


def winding_number(p, ring):
    """绕数法：累计有向跨越次数，带洞/自交更稳健。"""
    wn = 0
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i+1)%n]
        if on_segment(p, a, b):
            return 1
        if a[1] <= p[1]:
            if b[1] > p[1] and cross(a, b, p) > EPS:
                wn += 1
        else:
            if b[1] <= p[1] and cross(a, b, p) < -EPS:
                wn -= 1
    return wn


def point_in_polygon(p, outer, holes=()):
    if not point_in_ring(p, outer):
        return False, "在外环外"
    for h in holes:
        if point_in_ring(p, h):
            return False, "落在洞内"
    return True, "在内"


def centroid(poly):
    """多边形重心（要求非自交，面积非零）。"""
    a2 = 2 * signed_area(poly)
    if abs(a2) < EPS:
        return None
    cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i+1)%n]
        c = x0*y1 - x1*y0
        cx += (x0+x1)*c; cy += (y0+y1)*c
    return (cx/(3*a2), cy/(3*a2))


SQUARE = [(0,0),(4,0),(4,4),(0,4)]
TRI = [(0,0),(4,0),(0,3)]
CONCAVE = [(0,0),(4,0),(4,4),(2,2),(0,4)]

print("== 面积与方向（鞋带公式）==")
for name, poly in (("正方形", SQUARE), ("三角形", TRI), ("凹多边形", CONCAVE),
                   ("顺时针正方形", list(reversed(SQUARE)))):
    s = signed_area(poly)
    print(f"  {name:<14}: 有向面积={s:+.1f} 面积={area(poly):.1f} "
          f"方向={'逆时针' if s>0 else '顺时针'}")

print("\n== 射线法点包含（正方形 0..4）==")
for p in ((2,2),(0,0),(4,2),(5,2),(-1,2),(2,4),(2,0)):
    print(f"  p={str(p):<9} 在内部={point_in_ring(p, SQUARE)}")

print("\n== 凹多边形：射线法仍适用 ==")
for p in ((1,1),(3,3),(2,3),(2,1),(5,5)):
    print(f"  p={str(p):<9} 在内部={point_in_ring(p, CONCAVE)}")

print("\n== 绕数法 winding number ==")
for p in ((2,2),(5,5),(0,0),(3,3)):
    wn = winding_number(p, SQUARE)
    print(f"  p={str(p):<9} 绕数={wn}（非 0 即在内部）")
print("  绕数法对带洞/自交多边形比奇偶法更可控")

print("\n== 带洞多边形 ==")
OUTER = [(0,0),(10,0),(10,10),(0,10)]
HOLE = [(4,4),(6,4),(6,6),(4,6)]
for p in ((1,1),(5,5),(8,8),(4,4)):
    ok, why = point_in_polygon(p, OUTER, [HOLE])
    print(f"  p={str(p):<9} -> {ok} ({why})")

print("\n== 重心 ==")
for name, poly in (("正方形", SQUARE), ("三角形", TRI), ("凹多边形", CONCAVE)):
    c = centroid(poly)
    print(f"  {name:<12}: 重心=({c[0]:.3f}, {c[1]:.3f})")
print("  正方形重心应在 (2,2)，三角形在 (1.333,1)")

print("\n== 自交多边形（鞋带公式给出的是代数面积）==")
BOWTIE = [(0,0),(4,4),(0,4),(4,0)]
print(f"  蝴蝶结多边形有向面积={signed_area(BOWTIE):+.1f}（两半抵消）")
print("  自交图形要先拆分/用绕数定义「内部」，不能直接用面积")

print("\n== 方法对比 ==")
print(f"  {'方法':<14}{'复杂度':<12}{'边界':<10}{'带洞'}")
for row in (("射线法", "O(n)", "需特判", "外环+排除洞"),
            ("绕数法", "O(n)", "需特判", "天然支持"),
            ("三角剖分", "O(log n) 查询", "精确", "需预处理")):
    print(f"  {row[0]:<14}{row[1]:<12}{row[2]:<10}{row[3]}")

print("\n== 应用 ==")
for line in [
    "  GIS：判断地址是否落在行政区/电子围栏内（第66章）",
    "  图形学：多边形填充的扫描转换（第86章）",
    "  CAD/CAM：面积、质心、惯性矩计算",
    "  游戏：点击选中区域、碰撞区域判定",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现三角剖分（耳切法），把多边形拆成三角形并验证面积和。
# 2. 用绕数法处理「自交星形多边形」，对比射线法结果。
# 3. 给点包含加空间索引（网格/R-tree），支持百万级点批量判定。
# 4. 思考：为什么射线法要用「半开区间」避免顶点被重复计数？
