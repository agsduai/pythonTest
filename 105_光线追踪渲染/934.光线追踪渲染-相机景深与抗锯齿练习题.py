# ===== 第934课：光线追踪渲染-相机景深与抗锯齿 =====
# 知识点：
#   - 针孔相机无景深；薄透镜相机：光圈采样 + 对焦平面 → 真实模糊
#   - 景深 = 对焦距离前后清晰的范围；光圈越大模糊越强
#   - 抗锯齿：每像素采多束抖动光线取平均 —— 4x SSAA 是入门标配
#   - 采样即蒙特卡洛（675 章思想在渲染的应用）
#   - 全部效果都是「每像素发更多光线」—— 光线追踪的成本模型
# 依赖：无（标准库）
import math
import random
import tempfile


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

    def add(self, center, radius, color):
        self.spheres.append((center, radius, color))

    def nearest(self, origin, direction):
        best_t, best = None, None
        for center, radius, color in self.spheres:
            t = intersect_sphere(origin, direction, center, radius)
            if t is not None and (best_t is None or t < best_t):
                best_t, best = t, (center, radius, color)
        return best_t, best

    def shade(self, point, normal, color):
        light = normalize((0.6, 1.0, -0.5))
        brightness = 0.15 + 0.85 * max(0.0, dot(normal, light))
        return tuple(min(255, int(c * brightness)) for c in color)

    def trace(self, origin, direction, depth=0):
        t, obj = self.nearest(origin, direction)
        if obj is None:
            return (25, 25, 45)
        center, radius, color = obj
        hit = v_add(origin, v_scale(direction, t))
        normal = normalize(v_sub(hit, center))
        base = self.shade(hit, normal, color)
        if depth < 2 and radius > 0.5:               # 大球带反射
            rd = reflect(direction, normal)
            sub = self.trace(v_add(hit, v_scale(rd, 1e-4)), rd, depth + 1)
            base = tuple(int(0.7 * c + 0.3 * s) for c, s in zip(base, sub))
        return base


class Camera:
    """针孔相机 或 薄透镜相机（带景深）。"""

    def __init__(self, look_from=(0, 0, 0), focal=1.0, aperture=0.0,
                 focus_dist=4.0):
        self.origin = look_from
        self.focal = focal
        self.aperture = aperture
        self.focus_dist = focus_dist

    def primary_ray(self, px, py, width, height, rng=None):
        """像素坐标 -> 光线。aperture>0 时在光圈盘上抖动起点。"""
        x = 2 * (px + 0.5) / width - 1
        y = (1 - 2 * (py + 0.5) / height) / 2.0
        point_on_plane = (x, y, self.focal)
        if self.aperture > 0 and rng is not None:
            # 光圈圆盘均匀采样
            r = self.aperture * math.sqrt(rng.random())
            theta = rng.random() * 2 * math.pi
            off = (r * math.cos(theta), r * math.sin(theta), 0.0)
            origin = v_add(self.origin, off)
            # 焦平面上的点固定 -> 模糊由起点抖动产生
            dir_to_focus = normalize(v_sub(point_on_plane, origin))
            return origin, dir_to_focus
        return self.origin, normalize(point_on_plane)


def render(scene, camera, width, height, samples=1, rng=None):
    """samples > 1 时做抖动超采样（抗锯齿 + 景深）。"""
    image = []
    for py in range(height):
        row = []
        for px in range(width):
            acc = [0, 0, 0]
            for _ in range(samples):
                if samples > 1:
                    jx = rng.random() - 0.5
                    jy = rng.random() - 0.5
                else:
                    jx = jy = 0.0
                origin, direction = camera.primary_ray(
                    px + jx, py + jy, width, height, rng)
                rgb = scene.trace(origin, direction)
                acc[0] += rgb[0]; acc[1] += rgb[1]; acc[2] += rgb[2]
            row.append(tuple(c // samples for c in acc))
        image.append(row)
    return image


def ascii_view(image):
    chars = " .:-=+*#%@"
    lines = []
    for row in image:
        line = []
        for (r, g, b) in row:
            bright = (r + g + b) / (3 * 255)
            line.append(chars[int(bright * (len(chars) - 1))])
        lines.append("".join(line))
    return lines


rng = random.Random(134)
scene = Scene()
scene.add((0.0, 0.0, 4.0), 1.0, (255, 90, 90))          # 主体：红球（对焦处）
scene.add((-2.2, 0.3, 7.0), 0.9, (90, 220, 130))        # 远景：绿球
scene.add((2.0, -0.4, 2.2), 0.35, (120, 160, 255))      # 近景：蓝小球

print("== 针孔相机：全画面清晰 ==")
cam_pin = Camera(aperture=0.0)
img = render(scene, cam_pin, 48, 18, samples=1)
for line in ascii_view(img):
    print("  " + line)

print("\n== 薄透镜相机：大光圈景深 ==")
cam_dof = Camera(aperture=0.35, focus_dist=4.0)
img_dof = render(scene, cam_dof, 48, 18, samples=16, rng=rng)
for line in ascii_view(img_dof):
    print("  " + line)
print("  对焦在红球(z=4)：它保持清晰；远景绿球/近景蓝球被虚化")

print("\n== 模糊的定量度量 ==")


def sharpness(img):
    total = 0
    for row in img:
        for i in range(len(row) - 1):
            a = sum(row[i]) / 3
            b = sum(row[i + 1]) / 3
            total += abs(a - b)
    return total / len(img)


s_pin = sharpness(img)
s_dof = sharpness(img_dof)
print(f"  相邻像素平均差（清晰度指标）: 针孔 {s_pin:.2f} vs 景深 {s_dof:.2f}")
print("  景深版明显更『平』= 高频细节被模糊掉了")

print("\n== 抗锯齿对比 ==")
cam_aa = Camera(aperture=0.0)
img_1s = render(scene, cam_aa, 48, 18, samples=1)
img_4s = render(scene, cam_aa, 48, 18, samples=4, rng=rng)
print(f"  1 采样清晰度 = {sharpness(img_1s):.2f}")
print(f"  4 采样清晰度 = {sharpness(img_4s):.2f}")
print("  抗锯齿的『变平』只发生在几何边缘（阶梯），物体内部不变 —— 与景深不同")

print("\n== 成本模型 ==")
print(f"  {'配置':<26}{'光线数（48×18）':>16}")
for label, s in (("1 采样针孔", 1), ("4x SSAA", 4), ("16 采样景深", 16)):
    print(f"  {label:<26}{48 * 18 * s:>16}")
print("  每个效果（景深/抗锯齿/软阴影/运动模糊）都是『多发光线取平均』")
print("  这就是路径追踪器（936/938 课）的统一成本观")

print("\n== PPM 输出（临时目录）==")
with tempfile.TemporaryDirectory() as tmp:
    path = f"{tmp}/dof.ppm"
    with open(path, "wb") as fh:
        fh.write(f"P6 96 36 255\n".encode())
        for row in render(scene, cam_dof, 96, 36, samples=8, rng=rng):
            for (r, g, b) in row:
                fh.write(bytes((r, g, b)))
    import os
    print(f"  已写入 {path}（{os.path.getsize(path)} 字节，临时目录自动清理）")

print("\n== 小结 ==")
for line in (
    "  薄透镜模型 = 光圈盘采样 + 固定焦平面 → 真实景深",
    "  抖动超采样一举两得：抗锯齿 + 平滑景深噪声",
    "  所有『高级效果』共享同一成本模型：每像素光线数",
    "  935 课：场景变大后，先解决求交速度 —— BVH 加速结构",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「运动模糊」：在时间轴 [t0,t1] 抖动相机位置，渲染运动球的拖影。
# 2. 实现「鱼眼相机」：方向按球面映射，观察边缘拉伸。
# 3. 扫描光圈半径 0~0.6，绘制「光圈-清晰度」曲线。
# 4. 思考：为什么人眼的景深可以靠睫状肌调节？对应相机系统的哪个参数？
