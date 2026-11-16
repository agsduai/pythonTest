# ===== 第757课：计算几何与空间算法-线段相交与扫描线 =====
# 知识点：
#   - 线段相交判定：跨立实验（两次 orient 异号）+ 共线特例（on_segment）
#   - 快速排斥：先比包围盒，排除明显不相交的绝大多数情况
#   - 求交点：参数方程解 t = cross(q-p, s) / cross(r, s)，r/s 为两线段方向向量
#   - 扫描线 sweep line：按事件 x 排序，维护「当前活跃线段」有序集合
#   - Bentley-Ottmann：O((n+k) log n) 报出所有交点，避免 O(n²) 两两检查
#   - 本课用标准库实现判定/求交 + 简化扫描线（用有序列表代替平衡树）
# 依赖：无（标准库）
import math
from dataclasses import dataclass

EPS = 1e-9
Point = tuple


def orient(a, b, c):
    v = (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])
    return 0 if abs(v) < EPS else (1 if v > 0 else -1)


def cross(a, b): return a[0]*b[1] - a[1]*b[0]
def sub(a, b): return (a[0]-b[0], a[1]-b[1])
def add(a, b): return (a[0]+b[0], a[1]+b[1])
def mul(a, k): return (a[0]*k, a[1]*k)


def on_segment(p, a, b):
    return (orient(a, b, p) == 0 and
            min(a[0],b[0])-EPS <= p[0] <= max(a[0],b[0])+EPS and
            min(a[1],b[1])-EPS <= p[1] <= max(a[1],b[1])+EPS)


def bbox_overlap(a, b, c, d):
    """快速排斥：两线段包围盒是否重叠。"""
    return not (max(a[0],b[0]) < min(c[0],d[0]) - EPS or
                max(c[0],d[0]) < min(a[0],b[0]) - EPS or
                max(a[1],b[1]) < min(c[1],d[1]) - EPS or
                max(c[1],d[1]) < min(a[1],b[1]) - EPS)


def segments_intersect(a, b, c, d):
    if not bbox_overlap(a, b, c, d):
        return False
    o1, o2, o3, o4 = orient(a,b,c), orient(a,b,d), orient(c,d,a), orient(c,d,b)
    if o1 == 0 and on_segment(c, a, b): return True
    if o2 == 0 and on_segment(d, a, b): return True
    if o3 == 0 and on_segment(a, c, d): return True
    if o4 == 0 and on_segment(b, c, d): return True
    return o1 != o2 and o3 != o4


def intersection_point(a, b, c, d):
    """返回交点或 None；平行/共线时返回 None 或端点。"""
    r, s = sub(b, a), sub(d, c)
    denom = cross(r, s)
    if abs(denom) < EPS:
        return None                      # 平行或共线
    t = cross(sub(c, a), s) / denom
    return add(a, mul(r, t))


@dataclass
class Segment:
    name: str
    a: Point
    b: Point

    @property
    def xmin(self): return min(self.a[0], self.b[0])
    @property
    def xmax(self): return max(self.a[0], self.b[0])

    def y_at(self, x):
        if abs(self.b[0] - self.a[0]) < EPS:
            return self.a[1]
        t = (x - self.a[0]) / (self.b[0] - self.a[0])
        return self.a[1] + t * (self.b[1] - self.a[1])


print("== 线段相交判定（跨立实验）==")
cases = [
    ("标准交叉", (0,0),(4,4), (0,4),(4,0), True),
    ("共线但分离", (0,0),(1,1), (2,2),(3,3), False),
    ("端点接触", (0,0),(2,2), (2,2),(4,0), True),
    ("共线重叠", (0,0),(4,0), (2,0),(6,0), True),
    ("共线分离", (0,0),(1,0), (3,0),(4,0), False),
    ("平行", (0,0),(4,0), (0,1),(4,1), False),
    ("包围盒重叠但不相交", (0,0),(4,4), (0,3),(1,2), False),
]
for name, a,b,c,d, expect in cases:
    got = segments_intersect(a,b,c,d)
    print(f"  {name:<18}: {got!s:<5} 期望={expect} {'OK' if got==expect else '不符'}")

print("\n== 求交点 ==")
for a,b,c,d in (((0,0),(4,4),(0,4),(4,0)),
                ((0,0),(4,0),(2,-2),(2,2)),
                ((0,0),(2,0),(0,1),(2,1))):
    p = intersection_point(a,b,c,d)
    print(f"  {a}{b} × {c}{d} -> {p}")
print("  平行/共线返回 None（共线重叠有无穷多交点，需单独约定）")

print("\n== 暴力两两求交 O(n²) ==")
segs = [Segment(f"s{i}", (i%5, i//5), ((i*3)%7+1, (i*2)%5+1)) for i in range(12)]
hits = []
for i in range(len(segs)):
    for j in range(i+1, len(segs)):
        A, B = segs[i], segs[j]
        if segments_intersect(A.a, A.b, B.a, B.b):
            p = intersection_point(A.a, A.b, B.a, B.b)
            hits.append((A.name, B.name, p))
print(f"  {len(segs)} 条线段，暴力检查 {len(segs)*(len(segs)-1)//2} 对，命中 {len(hits)} 对")
for x in hits[:5]: print("   ", x)

print("\n== 扫描线（简化版：只维护 x 区间活跃的线段）==")
events = []
for s in segs:
    events.append((s.xmin, "add", s.name))
    events.append((s.xmax, "remove", s.name))
events.sort()
active, peak, trace = set(), 0, []
for x, kind, name in events:
    if kind == "add": active.add(name)
    else: active.discard(name)
    peak = max(peak, len(active))
    if len(trace) < 8:
        trace.append((round(x,2), kind, sorted(active)))
print("  事件序列（前 8）:")
for x, kind, act in trace:
    print(f"    x={x:<6} {kind:<6} 活跃={act}")
print(f"  峰值活跃线段数={peak}（远小于 {len(segs)}，扫描线只在相邻活跃对里查相交）")
print("  Bentley-Ottmann 用平衡树按 y 排序活跃集，只比较相邻线段 -> O((n+k)log n)")

print("\n== 复杂度对比 ==")
print(f"  {'方法':<20}{'复杂度':<20}{'适用'}")
for row in (("暴力两两", "O(n²)", "n<100 或教学"),
            ("均匀网格", "O(n + k) 均摊", "分布均匀"),
            ("扫描线 B-O", "O((n+k) log n)", "通用、交点少")):
    print(f"  {row[0]:<20}{row[1]:<20}{row[2]}")

print("\n== 应用 ==")
for line in [
    "  GIS 道路叠加、CAD 布尔运算、VLSI 设计规则检查",
    "  游戏碰撞检测（宽相位用包围盒，窄相位用线段相交）",
    "  多边形自交检测、地图边界合法性校验",
    "  与第66章点线面关系、第756课凸包串联",
]:
    print("  -", line)

print("\n== 工程要点 ==")
for line in [
    "  所有判定带 EPS；整数坐标可用精确整数叉积避免误差",
    "  共线重叠、端点接触、退化线段要显式定义语义",
    "  扫描线的事件顺序：同 x 时 add 先于 remove，避免漏判",
    "  浮点求交结果要 clamp 回线段范围内再用",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现完整的 Bentley-Ottmann（含事件队列与 y 序状态），输出全部交点。
# 2. 用均匀网格索引替代暴力两两，实测加速比。
# 3. 处理共线重叠线段，返回重叠区间的两个端点。
# 4. 思考：为什么扫描线只需比较「y 序相邻」的线段？
