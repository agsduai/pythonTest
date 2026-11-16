# ===== 第931课：光线追踪渲染-光线与球体相交 =====
# 知识点：
#   - 光线追踪：从相机向每个像素发射光线，找最近交点 —— 与 86 章光栅化互补
#   - 光线 = 起点 + 方向；球体相交 = 解二次方程 |o + t·d − c|² = r²
#   - 取最小正 t 作为可见表面 —— 天然解决遮挡（无需 Z-buffer）
#   - 本课用 ASCII 字符渲染亮度（更高级的效果见后续课程）
#   - 纯 Python 模拟：小分辨率 + 字符输出，重点在算法而非性能
# 依赖：无（标准库）
import math
import tempfile


# ---------- 三维向量工具（元组实现，保持不可变） ----------
def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v_scale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def length(a):
    return math.sqrt(dot(a, a))


def normalize(a):
    n = length(a)
    return (a[0] / n, a[1] / n, a[2] / n)


def reflect(d, n):
    """反射方向：d − 2(d·n)n。"""
    return v_sub(d, v_scale(n, 2 * dot(d, n)))


# ---------- 几何体 ----------
def intersect_sphere(origin, direction, center, radius):
    """返回最近正交点距离 t，未命中返回 None。"""
    oc = v_sub(origin, center)
    b = 2 * dot(oc, direction)
    c = dot(oc, oc) - radius * radius
    disc = b * b - 4 * c                       # direction 已归一化
    if disc < 0:
        return None
    sq = math.sqrt(disc)
    t1 = (-b - sq) / 2
    t2 = (-b + sq) / 2
    if t1 > 1e-6:
        return t1
    if t2 > 1e-6:
        return t2                              # 从球内部射出
    return None


def sphere_normal(point, center):
    return normalize(v_sub(point, center))


class Scene:
    def __init__(self):
        self.spheres = []                      # (center, radius, color)

    def add_sphere(self, center, radius, color):
        self.spheres.append((center, radius, color))

    def nearest_hit(self, origin, direction):
        best_t, best_obj = None, None
        for center, radius, color in self.spheres:
            t = intersect_sphere(origin, direction, center, radius)
            if t is not None and (best_t is None or t < best_t):
                best_t, best_obj = t, (center, radius, color)
        return best_t, best_obj


# ---------- 相机与渲染 ----------
def render_ascii(scene, width=64, height=24):
    """主光线投射：亮度 = 与球心的法向对齐程度。"""
    chars = " .:-=+*#%@"
    aspect = 2.0                              # 字符宽高比补偿
    out_lines = []
    for row in range(height):
        line = []
        y = (1 - 2 * (row + 0.5) / height) / aspect
        for col in range(width):
            x = (2 * (col + 0.5) / width - 1)
            direction = normalize((x, y, 1.0))        # 相机在原点看向 +z
            t, obj = scene.nearest_hit((0, 0, 0), direction)
            if obj is None:
                line.append(" ")
                continue
            center, radius, color = obj
            point = v_add((0, 0, 0), v_scale(direction, t))
            n = sphere_normal(point, center)
            brightness = 0.15 + 0.85 * max(0.0, dot(n, normalize((0.5, 0.8, -0.6))))
            level = int(brightness * (len(chars) - 1))
            line.append(chars[level])
        out_lines.append("".join(line))
    return out_lines


def render_ppm(scene, width, height, path):
    """输出 PPM 文件（86 章同款格式）。"""
    with open(path, "wb") as fh:
        fh.write(f"P6 {width} {height} 255\n".encode())
        for row in range(height):
            for col in range(width):
                y = (1 - 2 * (row + 0.5) / height) / 2.0
                x = 2 * (col + 0.5) / width - 1
                direction = normalize((x, y, 1.0))
                t, obj = scene.nearest_hit((0, 0, 0), direction)
                if obj is None:
                    fh.write(bytes((20, 20, 40)))
                    continue
                center, radius, color = obj
                point = v_add((0, 0, 0), v_scale(direction, t))
                n = sphere_normal(point, center)
                brightness = 0.15 + 0.85 * max(0.0, dot(n, normalize((0.5, 0.8, -0.6))))
                fh.write(bytes(min(255, int(c * brightness)) for c in color))


print("== 手工验证：光线-球体相交 ==")
t = intersect_sphere((0, 0, 0), (0, 0, 1), (0, 0, 5), 1.0)
print(f"  光线 |o=(0,0,0), d=(0,0,1)⟩ vs 球心(0,0,5) r=1: t = {t:.4f}（应为 4.0）")
t_miss = intersect_sphere((0, 0, 0), (0, 1, 0), (0, 0, 5), 1.0)
print(f"  平行擦过的光线: t = {t_miss}（应为 None）")
t_inside = intersect_sphere((0, 0, 5), (0, 0, 1), (0, 0, 5), 1.0)
print(f"  从球心射出: t = {t_inside:.4f}（应为半径 1.0，取远交点）")

print("\n== 场景：三个球 ==")
scene = Scene()
scene.add_sphere((0.0, 0.0, 4.0), 1.0, (255, 80, 80))       # 红
scene.add_sphere((-1.6, -0.4, 3.6), 0.8, (80, 255, 120))    # 绿
scene.add_sphere((1.4, 0.3, 3.2), 0.7, (90, 140, 255))      # 蓝
print(f"  球体数 = {len(scene.spheres)}")

print("\n== ASCII 渲染（64×24）==")
for line in render_ascii(scene):
    print("  " + line)

print("\n== PPM 输出（写入临时目录）==")
with tempfile.TemporaryDirectory() as tmp:
    path = f"{tmp}/raytraced.ppm"
    render_ppm(scene, 160, 90, path)
    import os
    print(f"  已写入 {path}（{os.path.getsize(path)} 字节，已随临时目录清理）")
print("  用查看器打开 PPM 即可看到彩色渲染结果")

print("\n== 光线追踪 vs 光栅化（86 章）==")
for line in (
    "  光栅化：把三角形投到屏幕上画出来 —— 快，适合实时游戏",
    "  光线追踪：每个像素反问『什么东西在这条视线』—— 慢，物理正确",
    "  遮挡：光栅化要 Z-buffer 排序；光线追踪取最近 t 天然正确",
    "  反射/折射/软阴影：光线递归即可，光栅化要靠贴图/预计算骗出来",
):
    print("  -", line)

print("\n== 小结 ==")
for line in (
    "  光线-球体相交 = 二次方程；取最小正 t 是可见性判定的全部",
    "  场景类封装 nearest_hit —— 后续光照/反射都在它之上",
    "  ASCII 渲染让算法过程可见：亮度来自法线与光照方向的夹角",
    "  932 课：加材质与光照（Lambert/镜面/阴影）",
):
    print("  -", line)

# ===== 练习题 =====
# 1. 实现光线-平面相交（地面 y=-2），渲染出『球悬浮在地面』的场景。
# 2. 实现 A/B 包围盒预测试：先查包围盒再查球，统计跳过的球体数。
# 3. 把相机拉远/改变视场角，观察球体透视变化。
# 4. 思考：为什么光线追踪天然支持透明与反射，而光栅化难以做到？
