# ===== 第937课：光线追踪渲染-软阴影与环境遮蔽 =====
# 知识点：
#   - 点光源 → 边缘锋利的硬阴影；面光源（区域光）→ 半影软阴影
#   - 软阴影 = 对光源面积采样：每次阴影光线取光源上不同点，平均结果
#   - 环境遮蔽（AO）：某点向半球随机采样，被遮挡比例 = 接触阴影强度
#   - 两者都是「多采几条射线取平均」—— 又是蒙特卡洛
#   - AO 不物理但视觉价值极高（凹陷处变暗）—— 游戏标配
# 依赖：无（标准库）
import math
import random


def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def normalize(a):
    n = math.sqrt(dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n)


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


class Scene:
    def __init__(self):
        self.spheres = []

    def add(self, center, radius):
        self.spheres.append((center, radius))

    def occluded(self, origin, direction, max_dist=1e18):
        for center, radius in self.spheres:
            t = intersect_sphere(origin, direction, center, radius)
            if t is not None and t < max_dist:
                return True
        return False


def uniform_hemisphere(normal, rng):
    """半球均匀随机方向（AO 用均匀分布即可）。"""
    w = normal
    if abs(w[0]) <= abs(w[1]) and abs(w[0]) <= abs(w[2]):
        helper = (1.0, 0.0, 0.0)
    elif abs(w[1]) <= abs(w[2]):
        helper = (0.0, 1.0, 0.0)
    else:
        helper = (0.0, 0.0, 1.0)
    u = normalize((helper[1] * w[2] - helper[2] * w[1],
                   helper[2] * w[0] - helper[0] * w[2],
                   helper[0] * w[1] - helper[1] * w[0]))
    v = (w[1] * u[2] - w[2] * u[0],
         w[2] * u[0] - w[0] * u[2],
         w[0] * u[1] - w[1] * u[0])
    z = rng.random()
    r = math.sqrt(max(0.0, 1 - z * z))
    phi = rng.random() * 2 * math.pi
    d_local = (r * math.cos(phi), r * math.sin(phi), z)
    return (d_local[0] * u[0] + d_local[1] * v[0] + d_local[2] * w[0],
            d_local[0] * u[1] + d_local[1] * v[1] + d_local[2] * w[1],
            d_local[0] * u[2] + d_local[1] * v[2] + d_local[2] * w[2])


rng = random.Random(137)
scene = Scene()
scene.add((0.0, -1.0, 4.0), 1.0)               # 遮挡球
scene.add((0.6, -1.1, 3.4), 0.5)               # 遮挡小球
scene.add((0.0, 2.5, 1.5), 0.7)                # 高处的球（弱遮挡）

print("== 硬阴影 vs 软阴影：沿地面扫一排采样点 ==")
light_center = (0.0, 3.0, 2.0)
light_radius = 1.2                              # 区域光半径
ground_y = -2.05

def ground_point_shadow(px):
    """地面点 p 的硬/软阴影强度。"""
    p = (px, ground_y, 4.0)
    l = v_sub(light_center, p)
    dist = math.sqrt(dot(l, l))
    l_dir = v_scale(l, 1 / dist)
    # 硬阴影：把面光源当点
    hard = scene.occluded(v_add(p, v_scale(l_dir, 1e-3)), l_dir, dist)
    # 软阴影：在光源盘上采样 N 次
    occluded_n = 0
    samples = 30
    w = normalize(l_dir)
    if abs(w[0]) <= abs(w[1]) and abs(w[0]) <= abs(w[2]):
        helper = (1.0, 0.0, 0.0)
    elif abs(w[1]) <= abs(w[2]):
        helper = (0.0, 1.0, 0.0)
    else:
        helper = (0.0, 0.0, 1.0)
    u = normalize((helper[1] * w[2] - helper[2] * w[1],
                   helper[2] * w[0] - helper[0] * w[2],
                   helper[0] * w[1] - helper[1] * w[0]))
    v = (w[1] * u[2] - w[2] * u[0],
         w[2] * u[0] - w[0] * u[2],
         w[0] * u[1] - w[1] * u[0])
    for _ in range(samples):
        r = light_radius * math.sqrt(rng.random())
        theta = rng.random() * 2 * math.pi
        sample_light = v_add(light_center,
                             v_add(v_scale(u, r * math.cos(theta)),
                                   v_scale(v, r * math.sin(theta))))
        to_light = v_sub(sample_light, p)
        length_tl = math.sqrt(dot(to_light, to_light))
        dir_tl = v_scale(to_light, 1 / length_tl)
        if scene.occluded(v_add(p, v_scale(dir_tl, 1e-3)), dir_tl, length_tl):
            occluded_n += 1
    return hard, occluded_n / samples


print(f"  {'地面x':>8}{'硬阴影':>10}{'软阴影(可见比例)':>18}")
profile = []
for px in (-1.6, -1.0, -0.4, 0.0, 0.4, 1.0, 1.6):
    hard, soft_vis = ground_point_shadow(px)
    profile.append((px, hard, soft_vis))
    soft = "阴" if soft_vis < 0.15 else ("半" if soft_vis < 0.7 else "亮")
    print(f"  {px:>8.1f}{str(hard):>10}{soft_vis:>18.2f}  [{soft}]")
print("  硬阴影是阶跃；软阴影有渐变的半影带 —— 物理正确的光源必然有面积")

print("\n== 环境遮蔽（AO）==")
def ambient_occlusion(point, normal, samples=30):
    blocked = 0
    for _ in range(samples):
        d = uniform_hemisphere(normal, rng)
        origin = v_add(point, v_scale(normal, 1e-3))
        if scene.occluded(origin, d, max_dist=2.5):
            blocked += 1
    return 1 - blocked / samples                # AO 值：1 = 完全开放


probe_points = [
    ((0.0, -1.05, 3.6), "贴近大球底部"),
    ((0.0, -1.2, 4.8), "远离遮挡物"),
    ((1.2, -1.0, 3.2), "两球夹缝"),
]
print(f"  {'采样点':<16}{'AO值':>8}  视觉含义")
for point, desc in probe_points:
    n = (0, 1, 0)
    ao = ambient_occlusion(point, n)
    visual = "开放明亮" if ao > 0.8 else ("半遮蔽" if ao > 0.4 else "接触阴影")
    print(f"  {desc:<16}{ao:>8.2f}  {visual}")
print("  缝隙与接触处的 AO 显著更低 —— 这就是『接触阴影』")

print("\n== AO 的应用 ==")
for line in (
    "  游戏实时渲染：SSAO（屏幕空间 AO）作后处理叠加",
    "  影视路径追踪：AO 不是单独特效，而是全局光照的自然结果",
    "  3D 打印/摄影测量：AO 贴图让材质立体感倍增",
    "  AO 非物理（只测遮挡不追踪反射），但视觉收益/成本比极高",
):
    print("  -", line)

print("\n== 采样数与噪声 ==")
point = (0.6, -1.1, 3.4)
n = (0, 1, 0)
print(f"  {'AO采样数':>10}{'AO值波动':>14}")
for samples in (5, 15, 30, 100):
    vals = [ambient_occlusion(point, n, samples) for _ in range(8)]
    mean = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
    print(f"  {samples:>10}{sd:>14.4f}")
print("  波动 ∝ 1/√N —— 与 936 课的收敛规律一致")

print("\n== 小结 ==")
for line in (
    "  面光源采样 → 半影；半球采样 → AO；都是阴影射线的蒙特卡洛化",
    "  AO 用均匀半球分布就够；软阴影要按光源面积均匀采样",
    "  采样数是这三个效果共同的旋钮（又是 1/√N）",
    "  938 课：把 931~937 全部效果拼成最终的迷你路径追踪器",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「接触硬化」：AO 的 max_dist 随采样点与遮挡物距离动态调整。
# 2. 实现「彩色区域光」：光采样点带颜色，半影带出现色温渐变。
# 3. 把 AO 嵌入 932 课的光照模型，渲染 AO 加强版 ASCII 场景。
# 4. 思考：SSAO 为什么用深度缓冲近似而不真的发半球射线？误差出现在哪些
#    场景（薄物体、屏幕外遮挡物）？
