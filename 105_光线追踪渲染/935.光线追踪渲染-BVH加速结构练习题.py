# ===== 第935课：光线追踪渲染-BVH加速结构 =====
# 知识点：
#   - 暴力求交：每条光线要测所有物体 O(n)；BVH：包围盒树 O(log n)
#   - BVH 节点 = AABB 包围盒 + 两个子节点；叶子存物体列表
#   - 光线-AABB 测试（slab 法）：先查包围盒，miss 则整棵子树剪掉
#   - 构建：按最长的轴取中位数划分 —— O(n log²n) 简单够用
#   - 收益的前提：包围盒要『紧』且子树不重叠 —— 顺序对结果影响大
# 依赖：无（标准库）
import math
import random
import time


class AABB:
    """轴对齐包围盒：(min, max) 三元组对。"""

    def __init__(self, vmin, vmax):
        self.vmin = vmin
        self.vmax = vmax

    @staticmethod
    def around_spheres(spheres):
        xs = [(c[0] - r, c[0] + r) for c, r, _ in spheres]
        ys = [(c[1] - r, c[1] + r) for c, r, _ in spheres]
        zs = [(c[2] - r, c[2] + r) for c, r, _ in spheres]
        return AABB((min(x[0] for x in xs), min(y[0] for y in ys),
                     min(z[0] for z in zs)),
                    (max(x[1] for x in xs), max(y[1] for y in ys),
                     max(z[1] for z in zs)))

    def union_with(self, other):
        return AABB(tuple(min(a, b) for a, b in zip(self.vmin, other.vmin)),
                    tuple(max(a, b) for a, b in zip(self.vmax, other.vmax)))

    def hit(self, origin, direction):
        """slab 法：光线与 6 个面构成的区间求交。"""
        tmin, tmax = -math.inf, math.inf
        for o, d, lo, hi in zip(origin, direction, self.vmin, self.vmax):
            if abs(d) < 1e-12:
                if o < lo or o > hi:
                    return False
                continue
            t1 = (lo - o) / d
            t2 = (hi - o) / d
            if t1 > t2:
                t1, t2 = t2, t1
            tmin = max(tmin, t1)
            tmax = min(tmax, t2)
            if tmin > tmax:
                return False
        return tmax >= max(tmin, 0.0)


class BVHNode:
    def __init__(self, bounds, left=None, right=None, spheres=None):
        self.bounds = bounds
        self.left = left
        self.right = right
        self.spheres = spheres               # 叶子才非空


def build_bvh(spheres, depth=0, max_leaf=4):
    bounds = AABB.around_spheres(spheres)
    if len(spheres) <= max_leaf or depth > 16:
        return BVHNode(bounds, spheres=spheres)
    # 按包围盒最长轴的中位数划分
    extent = [bounds.vmax[i] - bounds.vmin[i] for i in range(3)]
    axis = extent.index(max(extent))
    ordered = sorted(spheres, key=lambda s: s[0][axis])
    mid = len(ordered) // 2
    left = build_bvh(ordered[:mid], depth + 1, max_leaf)
    right = build_bvh(ordered[mid:], depth + 1, max_leaf)
    return BVHNode(bounds, left=left, right=right)


def intersect_sphere(origin, direction, center, radius):
    oc = v_sub(origin, center)
    b = 2 * dot(oc, direction)
    c = dot(oc, oc) - radius * radius
    disc = b * b - 4 * c
    if disc < 0:
        return None
    sq = math.sqrt(disc)
    t1, t2 = (-b - sq) / 2, (-b + sq) / 2
    if t1 > 1e-4:
        return t1
    if t2 > 1e-4:
        return t2
    return None


def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


class Tracer:
    """同一场景的两种求交策略：暴力 vs BVH。"""

    def __init__(self, spheres):
        self.spheres = spheres
        self.bvh = build_bvh(spheres)
        self.tests = 0                        # 求交测试计数（性能指标）

    def _hit_sphere(self, origin, direction, sphere):
        self.tests += 1
        return intersect_sphere(origin, direction,
                                sphere[0], sphere[1])

    def nearest_brute(self, origin, direction):
        best_t, best = None, None
        for s in self.spheres:
            t = self._hit_sphere(origin, direction, s)
            if t is not None and (best_t is None or t < best_t):
                best_t, best = t, s
        return best_t, best

    def nearest_bvh(self, origin, direction):
        stack = [self.bvh]
        best_t, best = None, None
        while stack:
            node = stack.pop()
            if not node.bounds.hit(origin, direction):
                continue                      # 包围盒没打中 -> 整棵剪掉
            if node.spheres is not None:      # 叶子
                for s in node.spheres:
                    t = self._hit_sphere(origin, direction, s)
                    if t is not None and (best_t is None or t < best_t):
                        best_t, best = t, s
            else:
                stack.append(node.left)
                stack.append(node.right)
        return best_t, best


def v_add_wrapper(a, b):
    return v_add(a, b)


print("== 场景：150 个随机球 ==")
rng = random.Random(135)
spheres = []
for _ in range(150):
    c = (rng.uniform(-8, 8), rng.uniform(-4, 4), rng.uniform(4, 20))
    spheres.append((c, rng.uniform(0.15, 0.5), (255, 200, 150)))
tracer = Tracer(spheres)
print(f"  球体数 = {len(spheres)}")

print("\n== 包围盒的剪枝演示 ==")
origin = (0, 0, 0)
direction = (0, 0, 1)
tests_naive = len(spheres)
t_b, obj_b = tracer.nearest_bvh(origin, direction)
print(f"  暴力：光线 (0,0,1) 需要 {tests_naive} 次球体求交")
print(f"  BVH ：同一光线实际求交 {tracer.tests} 次（包围盒测试另计，更便宜）")
print(f"  两者结果一致: "
      f"{tracer.nearest_brute(origin, direction)[0] is not None} vs {t_b is not None}")
print(f"  命中距离: BVH {t_b:.3f}" if t_b else "  BVH: 未命中")

print("\n== 全帧渲染的求交统计 ==")
for method in ("brute", "bvh"):
    tracer.tests = 0
    t0 = time.perf_counter()
    hits = 0
    for row in range(24):
        for col in range(48):
            x = 2 * (col + 0.5) / 48 - 1
            y = (1 - 2 * (row + 0.5) / 24) / 2.0
            d = (x, y, 1.0)
            n = math.sqrt(dot(d, d))
            d = (d[0] / n, d[1] / n, d[2] / n)
            if method == "brute":
                t, obj = tracer.nearest_brute(origin, d)
            else:
                t, obj = tracer.nearest_bvh(origin, d)
            hits += (t is not None)
    elapsed = time.perf_counter() - t0
    print(f"  {method:>6}: 1152 条光线, 求交 {tracer.tests} 次, "
          f"{elapsed * 1000:.1f} ms, 命中 {hits}")
print("  BVH 把每光线求交从 O(n) 降到 ~O(log n) —— 场景越大收益越大")

print("\n== 光线-AABB 的 slab 法 ==")
box = AABB((1, -1, 2), (2, 1, 6))
inside_ray = (0, 0, 0), (0, 0, 1)
print(f"  光线 (0,0,1) 打盒子 x∈[1,2]: {box.hit(*inside_ray)}")
miss_ray = (0, 0, 0), (0, 1, 1)
print(f"  光线 (0,1,1) 从盒上方掠过: {box.hit(*miss_ray)}")

print("\n== 节点数与深度 ==")


def bvh_stats(node, depth=0):
    if node.spheres is not None:
        return (1, 1, depth)                  # (节点, 叶子, 最大深度)
    l = bvh_stats(node.left, depth + 1)
    r = bvh_stats(node.right, depth + 1)
    return (1 + l[0] + r[0], l[1] + r[1], max(l[2], r[2]))


nodes, leaves, max_depth = bvh_stats(tracer.bvh)
print(f"  节点 {nodes}, 叶子 {leaves}, 最大深度 {max_depth}")
print("  叶子 ≤4 个球：查询成本 ≈ 深度 × 少量球体求交")

print("\n== 顺序与包围盒质量 ==")
shuffled = spheres[:]
rng.shuffle(shuffled)
tracer2 = Tracer(shuffled)
n2, l2, d2 = bvh_stats(tracer2.bvh)
print(f"  打乱输入顺序后重建: 节点 {n2}, 叶子 {l2}, 深度 {d2}")
print("  中位数划分对顺序不敏感；但对『按空间聚类的数据』质量最佳")
print("  更高质量的划分用 SAH（表面面积启发式）—— 以建树时间换查询时间")

print("\n== 小结 ==")
for line in (
    "  BVH = 包围盒二叉树：miss 一次剪掉一片，求交从 O(n) 到 O(log n)",
    "  slab 法的 AABB 测试便宜（6 次除法）—— 剪枝收益远大于测试成本",
    "  叶子大小/划分轴是构建参数；SAH 是工业级做法",
    "  936 课：加了 BVH 之后，蒙特卡洛路径追踪才跑得动",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 SAH：对候选划分计算 cost = 遍历概率 × 子节点面积，选最优轴与位置。
# 2. 实现「均匀网格」加速结构，与 BVH 对比渲染耗时。
# 3. 实现动态场景的「BVH 增量更新」（球每帧移动一点点时的重构策略）。
# 4. 思考：为什么 BVH 比 KD-tree 更适合三角形网格？（提示：物体排序 vs
#    空间划分、三角形的重叠包围盒）
