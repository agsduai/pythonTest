# ===== 第933课：光线追踪渲染-反射与折射 =====
# 知识点：
#   - 递归光线：交点处按材质生成新光线（反射/折射），结果加权累加
#   - 折射 = Snell 定律：n1·sinθ1 = n2·sinθ2；角度过大 → 全内反射(TIR)
#   - 玻璃球：先算折射方向，再检查是否 TIR → 反射兜底
#   - 递归深度限制：每次弹射衰减系数 < 1，深度 3~5 足够收敛
#   - 不可变设计：trace(origin, direction, depth) 纯函数式递归
# 依赖：无（标准库）
import math
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


def refract(d, n, eta):
    """Snell 折射。全内反射返回 None。
    d/n 为单位向量；eta = n1/n2（入射介质/出射介质）。"""
    cos_i = -dot(d, n)
    sin2_t = eta * eta * (1 - cos_i * cos_i)
    if sin2_t > 1.0:
        return None                             # 全内反射
    cos_t = math.sqrt(1 - sin2_t)
    return v_add(v_scale(d, eta), v_scale(n, eta * cos_i - cos_t))


class Sphere:
    def __init__(self, center, radius, material):
        self.center = center
        self.radius = radius
        self.material = material                # dict: kind/color/...

    def intersect(self, origin, direction):
        oc = v_sub(origin, self.center)
        b = 2 * dot(oc, direction)
        c = dot(oc, oc) - self.radius ** 2
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


class Tracer:
    def __init__(self, spheres, max_depth=4):
        self.spheres = spheres
        self.max_depth = max_depth
        self.stats = {"rays": 0}

    def nearest(self, origin, direction):
        best_t, best_obj = None, None
        for obj in self.spheres:
            t = obj.intersect(origin, direction)
            if t is not None and (best_t is None or t < best_t):
                best_t, best_obj = t, obj
        return best_t, best_obj

    def surface_color(self, obj, point, normal):
        """简单方向光照（无阴影，聚焦反射/折射本身）。"""
        base = obj.material["color"]
        lambert = max(0.0, dot(normal, normalize((0.5, 0.8, -0.5))))
        return tuple(min(255, int(c * (0.25 + 0.75 * lambert))) for c in base)

    def trace(self, origin, direction, depth, inside=None):
        """递归求色。inside: 当前所在介质（玻璃球或 None）。"""
        self.stats["rays"] += 1
        t, obj = self.nearest(origin, direction)
        if obj is None:
            return (30, 30, 60)                 # 背景
        hit = v_add(origin, v_scale(direction, t))
        normal = normalize(v_sub(hit, obj.center))
        if inside is obj:
            normal = v_scale(normal, -1)        # 从内部射出：法线朝内
        mat = obj.material
        kind = mat["kind"]

        if depth >= self.max_depth:
            return self.surface_color(obj, hit, normal)

        if kind == "mirror":
            rd = reflect(direction, normal)
            sub = self.trace(v_add(hit, v_scale(rd, 1e-4)), rd,
                             depth + 1, inside)
            tint = mat.get("tint", (255, 255, 255))
            return tuple(int(s * tnt / 255)
                         for s, tnt in zip(sub, tint))

        if kind == "glass":
            eta = 1.0 / 1.5 if inside is not obj else 1.5
            refr = refract(direction, normal, eta)
            if refr is None:                    # 全内反射
                rd = reflect(direction, normal)
                return self.trace(v_add(hit, v_scale(rd, 1e-4)), rd,
                                  depth + 1, inside)
            entered = obj if inside is not obj else None
            sub = self.trace(v_add(hit, v_scale(refr, 1e-4)), refr,
                             depth + 1, entered)
            base = self.surface_color(obj, hit, normal)
            return tuple(int(0.85 * s + 0.15 * b)
                         for s, b in zip(sub, base))

        # 漫反射：环境光 + Lambert，再叠一点反射（可配置）
        color = self.surface_color(obj, hit, normal)
        if mat.get("reflectivity", 0.0) > 0:
            rd = reflect(direction, normal)
            sub = self.trace(v_add(hit, v_scale(rd, 1e-4)), rd,
                             depth + 1, inside)
            k = mat["reflectivity"]
            color = tuple(int((1 - k) * c + k * s)
                          for c, s in zip(color, sub))
        return color


print("== Snell 定律与全内反射 ==")
n = (0, 1, 0)
d_in = normalize((0, -1, 1))
print(f"  入射方向 {tuple(round(x, 3) for x in d_in)}")
for eta, label in ((1 / 1.5, "空气→玻璃 η=0.67"), (1.5, "玻璃→空气 η=1.5")):
    out = refract(d_in, n, eta)
    print(f"  {label}: 折射方向 = "
          f"{tuple(round(x, 3) for x in out) if out else '全内反射!'}")
d_tir = normalize((0.9, -0.5, 0))
print(f"  掠射入射 {tuple(round(x, 3) for x in d_tir)} 玻璃→空气: "
      f"{refract(d_tir, n, 1.5)}（TIR —— 光纤的原理）")

print("\n== 场景：镜面球 + 玻璃球 + 漫反射球 ==")
spheres = [
    Sphere((0.0, 0.0, 4.0), 1.0,
           {"kind": "mirror", "color": (200, 220, 255),
            "tint": (230, 240, 255)}),
    Sphere((1.6, 0.1, 3.4), 0.7,
           {"kind": "glass", "color": (200, 230, 255)}),
    Sphere((-1.6, -0.2, 3.6), 0.8,
           {"kind": "diffuse", "color": (255, 120, 100),
            "reflectivity": 0.25}),
    Sphere((0.0, -6.2, 0.5), 5.8,
           {"kind": "diffuse", "color": (150, 170, 90),
            "reflectivity": 0.05}),
]
tracer = Tracer(spheres, max_depth=4)

print("\n== 中心像素的射线追踪 ==")
direction = normalize((0.05, -0.1, 1.0))
color = tracer.trace((0, 0, 0), direction, 0)
print(f"  d={tuple(round(x, 2) for x in direction)} -> RGB {color}")
print(f"  射线总数 = {tracer.stats['rays']}（一条像素射线的递归调用开销）")

print("\n== ASCII 渲染（48×18，亮度=RGB均值）==")
chars = " .:-=+*#%@"
for row in range(18):
    line = []
    for col in range(48):
        x = 2 * (col + 0.5) / 48 - 1
        y = (1 - 2 * (row + 0.5) / 18) / 2.0
        rgb = tracer.trace((0, 0, 0), normalize((x, y, 1.0)), 0)
        b = (rgb[0] + rgb[1] + rgb[2]) / (3 * 255)
        line.append(chars[int(b * (len(chars) - 1))])
    print("  " + "".join(line))
print(f"  渲染射线总数 = {tracer.stats['rays']}"
      f"（48×18=864 主光线 → {tracer.stats['rays'] / 864:.1f} 倍递归放大）")

print("\n== 反射的『无限走廊』实验 ==")
mirrors = [Sphere((0, 0, 3), 0.9, {"kind": "mirror",
                                   "color": (255, 255, 255),
                                   "tint": (200, 220, 255)}),
           Sphere((0, 0, -3), 0.9, {"kind": "mirror",
                                    "color": (255, 255, 255),
                                    "tint": (220, 200, 255)})]
t2 = Tracer(mirrors, max_depth=6)
color = t2.trace((0, 0, 0), (0, 0, 1), 0)
print(f"  两个对面镜球之间: 颜色 {color}")
print("  每次反弹 tint 逐级衰减 —— max_depth 保证递归终止")

print("\n== 递归成本与衰减 ==")
print(f"  {'深度':>6}{'玻璃球路径的射线数（上界）':>26}")
for d in range(1, 6):
    print(f"  {d:>6}{2 ** d:>26}")
print("  二选一（反射 or 折射）走单分支，玻璃的 tint 让深弹射自然变暗")
print("  工程上限深 4~6：视觉收益递减，成本指数级")

print("\n== 小结 ==")
for line in (
    "  递归光线 = 材质决定的新光线 + 加权合成，max_depth 保证终止",
    "  Snell + TIR 覆盖折射全部情形；法线在『内部射出』时要翻转",
    "  不可变元组 + 纯函数 trace —— 与 915 课的持久化思想一致",
    "  934 课：让相机更像真实镜头 —— 景深与抗锯齿",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现菲涅尔方程（Schlick 近似）：反射/折射按角度加权，观察玻璃边缘更反射。
# 2. 实现 Beer 定律吸收：光线在玻璃内按距离衰减颜色（彩色玻璃）。
# 3. 渲染「镜面走廊」并输出每深度的颜色衰减表。
# 4. 思考：为什么折射方向的推导必须处理『从内部射出』（eta 翻转）？漏掉会怎样？
