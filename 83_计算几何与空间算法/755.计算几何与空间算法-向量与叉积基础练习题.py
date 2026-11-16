# ===== 第755课：计算几何与空间算法-向量与叉积基础 =====
# 知识点：
#   - 点用 (x,y) 元组，向量 = 两点相减；加减/数乘/点积/叉积是基本运算
#   - 点积 a·b = |a||b|cosθ，判夹角/投影；叉积 a×b = ax*by - ay*bx，判转向
#   - 叉积符号：>0 逆时针左转、<0 右转、=0 共线；是几乎所有几何算法的基石
#   - 浮点比较要用 eps 容差，别用 ==；eps 取 1e-9 量级
#   - 常见判定：点在直线哪侧、三点转向、线段上、两向量夹角、点到直线距离
#   - 与第66章地理空间不同：这里用平面欧氏几何，不考虑球面/投影
# 依赖：无（标准库）
import math

EPS = 1e-9
Point = tuple


def sub(a, b): return (a[0]-b[0], a[1]-b[1])
def add(a, b): return (a[0]+b[0], a[1]+b[1])
def mul(a, k): return (a[0]*k, a[1]*k)
def dot(a, b): return a[0]*b[0] + a[1]*b[1]
def cross(a, b): return a[0]*b[1] - a[1]*b[0]
def norm2(a): return dot(a, a)
def length(a): return math.sqrt(norm2(a))
def sign(v): return 0 if abs(v) < EPS else (1 if v > 0 else -1)


def orient(a, b, c):
    """三点转向：>0 逆时针(c 在 ab 左侧)，<0 顺时针，0 共线。"""
    return sign(cross(sub(b, a), sub(c, a)))


def on_segment(p, a, b):
    """p 是否在线段 ab 上（含端点），要求先共线。"""
    return (orient(a, b, p) == 0 and
            min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS and
            min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS)


def point_line_dist(p, a, b):
    """点 p 到直线 ab 的距离 = |cross(b-a, p-a)| / |b-a|。"""
    ab = sub(b, a)
    return abs(cross(ab, sub(p, a))) / length(ab)


def angle(a, b):
    """两向量夹角（弧度）。"""
    cosv = dot(a, b) / (length(a) * length(b))
    return math.acos(max(-1.0, min(1.0, cosv)))


print("== 基础运算 ==")
a, b = (3, 4), (1, 2)
print(f"  a={a} b={b}")
print(f"  a+b={add(a,b)}  a-b={sub(a,b)}  2a={mul(a,2)}")
print(f"  点积={dot(a,b)}  叉积={cross(a,b)}  |a|={length(a):.4f}")

print("\n== 三点转向 orient(a,b,c) ==")
O, X, Y = (0,0), (1,0), (0,1)
for name, p in (("左侧(逆时针)", (1,1)), ("右侧(顺时针)", (1,-1)),
                ("共线", (2,0)), ("反向共线", (-1,0))):
    o = orient(O, X, p)
    label = {1:"逆时针/左", -1:"顺时针/右", 0:"共线"}[o]
    print(f"  c={str(p):<10} orient={o:>2} -> {label}")

print("\n== 点在直线哪侧 ==")
line_a, line_b = (0,0), (4,4)
for p in ((1,2), (3,1), (2,2), (5,5)):
    o = orient(line_a, line_b, p)
    print(f"  p={str(p):<8} -> {'左' if o>0 else '右' if o<0 else '线上'}")

print("\n== 点在线段上 ==")
seg_a, seg_b = (0,0), (4,0)
for p in ((2,0), (0,0), (5,0), (-1,0), (2,1), (2,0.0)):
    print(f"  p={str(p):<10} on_segment={on_segment(p, seg_a, seg_b)}")

print("\n== 点到直线距离 ==")
for p in ((0,5), (3,4), (2,2)):
    d = point_line_dist(p, (0,0), (10,0))
    print(f"  p={str(p):<8} 到 x 轴距离={d:.4f}")

print("\n== 向量夹角 ==")
for v in ((1,0), (1,1), (0,1), (-1,0), (1,-1)):
    deg = math.degrees(angle((1,0), v))
    print(f"  (1,0) 与 {str(v):<8} 夹角={deg:>6.1f}°")

print("\n== 浮点容差的重要性 ==")
p = (0.1 + 0.2, 0.0)      # 0.30000000000000004
q = (0.3, 0.0)
print(f"  p={p} q={q}")
print(f"  p == q            : {p == q}")
print(f"  用 eps 比较        : {abs(p[0]-q[0]) < EPS}")
print("  几何判定一律用 sign(cross) 带 EPS，避免共线误判")

print("\n== 叉积的几何意义 ==")
u, v = (3,0), (0,4)
print(f"  u={u} v={v} 叉积={cross(u,v)} = 以 u,v 为边的平行四边形有向面积")
print(f"  三角形面积 = |cross|/2 = {abs(cross(u,v))/2}")

print("\n== 常见坑 ==")
for line in (
    "  整数坐标叉积精确；浮点坐标必须带 EPS",
    "  orient 返回 -1/0/1 而非原始叉积值，避免量级差异干扰",
    "  退化情况：重合点、零长度线段要单独处理",
    "  极角排序用 atan2 或叉积比较，别用斜率（会除零）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现极角排序（atan2 与叉积比较两种），验证凸包输入有序。
# 2. 用叉积判断一个点集是否全部共线。
# 3. 实现点到「线段」的最短距离（区别于到直线）。
# 4. 思考：为什么几何判定不能直接用浮点 == 比较？
