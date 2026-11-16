# ===== 第759课：计算几何与空间算法-最近点对与分治 =====
# 知识点：
#   - 最近点对 closest pair：在 n 个点里找欧氏距离最小的一对
#   - 暴力 O(n²)；分治 O(n log n)：按 x 分两半，递归求左右最小距离 d
#   - 合并：只检查中线附近 |x - mid| < d 的点，且按 y 序每个点最多比 7 个后继
#   - 「每个点最多比较常数个」来自鸽巢原理：d×2d 矩形里最多放 8 个互不更近的点
#   - 与第78章组合优化不同：这里利用几何结构得到严格的多项式算法
#   - 也可用扫描线 O(n log n) 或均匀网格 O(n) 均摊
# 依赖：无（标准库）
import math
import random
import time

Point = tuple


def dist2(a, b): return (a[0]-b[0])**2 + (a[1]-b[1])**2


def brute_force(pts):
    best, pair = float("inf"), None
    for i in range(len(pts)):
        for j in range(i+1, len(pts)):
            d = dist2(pts[i], pts[j])
            if d < best:
                best, pair = d, (pts[i], pts[j])
    return math.sqrt(best), pair


def closest_pair(pts):
    """分治 O(n log n)：按 x 排序，合并时按 y 序只查带状区域。"""
    px = sorted(pts)
    def rec(xs):
        n = len(xs)
        if n <= 3:
            return brute_force(xs)
        mid = n // 2
        midx = xs[mid][0]
        d1, p1 = rec(xs[:mid])
        d2, p2 = rec(xs[mid:])
        d, best_pair = (d1, p1) if d1 <= d2 else (d2, p2)
        # 带状区：|x - midx| < d 的点，按 y 排序
        strip = [p for p in xs if (p[0]-midx)**2 < d*d]
        strip.sort(key=lambda p: p[1])
        for i in range(len(strip)):
            # 每个点最多与后续 7 个比较（鸽巢原理）
            for j in range(i+1, min(i+8, len(strip))):
                dd = dist2(strip[i], strip[j])
                if dd < d*d:
                    d, best_pair = math.sqrt(dd), (strip[i], strip[j])
        return d, best_pair
    return rec(px)


def grid_nearest(pts, cell=None):
    """均匀网格均摊 O(n)：按格子哈希，只查本格与 8 邻格。"""
    if not pts: return float("inf"), None
    if cell is None:
        # 用平均间距估计格子大小
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        span = max(max(xs)-min(xs), max(ys)-min(ys), 1e-9)
        cell = span / math.sqrt(len(pts))
    grid = {}
    for p in pts:
        grid.setdefault((int(p[0]//cell), int(p[1]//cell)), []).append(p)
    best, pair = float("inf"), None
    for p in pts:
        cx, cy = int(p[0]//cell), int(p[1]//cell)
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for q in grid.get((cx+dx, cy+dy), ()):
                    if q is p: continue
                    d = dist2(p, q)
                    if d < best:
                        best, pair = d, (p, q)
    return math.sqrt(best), pair


print("== 小例子：三种方法结果一致 ==")
pts = [(2,3),(12,30),(40,50),(5,1),(12,10),(3,4),(7,7),(9,8)]
for name, fn in (("暴力", brute_force), ("分治", closest_pair),
                 ("网格", lambda ps: grid_nearest(ps, 4))):
    d, pair = fn(pts)
    print(f"  {name:<6}: d={d:.6f} pair={pair}")

print("\n== 随机数据正确性校验 ==")
for seed in range(20):
    r = random.Random(seed)
    cloud = [(r.uniform(0,1000), r.uniform(0,1000)) for _ in range(60)]
    db, _ = brute_force(cloud)
    dc, _ = closest_pair(cloud)
    assert abs(db - dc) < 1e-9, (seed, db, dc)
print("  20 组随机点：分治结果与暴力完全一致")

print("\n== 复杂度实测 ==")
for n in (100, 500, 1000, 3000):
    r = random.Random(n)
    cloud = [(r.uniform(0,10000), r.uniform(0,10000)) for _ in range(n)]
    t0=time.perf_counter(); d1,_=closest_pair(cloud); t1=time.perf_counter()
    t2=time.perf_counter(); d2,_=grid_nearest(cloud); t3=time.perf_counter()
    print(f"  n={n:>5}: 分治={t1-t0:.3f}s 网格={t3-t2:.3f}s "
          f"距离一致={abs(d1-d2)<1e-9}")
print("  n 大到暴力 O(n²) 已明显不划算（这里不再跑基线）")

print("\n== 鸽巢原理：为什么每个点只比 7 个后继 ==")
for line in (
    "  合并时左右两半内部各自的最小距离都 >= d",
    "  在 d×2d 的矩形里，任意两点距离 >= d，最多能放 8 个点",
    "  所以按 y 排序后，第 i 个点只需看接下来最多 7 个",
    "  这是分治能到 O(n log n) 的关键，而不是 O(n²) 回退",
):
    print(" ", line)

print("\n== 边界情况 ==")
for cloud, label in (([(0,0)], "1 个点"), ([(0,0),(1,1)], "2 个点"),
                     ([(0,0),(0,0),(1,1)], "有重合点")):
    try:
        d, pair = closest_pair(cloud)
        print(f"  {label}: d={d} pair={pair}")
    except Exception as e:
        print(f"  {label}: {type(e).__name__}（需特判点数为 1）")

print("\n== 高维与替代方案 ==")
for line in (
    "  d 维最近点对：分治常数随维度指数增长，常用 KD-tree / LSH",
    "  近似最近邻：LSH、乘积量化，牺牲精度换速度（第624课）",
    "  动态点集：需支持插入删除，用平衡结构维护",
    "  曼哈顿/切比雪夫距离：换度量后带状区域形状要跟着改",
):
    print(" ", line)

print("\n== 应用 ==")
for line in [
    "  碰撞检测里找最可能相撞的一对物体",
    "  聚类（单链接层次聚类的第一步）",
    "  天文/点云配准、图像特征点匹配",
    "  与第624课 geohash/网格索引共享「空间划分」思想",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 处理「点数为 1」与「重合点」的边界，让 closest_pair 返回 (0, pair) 或 None。
# 2. 把分治改成扫描线实现（按 x 推进、维护按 y 排序的活跃集）。
# 3. 用 KD-tree 求最近邻，对比与网格法的查询耗时。
# 4. 思考：为什么合并步骤里带状区按 y 排序后只需比较常数个点？
