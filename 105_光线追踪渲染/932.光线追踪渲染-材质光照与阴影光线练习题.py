# ===== 第932课：光线追踪渲染-材质光照与阴影光线 =====
# 知识点：
#   - Lambert 漫反射：亮度 ∝ max(0, n·l) —— 与光源方向的夹角
#   - 镜面高光：反射视线与光源对齐程度 ^ shininess
#   - 阴影光线：从交点向光源再发一条射线，被挡即在本影中
#   - 阴影偏移（bias）：交点沿法线抬一点，避免与自身相交（shadow acne）
#   - 光线追踪实现阴影是『顺手』的：光栅化要靠 shadow map 近似
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


def intersect_sphere(origin, direction, center, radius):
    oc = v_sub(origin, center)
    b = 2 * dot(oc, direction)
    c = dot(oc, oc) - radius * radius
    disc = b * b - 4 * c
    if disc < 0:
        return None
    sq = math.sqrt(disc)
    t1 = (-b - sq) / 2
    t2 = (-b + sq) / 2
    if t1 > 1e-4:
        return t1
    if t2 > 1e-4:
        return t2
    return None


class Scene:
    def __init__(self):
        self.spheres = []
        self.light_dir = normalize((0.6, 1.0, -0.5))
        self.ambient = 0.12

    def add_sphere(self, center, radius, color, specular=0.4, shininess=16):
        self.spheres.append({"center": center, "radius": radius,
                             "color": color, "specular": specular,
                             "shininess": shininess})

    def nearest_hit(self, origin, direction, skip=None):
        best_t, best_obj = None, None
        for obj in self.spheres:
            if obj is skip:
                continue
            t = intersect_sphere(origin, direction,
                                 obj["center"], obj["radius"])
            if t is not None and (best_t is None or t < best_t):
                best_t, best_obj = t, obj
        return best_t, best_obj

    def in_shadow(self, point):
        """阴影光线：沿光方向看有没有遮挡物。起点沿法线抬升 bias。"""
        origin = v_add(point, v_scale(self.light_dir, 1e-3))
        t, _ = self.nearest_hit(origin, self.light_dir)
        return t is not None

    def shade(self, point, normal, obj, view_dir):
        """Lambert + 镜面高光 + 阴影。"""
        color = obj["color"]
        if self.in_shadow(point):
            return tuple(int(c * self.ambient) for c in color)   # 阴影只剩环境光
        lambert = max(0.0, dot(normal, self.light_dir))
        reflected = reflect(v_scale(self.light_dir, -1), normal)
        spec_factor = max(0.0, dot(reflected, view_dir)) ** obj["shininess"]
        out = []
        for i in range(3):
            value = (self.ambient
                     + lambert * 0.75
                     + obj["specular"] * spec_factor * 0.6)
            out.append(min(255, int(color[i] * value)))
        return tuple(out)


def render_ascii(scene, width=64, height=24):
    chars = " .:-=+*#%@"
    lines = []
    for row in range(height):
        line = []
        y = (1 - 2 * (row + 0.5) / height) / 2.0
        for col in range(width):
            x = 2 * (col + 0.5) / width - 1
            direction = normalize((x, y, 1.0))
            t, obj = scene.nearest_hit((0, 0, 0), direction)
            if obj is None:
                line.append(" ")
                continue
            point = v_add((0, 0, 0), v_scale(direction, t))
            normal = normalize(v_sub(point, obj["center"]))
            rgb = scene.shade(point, normal, obj, v_scale(direction, -1))
            brightness = (rgb[0] + rgb[1] + rgb[2]) / (3 * 255)
            line.append(chars[int(brightness * (len(chars) - 1))])
        lines.append("".join(line))
    return lines


def render_ascii_no_shadow(scene, width=64, height=24):
    """对照组：跳过阴影光线。"""
    chars = " .:-=+*#%@"
    saved = scene.in_shadow
    scene.in_shadow = lambda point: False
    lines = render_ascii(scene, width, height)
    scene.in_shadow = saved
    return lines


print("== 场景：三球 + 方向光 ==")
scene = Scene()
scene.add_sphere((0.0, 0.0, 4.0), 1.0, (255, 90, 90), specular=0.5, shininess=32)
scene.add_sphere((-1.6, -0.5, 3.6), 0.8, (90, 255, 130))
scene.add_sphere((1.4, 0.3, 3.2), 0.7, (100, 150, 255))
scene.add_sphere((0.0, -6.0, 0.5), 5.6, (220, 220, 120))    # 大球当地面

print("\n== 有阴影渲染 ==")
with_shadow = render_ascii(scene)
for line in with_shadow:
    print("  " + line)

print("\n== 无阴影对照 ==")
without_shadow = render_ascii_no_shadow(scene)
for line in without_shadow:
    print("  " + line)

diff = sum(1 for a, b in zip("".join(with_shadow), "".join(without_shadow)) if a != b)
print(f"  两种渲染不同字符数 = {diff}（阴影对画面信息的贡献）")

print("\n== 阴影偏移（bias）的作用 ==")
point_on_sphere = (0.0, -1.0, 4.0)                 # 大球顶部附近
biased = v_add(point_on_sphere, v_scale(scene.light_dir, 1e-3))
print(f"  交点 {point_on_sphere}")
print(f"  抬升后的阴影光线起点 = {biased}")
print("  不抬升 → 阴影光线可能击中自身表面 → 全画面出现『 acne 』噪点")

print("\n== 高光的直观感受 ==")
spec_obj = scene.spheres[0]
sample_dir = normalize((0.15, 0.25, 1.0))
t, obj = scene.nearest_hit((0, 0, 0), sample_dir)
if obj:
    p = v_add((0, 0, 0), v_scale(sample_dir, t))
    n = normalize(v_sub(p, obj["center"]))
    rgb = scene.shade(p, n, obj, v_scale(sample_dir, -1))
    print(f"  朝高光方向的像素 RGB = {rgb}（远超本体颜色的亮度 → 高光）")

print("\n== 光照模型小结 ==")
print(f"  {'成分':<12}{'公式':<28}{'作用'}")
for row in (("环境光", "常数 × 颜色", "兜底亮度"),
            ("Lambert", "max(0, n·l)", "漫反射主体"),
            ("镜面", "(r·v)^shininess", "高光斑点"),
            ("阴影", "遮挡测试", "空间关系")):
    print(f"  {row[0]:<12}{row[1]:<28}{row[2]}")

print("\n== 小结 ==")
for line in (
    "  阴影光线是光线追踪最『划算』的效果：一次遮挡查询换真实阴影",
    "  bias 是浮点求交的必修课 —— 否则 shadow acne 满屏",
    "  光照 = 环境光 + 漫反射 + 镜面，三种成分线性叠加",
    "  933 课：递归光线 —— 反射与折射",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现点光源（有位置，方向按交点计算），观察阴影随光源位置的变化。
# 2. 实现两盏灯叠加：阴影区 = 全遮挡，半影 = 部分遮挡。
# 3. 给地面加棋盘格颜色（按交点坐标取色）。
# 4. 思考：为什么 shadow map 是『图像空间的近似』而 shadow ray 是『精确的』？
