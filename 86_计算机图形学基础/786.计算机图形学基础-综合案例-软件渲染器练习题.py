# ===== 第786课：计算机图形学基础-综合案例-软件渲染器 =====
# 知识点：
#   - 综合串起本章：变换 -> 透视投影 -> 三角形光栅化 -> Z-buffer -> Lambert 光照 -> 输出 PPM
#   - 渲染管线：顶点(模型+视图矩阵) -> 投影 -> 视口映射 -> 光栅化(重心坐标) -> 像素着色
#   - 重心坐标：把三角形内点表示为三个顶点的加权组合，用于插值深度与法线
#   - 逐像素：Z-buffer 深度测试 + 顶点法线插值 + Lambert 光照（第783/784课）
#   - 输出：PPM(P6 二进制) 是最简单的无压缩图像格式，可直接转 PNG 验证
#   - 全部标准库 + 临时目录 + 固定 seed，离线可运行
# 依赖：无（标准库）
import math
import random
import tempfile
from pathlib import Path


def normalize(v):
    l = math.sqrt(sum(c*c for c in v)) or 1.0
    return tuple(c/l for c in v)

def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def mul(a,k): return tuple(x*k for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def mat4_mul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]

def apply4(M, p):
    x,y,z = p
    v = [x,y,z,1]
    r = [sum(M[i][k]*v[k] for k in range(4)) for i in range(4)]
    return (r[0]/r[3], r[1]/r[3], r[2]/r[3])

def rot_y(a):
    c,s = math.cos(a), math.sin(a)
    return [[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
def rot_x(a):
    c,s = math.cos(a), math.sin(a)
    return [[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]]
def translate3(tx,ty,tz):
    return [[1,0,0,tx],[0,1,0,ty],[0,0,1,tz],[0,0,0,1]]


# ---------- 简单几何：立方体 + 地面 ----------
CUBE_V = [(-0.8,-0.8,-0.8),(0.8,-0.8,-0.8),(0.8,0.8,-0.8),(-0.8,0.8,-0.8),
          (-0.8,-0.8,0.8),(0.8,-0.8,0.8),(0.8,0.8,0.8),(-0.8,0.8,0.8)]
CUBE_F = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(0,3,7,4)]
GROUND_V = [(-4,-1.0,-4),(4,-1.0,-4),(4,-1.0,4),(-4,-1.0,4)]
GROUND_F = [(0,1,2,3)]


def quad_to_tris(f):
    return (f[0],f[1],f[2]), (f[0],f[2],f[3])


def view_transform(vertices, ax, ay, dist=5.0):
    M = mat4_mul(translate3(0,0,dist), mat4_mul(rot_x(ax), rot_y(ay)))
    return [apply4(M, v) for v in vertices]


def project(p, w, h, fov_scale=1.6):
    x, y, z = p
    z = max(z, 0.05)
    sx = (x*fov_scale/z*0.5 + 0.5) * w
    sy = (1.0 - (y*fov_scale/z*0.5 + 0.5)) * h
    return sx, sy, z


def raster_triangle(fb, depth, v0, v1, v2, normals, color, light):
    """光栅化一个屏幕三角形：重心坐标插值深度与法线，Lambert 着色。"""
    fh, fw = len(fb), len(fb[0])
    xs = [v[0] for v in (v0,v1,v2)]; ys = [v[1] for v in (v0,v1,v2)]
    x0, x1 = max(0, math.floor(min(xs))), min(fw-1, math.ceil(max(xs)))
    y0, y1 = max(0, math.floor(min(ys))), min(fh-1, math.ceil(max(ys)))
    # 屏幕空间叉积的有向面积
    area = (v1[0]-v0[0])*(v2[1]-v0[1]) - (v1[1]-v0[1])*(v2[0]-v0[0])
    if abs(area) < 1e-9:
        return 0
    N = normalize(normals)
    L = normalize((0.5, 0.8, -0.6))
    intensity = max(0.15, dot(N, L))
    drawn = 0
    for py in range(y0, y1+1):
        for px in range(x0, x1+1):
            cx, cy = px+0.5, py+0.5
            w0 = ((v1[0]-cx)*(v2[1]-cy) - (v1[1]-cy)*(v2[0]-cx)) / area
            w1 = ((v2[0]-cx)*(v0[1]-cy) - (v2[1]-cy)*(v0[0]-cx)) / area
            w2 = 1 - w0 - w1
            if w0 < -1e-6 or w1 < -1e-6 or w2 < -1e-6:
                continue
            z = w0*v0[2] + w1*v1[2] + w2*v2[2]
            if z < depth[py][px]:
                depth[py][px] = z
                shade = min(1.0, max(0.0, intensity)) * color
                r = int(60 + 180*shade)
                g = int(60 + 150*shade)
                b = int(80 + 120*shade)
                fb[py][px] = (r, g, b)
                drawn += 1
    return drawn


def write_ppm(path, fb):
    """P6 二进制 PPM：最简单的无压缩图像格式。"""
    h, w = len(fb), len(fb[0])
    data = bytearray()
    for row in fb:
        for (r,g,b) in row:
            data += bytes((max(0,min(255,r)), max(0,min(255,g)), max(0,min(255,b))))
    with path.open("wb") as f:
        f.write(f"P6\n{w} {h}\n255\n".encode("ascii"))
        f.write(bytes(data))


def ascii_preview(fb, cols=52, rows=16):
    """把 RGB framebuffer 缩成 ASCII 亮度预览。"""
    GRAY = " .:-=+*#%@"
    h, w = len(fb), len(fb[0])
    out = []
    for ry in range(rows):
        line = []
        for rx in range(cols):
            x0, x1 = int(rx*w/cols), int((rx+1)*w/cols)
            y0, y1 = int(ry*h/rows), int((ry+1)*h/rows)
            v = sum(sum(fb[y][x]) for y in range(y0,y1) for x in range(x0,x1))
            n = max(1,(x1-x0)*(y1-y0))
            line.append(GRAY[min(9, int(v/n/255*9.99))])
        out.append("".join(line))
    return "\n".join(out)


print("== 场景：旋转的立方体 + 地面 ==")
ax, ay = math.radians(28), math.radians(35)
cube_v = view_transform(CUBE_V, ax, ay)
ground_v = view_transform(GROUND_V, ax, ay)
print(f"  立方体 8 顶点 + 地面 4 顶点，相机距离 5")

W, H = 160, 90
fb = [[(18,20,28)]*W for _ in range(H)]
depth = [[math.inf]*W for _ in range(H)]
light = normalize((0.5, 0.8, -0.6))

print("\n== 光栅化 ==")
tris_drawn = px_total = 0
for f in CUBE_F:
    for t in quad_to_tris(f):
        vs = [project(cube_v[k], W, H) for k in t]
        n = normalize(cross(sub(cube_v[t[1]],cube_v[t[0]]), sub(cube_v[t[2]],cube_v[t[0]])))
        # 背面剔除：法线朝向相机(负 z 方向)才画
        if n[2] > 0:
            continue
        px_total += raster_triangle(fb, depth, *vs, n, 0.9, light)
        tris_drawn += 1
for t in quad_to_tris(GROUND_F[0]):
    vs = [project(ground_v[k], W, H) for k in t]
    px_total += raster_triangle(fb, depth, *vs, (0,1,0), 0.5, light)
    tris_drawn += 1
print(f"  绘制三角形 {tris_drawn} 个（背面剔除后），填充像素 {px_total} 个")
print(f"  帧缓冲 {W}x{H}，覆盖 {px_total/(W*H):.1%}")

print("\n== ASCII 预览 ==")
print(ascii_preview(fb))

print("\n== 输出 PPM 并验证 ==")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "render.ppm"
    write_ppm(p, fb)
    raw = p.read_bytes()
    header = raw[:20].split(b"\n")[:3]
    print(f"  {p.name}: {p.stat().st_size} 字节 = 15B 头 + {W*H*3} 像素数据")
    print(f"  PPM 头: {b' | '.join(header)!r}")
    print(f"  文件头+数据长度一致: {len(raw) == 15 + W*H*3}")
    print("  P6 格式可被 Pillow/PIL/ImageMagick 直接打开转 PNG")

print("\n== 渲染管线回顾 ==")
for line in [
    "  变换    : 4x4 齐次矩阵旋转+平移（第780/782课）",
    "  投影    : 透视除法得到屏幕坐标与深度（第782课）",
    "  背面剔除: 三角形法线朝向检查（第782课）",
    "  光栅化  : 重心坐标判定像素归属（第779/781课）",
    "  可见性  : Z-buffer 逐像素深度测试（第783课）",
    "  着色    : Lambert 漫反射（第784课）",
    "  输出    : framebuffer -> PPM 文件 -> ASCII 预览",
]:
    print("  -", line)

print("\n== 与真实渲染器的差距 ==")
for line in [
    "  无纹理映射、阴影贴图、抗锯齿（第785课）、环境光遮蔽",
    "  只画了线框级几何 + 简单颜色，无材质/反射/全局光照",
    "  光栅化用逐像素重心坐标，GPU 用边界函数 + 分块并行",
    "  目标是把本章组件串成一条从顶点到图像文件的完整管线",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 把 framebuffer 用 Pillow 转成 PNG，肉眼检查渲染结果。
# 2. 给立方体各面不同颜色，并实现 Blinn-Phong 高光（第784课）。
# 3. 加入 2×2 超采样抗锯齿，对比边缘质量（第785课）。
# 4. 思考：为什么重心坐标插值需要做透视校正（透视除法在插值之前还是之后）？
