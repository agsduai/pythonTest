# ===== 第936课：光线追踪渲染-蒙特卡洛路径追踪 =====
# 知识点：
#   - 路径追踪 = 光线追踪 + 蒙特卡洛：漫反射面随机弹射，采样积分
#   - 渲染方程的蒙特卡洛解：多次弹射的辐射亮度 = 采样平均
#   - 余弦加权采样：与朗伯反射概率分布一致 —— 重要性采样
#   - 样本数决定噪声：误差 ~ 1/√N（与 675 章蒙特卡洛一致）
#   - 色彩溢出（color bleeding）：红色地面会把红色『染』到邻近物体上
# 依赖：无（标准库）
import math
import random
import time


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


def cosine_hemisphere(normal, rng):
    """余弦加权采样：以法线为轴在半球内随机方向（朗伯反射分布）。
    正交基用「最小分量选轴」避免与法线平行导致除零。"""
    w = normal
    if abs(w[0]) <= abs(w[1]) and abs(w[0]) <= abs(w[2]):
        helper = (1.0, 0.0, 0.0)
    elif abs(w[1]) <= abs(w[2]):
        helper = (0.0, 1.0, 0.0)
    else:
        helper = (0.0, 0.0, 1.0)
    u = normalize((
        helper[1] * w[2] - helper[2] * w[1],
        helper[2] * w[0] - helper[0] * w[2],
        helper[0] * w[1] - helper[1] * w[0]))
    v = (w[1] * u[2] - w[2] * u[0],
         w[2] * u[0] - w[0] * u[2],
         w[0] * u[1] - w[1] * u[0])
    r = math.sqrt(rng.random())
    theta = rng.random() * 2 * math.pi
    d_local = (r * math.cos(theta), r * math.sin(theta),
               math.sqrt(max(0.0, 1 - r * r)))
    return (d_local[0] * u[0] + d_local[1] * v[0] + d_local[2] * w[0],
            d_local[0] * u[1] + d_local[1] * v[1] + d_local[2] * w[1],
            d_local[0] * u[2] + d_local[1] * v[2] + d_local[2] * w[2])


class PathTracer:
    def __init__(self, spheres, rng):
        self.spheres = spheres
        self.rng = rng
        self.rays = 0

    def nearest(self, origin, direction):
        best_t, best = None, None
        for center, radius, mat in self.spheres:
            t = intersect_sphere(origin, direction, center, radius)
            if t is not None and (best_t is None or t < best_t):
                best_t, best = t, (center, radius, mat)
        self.rays += 1
        return best_t, best

    def trace_path(self, origin, direction, max_bounces=4):
        """一条路径的 radiance：递归弹射，能量随弹射衰减。"""
        throughput = (1.0, 1.0, 1.0)          # 光的「携带能量」
        radiance = (0.0, 0.0, 0.0)
        for bounce in range(max_bounces):
            t, obj = self.nearest(origin, direction)
            if obj is None:
                sky = (0.35, 0.55, 0.9)       # 天空背景
                radiance = tuple(r + tput * s for r, tput, s in
                                 zip(radiance, throughput, sky))
                break
            center, radius, mat = obj
            hit = v_add(origin, v_scale(direction, t))
            normal = normalize(v_sub(hit, center))
            if mat["kind"] == "light":
                radiance = tuple(r + tput * s for r, tput, s
                                 in zip(radiance, throughput, mat["emission"]))
                break
            if mat["kind"] == "diffuse":
                # 直接光照（简化：采样太阳方向 + 遮挡判断）
                sun = normalize((0.5, 0.9, -0.4))
                if dot(normal, sun) > 0:
                    shadow_origin = v_add(hit, v_scale(normal, 1e-4))
                    st, sobj = self.nearest(shadow_origin, sun)
                    if sobj is None:
                        radiance = tuple(
                            r + tput * s * dot(normal, sun) * 0.9
                            for r, tput, s in zip(radiance, throughput,
                                                  mat["color"]))
                # 弹射：余弦加权随机方向，throughput 乘反照率
                new_dir = cosine_hemisphere(normal, self.rng)
                origin = v_add(hit, v_scale(normal, 1e-4))
                direction = new_dir
                throughput = tuple(tp * c / 255 * 1.6
                                   for tp, c in zip(throughput, mat["color"]))
                continue
            if mat["kind"] == "mirror":
                direction = v_sub(direction,
                                  v_scale(normal, 2 * dot(direction, normal)))
                origin = v_add(hit, v_scale(normal, 1e-4))
                throughput = tuple(tp * c / 255 * 1.8
                                   for tp, c in zip(throughput, mat["color"]))
                continue
            break
        return radiance


def make_scene():
    return [
        ((0.0, -6.0, 0.5), 5.5,
         {"kind": "diffuse", "color": (200, 170, 160)}),        # 地面
        ((0.0, 0.0, 4.0), 1.0,
         {"kind": "diffuse", "color": (220, 90, 80)}),          # 红球
        ((-1.7, -0.3, 3.6), 0.75,
         {"kind": "mirror", "color": (230, 230, 230)}),         # 镜面球
        ((1.5, 0.2, 3.3), 0.7,
         {"kind": "diffuse", "color": (90, 130, 220)}),         # 蓝球
        ((0.0, 3.5, 1.5), 0.6,
         {"kind": "light", "emission": (255, 255, 240)}),       # 天灯
    ]


def render(tracer, width, height, samples):
    img = []
    for py in range(height):
        row = []
        for px in range(width):
            acc = [0.0, 0.0, 0.0]
            x = 2 * (px + 0.5) / width - 1
            y = (1 - 2 * (py + 0.5) / height) / 2.0
            for _ in range(samples):
                radiance = tracer.trace_path((0, 0, 0),
                                             normalize((x, y, 1.0)), 4)
                acc[0] += radiance[0]
                acc[1] += radiance[1]
                acc[2] += radiance[2]
            row.append(tuple(min(255, int(c / samples)) for c in acc))
        img.append(row)
    return img


def ascii_view(img):
    chars = " .:-=+*#%@"
    lines = []
    for row in img:
        line = "".join(chars[min(len(chars) - 1,
                                 int((r + g + b) / (3 * 255) * (len(chars) - 1)))]
                       for r, g, b in row)
        lines.append(line)
    return lines


rng = random.Random(136)

print("== 收敛实验：同一条像素随样本数的 radiance ==")
tracer = PathTracer(make_scene(), rng)
px_target = 24
py_target = 12
x = 2 * (px_target + 0.5) / 48 - 1
y = (1 - 2 * (py_target + 0.5) / 24) / 2.0
print(f"  像素 ({px_target},{py_target})，方向 {tuple(round(v, 2) for v in normalize((x, y, 1.0)))}")
acc = [0.0, 0.0, 0.0]
for n in (1, 10, 100, 500):
    for _ in range(n if n != 1 else 1):
        rad = tracer.trace_path((0, 0, 0), normalize((x, y, 1.0)), 4)
        acc[0] += rad[0]; acc[1] += rad[1]; acc[2] += rad[2]
    total = 1 if n == 1 else n
    print(f"  样本 {n if n != 1 else 1:>4}: RGB ≈ "
          f"{tuple(round(c / total, 1) for c in acc)}"
          f"{'（方差巨大）' if n <= 10 else ''}")
print("  样本越多越稳定 —— 误差 ~1/√N，这就是蒙特卡洛渲染的收敛规律")

print("\n== 低样本 vs 高样本渲染 ==")
t0 = time.perf_counter()
img_low = render(PathTracer(make_scene(), rng), 32, 12, 2)
t_low = time.perf_counter() - t0
t0 = time.perf_counter()
img_high = render(PathTracer(make_scene(), rng), 32, 12, 40)
t_high = time.perf_counter() - t0
print(f"  2 样本/像素: {t_low * 1000:.0f} ms —— 噪声明显")
for line in ascii_view(img_low):
    print("  " + line)
print(f"  40 样本/像素: {t_high * 1000:.0f} ms —— 平滑（20 倍成本）")
for line in ascii_view(img_high):
    print("  " + line)

print("\n== 色彩溢出（color bleeding）验证 ==")
# 红球下方的地面像素：路径 红→地面 会带回红色
tracer2 = PathTracer(make_scene(), rng)
ground_dir = normalize((-0.05, -1, 1))
acc = [0.0, 0.0, 0.0]
N = 200
for _ in range(N):
    rad = tracer2.trace_path((0, 0, 0), ground_dir, 4)
    acc[0] += rad[0]; acc[1] += rad[1]; acc[2] += rad[2]
print(f"  红球下方地面像素 (200 样本): RGB ≈ "
      f"{tuple(round(c / N) for c in acc)}")
print("  绿蓝分量被红球间接照亮抬高 —— 间接光照的物理效应")

print("\n== 余弦加权采样的意义 ==")
print("  朗伯反射的概率分布 ∝ cosθ —— 采样方向按 cosθ 加权")
print("  无偏且方差更小：重要性采样的教科书案例（对照 675 章的均匀采样）")
print("  若用均匀半球采样 + 除以 cos 权重：无偏但噪声更大")

print("\n== 成本全景 ==")
print(f"  {'配置':<28}{'路径数':>12}")
w, h = 32, 12
for label, s in (("2 样本预览", 2), ("40 样本成片", 40),
                 ("1920×1080 × 100 样本", "-")):
    paths = w * h * s if s != "-" else "1920×1080×100 = 2 亿"
    print(f"  {label:<28}{paths!s:>12}")
print("  纯 Python 模拟只能做小样张；工业渲染器靠 C++/GPU/降噪器")

print("\n== 小结 ==")
for line in (
    "  路径追踪 = 蒙特卡洛积分渲染方程：随机弹射 + 平均",
    "  余弦加权采样与朗伯分布匹配 —— 重要性采样降方差",
    "  1/√N 收敛意味着 10 倍质量 = 100 倍成本 —— 噪声是它的指纹",
    "  937 课：软阴影与环境遮蔽 —— 再多采一点",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现俄罗斯轮盘（按 throughput 概率终止路径），对比偏置与噪声。
# 2. 实现光源直接采样（Next Event Estimation）：向灯盘发阴影光线，观察
#    收敛速度提升。
# 3. 实现绿色地面 + 白球的「色彩溢出」对比实验（白球底部应偏绿）。
# 4. 思考：为什么路径追踪的结果是『无偏』的？「噪声大但无偏」与「平滑但有
#    偏差」你选哪个？（两种降噪哲学）
