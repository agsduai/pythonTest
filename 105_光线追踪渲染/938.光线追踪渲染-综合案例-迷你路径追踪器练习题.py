# ===== 第938课：光线追踪渲染-综合案例-迷你路径追踪器 =====
# 知识点：
#   - 综合：求交(931) + 光照/阴影(932) + 反射折射(933) + 相机(934) +
#     BVH(935) + 路径追踪(936) + 软阴影/AO(937)
#   - 迷你引擎：材质注册表 + 场景构建 DSL + PPM 输出（临时目录）
#   - 每像素统计：路径数 / 反弹次数 / 命中率 —— 性能报告
#   - 渲染 = 物理：渲染方程的蒙特卡洛求解器（影片级画质的原理）
# 依赖：无（标准库）
import math
import os
import random
import tempfile
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


def reflect(d, n):
    return v_sub(d, v_scale(n, 2 * dot(d, n)))


def refract(d, n, eta):
    cos_i = -dot(d, n)
    sin2_t = eta * eta * (1 - cos_i * cos_i)
    if sin2_t > 1.0:
        return None
    cos_t = math.sqrt(1 - sin2_t)
    return v_add(v_scale(d, eta), v_scale(n, eta * cos_i - cos_t))


def cosine_hemisphere(normal, rng):
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
    r = math.sqrt(rng.random())
    theta = rng.random() * 2 * math.pi
    d = (r * math.cos(theta), r * math.sin(theta),
         math.sqrt(max(0.0, 1 - r * r)))
    return (d[0] * u[0] + d[1] * v[0] + d[2] * w[0],
            d[0] * u[1] + d[1] * v[1] + d[2] * w[1],
            d[0] * u[2] + d[1] * v[2] + d[2] * w[2])


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


class MiniPathTracer:
    def __init__(self, seed=138):
        self.spheres = []                       # dict: center/radius/material
        self.rng = random.Random(seed)
        self.stats = {"paths": 0, "rays": 0, "bounces": 0, "hits": 0}

    def add_sphere(self, center, radius, material):
        self.spheres.append({"center": center, "radius": radius,
                             "material": material})

    def nearest(self, origin, direction):
        best_t, best = None, None
        for obj in self.spheres:
            t = intersect_sphere(origin, direction,
                                 obj["center"], obj["radius"])
            self.stats["rays"] += 1
            if t is not None and (best_t is None or t < best_t):
                best_t, best = t, obj
        return best_t, best

    def trace(self, origin, direction, max_bounces=4):
        """一条路径：返回 radiance (r,g,b) 与终止原因。"""
        self.stats["paths"] += 1
        throughput = (1.0, 1.0, 1.0)
        radiance = (0.0, 0.0, 0.0)
        for bounce in range(max_bounces):
            self.stats["bounces"] += 1
            t, obj = self.nearest(origin, direction)
            if obj is None:
                radiance = tuple(r + tp * s for r, tp, s in
                                 zip(radiance, throughput, (0.3, 0.5, 0.85)))
                return radiance, "sky"
            self.stats["hits"] += 1
            hit = v_add(origin, v_scale(direction, t))
            normal = normalize(v_sub(hit, obj["center"]))
            mat = obj["material"]
            if mat["kind"] == "light":
                radiance = tuple(r + tp * e for r, tp, e in
                                 zip(radiance, throughput, mat["emission"]))
                return radiance, "light"
            # 直接光照（Next Event Estimation，936 课练习的实现）
            sun = normalize((0.5, 0.9, -0.4))
            if mat["kind"] == "diffuse" and dot(normal, sun) > 0:
                shadow_origin = v_add(hit, v_scale(normal, 1e-4))
                st, sobj = self.nearest(shadow_origin, sun)
                self.stats["rays"] += 1
                if sobj is None:
                    radiance = tuple(r + tp * dot(normal, sun) * c / 255 * 1.4
                                     for r, tp, c in
                                     zip(radiance, throughput, mat["color"]))
            if bounce == max_bounces - 1:
                return radiance, "max_depth"
            if mat["kind"] == "diffuse":
                new_dir = cosine_hemisphere(normal, self.rng)
                origin = v_add(hit, v_scale(normal, 1e-4))
                direction = new_dir
                throughput = tuple(tp * c / 255 * 1.5
                                   for tp, c in zip(throughput, mat["color"]))
            elif mat["kind"] == "mirror":
                direction = reflect(direction, normal)
                origin = v_add(hit, v_scale(normal, 1e-4))
                throughput = tuple(tp * c / 255 * 1.8
                                   for tp, c in zip(throughput, mat["color"]))
            elif mat["kind"] == "glass":
                eta = 1.0 / 1.5 if not mat.get("inside") else 1.5
                refr = refract(direction, normal, eta)
                if refr is None:
                    direction = reflect(direction, normal)
                else:
                    direction = refr
                origin = v_add(hit, v_scale(direction, 1e-4))
            else:
                return radiance, "unknown_material"
        return radiance, "max_depth"

    def render(self, width, height, samples):
        """渲染一帧：返回颜色数组与耗时。"""
        t0 = time.perf_counter()
        img = []
        for py in range(height):
            row = []
            for px in range(width):
                acc = [0.0, 0.0, 0.0]
                x = 2 * (px + 0.5) / width - 1
                y = (1 - 2 * (py + 0.5) / height) / 2.0
                for _ in range(samples):
                    radiance, _ = self.trace((0, 0, 0),
                                             normalize((x, y, 1.0)), 4)
                    acc[0] += radiance[0]
                    acc[1] += radiance[1]
                    acc[2] += radiance[2]
                row.append(tuple(min(255, int(c / samples)) for c in acc))
            img.append(row)
        elapsed = time.perf_counter() - t0
        return img, elapsed


def save_ppm(img, path):
    with open(path, "wb") as fh:
        fh.write(f"P6 {len(img[0])} {len(img)} 255\n".encode())
        for row in img:
            for (r, g, b) in row:
                fh.write(bytes((r, g, b)))


def ascii_view(img):
    chars = " .:-=+*#%@"
    lines = []
    for row in img:
        lines.append("".join(
            chars[min(len(chars) - 1,
                      int((r + g + b) / (3 * 255) * (len(chars) - 1)))]
            for r, g, b in row))
    return lines


print("== 搭建场景（DSL 风格）==")
tracer = MiniPathTracer(seed=138)
tracer.add_sphere((0.0, -6.0, 0.5), 5.5,
                  {"kind": "diffuse", "color": (190, 180, 160)})       # 地面
tracer.add_sphere((0.0, 0.0, 4.0), 1.0,
                  {"kind": "diffuse", "color": (230, 95, 85)})         # 红球主体
tracer.add_sphere((-1.8, -0.2, 3.5), 0.75,
                  {"kind": "mirror", "color": (235, 235, 235)})        # 镜面球
tracer.add_sphere((1.6, 0.1, 3.3), 0.7,
                  {"kind": "diffuse", "color": (95, 140, 230)})        # 蓝球
tracer.add_sphere((0.0, 3.2, 1.5), 0.55,
                  {"kind": "light", "emission": (255, 250, 230)})      # 天灯
for s in tracer.spheres:
    print(f"  {s['material']['kind']:<8} 球心 {s['center']} r={s['radius']}")

print("\n== 渲染 96×36 @ 8 samples ==")
img, elapsed = tracer.render(96, 36, samples=8)
total_paths = 96 * 36 * 8
print(f"  耗时 = {elapsed:.1f} s, 路径 = {total_paths}, "
      f"射线 = {tracer.stats['rays']}, 反弹 = {tracer.stats['bounces']}")
print(f"  平均每路径 {tracer.stats['rays'] / total_paths:.1f} 次求交")
print(f"  命中率 = {tracer.stats['hits'] / tracer.stats['bounces']:.1%}")

print("\n== ASCII 预览 ==")
for line in ascii_view(img):
    print("  " + line)

print("\n== PPM 输出（临时目录，随目录销毁）==")
with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "final.ppm")
    save_ppm(img, path)
    print(f"  写入 {path}（{os.path.getsize(path)} 字节）")
    print("  用任意 PPM 查看器打开即可看到彩色成品图")
    print("  （课程约定：渲染产物一律临时目录，不留文件）")

print("\n== 性能剖面 ==")
print(f"  {'指标':<22}{'数值':>12}")
for label, value in (("路径总数", total_paths),
                     ("求交总次数", tracer.stats["rays"]),
                     ("每路径求交", round(tracer.stats["rays"] / total_paths, 1)),
                     ("每秒路径", round(total_paths / elapsed)),
                     ("每秒射线", round(tracer.stats["rays"] / elapsed))):
    print(f"  {label:<22}{value!s:>12}")
print("  优化方向：向量化（NumPy 批量求交）、BVH、降噪器、GPU")

print("\n== 效果清单回顾 ==")
for line in (
    "  931 求交与遮挡    932 光照与硬阴影",
    "  933 反射与折射    934 景深与抗锯齿",
    "  935 BVH 加速      936 蒙特卡洛路径",
    "  937 软阴影与 AO   938 本课：全部集成",
):
    print("  -", line)

print("\n== 与工业渲染器的差距 ==")
for line in (
    "  几何体：只有球 → 生产需要三角网格 + 法线贴图",
    "  光照：单方向太阳 + 单灯 → 生产需要 HDRI 环境贴图、多光源采样",
    "  采样：8 spp → 影视成片常要 1000+ spp + 降噪",
    "  语言：纯 Python → C++/GPU（CUDA/OptiX）；但算法骨架完全一致",
    "  学习路径：本章原理 → pbrt-v4 源码 → 自研渲染器",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  迷你路径追踪器 = 求交 + 材质调度 + 蒙特卡洛 + 输出，四层结构",
    "  所有『高级感』来自同一个动作：每像素发更多、更聪明的光线",
    "  渲染方程是物理；蒙特卡洛是求解器；工程是让它在预算内跑完",
    "  至此光线追踪篇完结：与 86 章光栅化共同覆盖渲染的两极",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 ACES 色调映射替代直接截断，对比高亮区的过渡。
# 2. 给玻璃材质实现「内部传播」状态跟踪（进出玻璃的 eta 翻转）。
# 3. 实现「逐行渐进渲染」：先低样本出图，再对噪点最多的行补采样。
# 4. 思考：路径追踪为什么天然支持『毛玻璃、次表面散射』这类效果？在
#    光栅化管线里它们各自靠什么技巧近似？
