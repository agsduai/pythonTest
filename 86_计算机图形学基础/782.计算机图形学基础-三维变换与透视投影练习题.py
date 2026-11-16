# ===== 第782课：计算机图形学基础-三维变换与透视投影 =====
# 知识点：
#   - 3D 顶点用 4 分量齐次坐标 (x,y,z,1)；4x4 矩阵统一表达变换
#   - 透视投影：近大远小，x' = x·d/z（相机看向 +z，d 为焦距）
#   - 正交投影：直接丢掉 z，工程制图/CAD 用；透视投影：游戏/电影用
#   - 视图变换：先相机旋转（lookAt），再投影；深度 z 保留用于消隐
#   - 背面剔除：三角形法线朝向相机为正则可见，可先剔除一半三角形
#   - 本课手写 4x4 矩阵与透视除法，把旋转立方体投影成 ASCII 图
# 依赖：无（标准库）
import math


def mat4_mul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def apply4(M, p):
    x, y, z = p
    v = [x, y, z, 1]
    r = [sum(M[i][k]*v[k] for k in range(4)) for i in range(4)]
    return (r[0]/r[3], r[1]/r[3], r[2]/r[3])    # 透视除法 /w


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return [[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]]
def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return [[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]]
def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return [[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]]
def translate3(tx, ty, tz):
    return [[1,0,0,tx],[0,1,0,ty],[0,0,1,tz],[0,0,0,1]]


def project_persp(p, d=3.0):
    """简单针孔相机：相机在原点看向 +z，焦距 d；返回屏幕坐标 (x,y) 与深度。"""
    x, y, z = p
    if z <= 0.1:
        z = 0.1                                  # 防止除零（近裁剪面）
    return (x*d/z, y*d/z), z


def project_ortho(p):
    return (p[0], p[1], p[2])


CUBE_V = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
          (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
CUBE_E = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
          (0,4),(1,5),(2,6),(3,7)]


def render_wireframe(proj_pts, w=46, h=22, scale=14, ox=None, oy=None):
    ox = ox or w//2; oy = oy or h//2
    fb = [[" "]*w for _ in range(h)]
    pts = [(int(ox + x*scale), int(oy - y*scale)) for x, y, *_ in proj_pts]
    for i, j in CUBE_E:
        x0, y0 = pts[i]; x1, y1 = pts[j]
        steps = max(abs(x1-x0), abs(y1-y0))
        for t in range(steps+1):
            x = round(x0 + (x1-x0)*t/steps)
            y = round(y0 + (y1-y0)*t/steps)
            if 0 <= x < w and 0 <= y < h:
                fb[y][x] = "#"
    return "\n".join("".join(r) for r in fb)


def cube_view(angle_x, angle_y, distance=6.0):
    """把立方体绕 X/Y 轴旋转后平移到相机前方 distance。"""
    M = mat4_mul(translate3(0, 0, distance), mat4_mul(rot_x(angle_x), rot_y(angle_y)))
    return [apply4(M, v) for v in CUBE_V]


print("== 正交投影 vs 透视投影 ==")
view = cube_view(math.radians(25), math.radians(35))
ortho = [project_ortho(p) for p in view]
print("  正交投影（无视差，工程图）:")
print(render_wireframe(ortho))
persp = [project_persp(p)[0] for p in view]
print("\n  透视投影（近大远小，真实感）:")
print(render_wireframe(persp))

print("\n== 同一顶点的两种投影 ==")
v = view[0]
print(f"  3D 顶点 = {tuple(round(c,3) for c in v)}")
print(f"  正交 -> ({ortho[0][0]:.3f}, {ortho[0][1]:.3f})")
print(f"  透视 -> ({persp[0][0]:.3f}, {persp[0][1]:.3f})")
print("  透视除法 x*d/z 使近处顶点被放大")

print("\n== 焦距 d 对透视强度的影响 ==")
view0 = cube_view(math.radians(0), math.radians(45), distance=8)
for d in (1.0, 2.0, 4.0, 8.0):
    pp = [project_persp(p, d)[0] for p in view0]
    xs = [p[0] for p in pp]
    print(f"  d={d:>4}: 屏幕宽度={max(xs)-min(xs):>6.2f} "
          f"(近面/远面宽度比={abs(pp[1][0]-pp[0][0]) / max(abs(pp[5][0]-pp[4][0]),1e-9):.3f})")
print("  d 越小透视畸变越强（广角）；d→∞ 趋近正交")

print("\n== 深度排序（画家算法）与背面剔除 ==")
def triangle_normal(v0, v1, v2):
    ax, ay, az = (v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2])
    bx, by, bz = (v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2])
    return (ay*bz-az*by, az*bx-ax*bz, ax*by-ay*bx)

FACES = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(2,3,7,6),(1,2,6,5),(0,3,7,4)]
view_f = cube_view(math.radians(30), math.radians(40), distance=6)
visible, backface = [], 0
for f in FACES:
    v0, v1, v2, v3 = (view_f[k] for k in f)
    nx, ny, nz = triangle_normal(v0, v1, v2)
    # 相机看向 +z：法线 z 分量朝 -z（面向相机）则可见
    if nz < 0:
        visible.append(f)
    else:
        backface += 1
print(f"  立方体 6 个面: 可见 {len(visible)} 个, 背面剔除 {backface} 个")
print("  背面剔除在光栅化前丢弃一半三角形，是性能优化的第一步")

print("\n== 透视除法与近裁剪面 ==")
for z in (10.0, 5.0, 2.0, 1.0, 0.5):
    p = ((1.0)*3.0/z, (1.0)*3.0/z, z)
    print(f"  顶点 z={z:>5}: 屏幕坐标=({p[0]:.3f},{p[1]:.3f})")
print("  z 越小屏幕坐标越大（近大远小）；z→0 发散，需要近裁剪面保护")

print("\n== 管线顺序 ==")
for line in (
    "  顶点 -> 模型变换(物体的姿态) -> 视图变换(相机) -> 投影变换 -> 裁剪 -> 视口变换",
    "  本课把模型/视图合并成一个 4x4 矩阵，投影单独做透视除法",
    "  真实 GPU 用 MVP 一次矩阵乘法 + 固定的裁剪/视口阶段",
    "  深度值保存在投影输出里供 Z-buffer 消隐（第783课）",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 实现 lookAt(eye, target, up) 视图矩阵，把相机放到任意位置。
# 2. 加入近/远裁剪面与视口映射，输出标准化的 NDC 坐标。
# 3. 渲染旋转动画：angle 从 0° 到 90° 每 10° 一帧，观察近大远小。
# 4. 思考：为什么透视除法必须在裁剪之后、且不能对 w<=0 的点做？
