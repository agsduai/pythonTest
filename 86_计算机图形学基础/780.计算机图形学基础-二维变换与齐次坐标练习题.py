# ===== 第780课：计算机图形学基础-二维变换与齐次坐标 =====
# 知识点：
#   - 平移不是线性变换，无法用 2x2 矩阵表示 -> 引入齐次坐标 (x, y, 1)
#   - 3x3 齐次矩阵统一表示：平移/旋转/缩放/错切，复合只需矩阵乘法
#   - 矩阵从左到右依次作用（列向量约定）：M3·M2·M1·p
#   - 旋转矩阵绕原点转；绕任意点 = 平移到原点 -> 旋转 -> 平移回去
#   - 变换顺序不可交换：先平移后旋转 ≠ 先旋转后平移
#   - 本课手写 3x3 矩阵乘法，全部标准库，用 ASCII 渲染验证
# 依赖：无（标准库）
import math


def mat_mul(A, B):
    return [[sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def apply(M, p):
    x, y = p
    v = [x, y, 1]
    r = [sum(M[i][k]*v[k] for k in range(3)) for i in range(3)]
    return (r[0]/r[2], r[1]/r[2])           # 齐次除法


def translate(tx, ty):
    return [[1,0,tx],[0,1,ty],[0,0,1]]
def rotate(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return [[c,-s,0],[s,c,0],[0,0,1]]
def scale(sx, sy):
    return [[sx,0,0],[0,sy,0],[0,0,1]]
def shear(kx, ky):
    return [[1,kx,0],[ky,1,0],[0,0,1]]


def transform_shape(M, shape):
    return [apply(M, p) for p in shape]


def render(points, w=40, h=14, origin=(2,12), scale=1.0):
    """把几何坐标画到 ASCII 画布（y 翻转成屏幕方向）。"""
    fb = [[" "]*w for _ in range(h)]
    ox, oy = origin
    for i in range(len(points)):
        x, y = points[i]
        px, py = int(round(ox + x*scale)), int(round(oy - y*scale))
        if 0 <= px < w and 0 <= py < h:
            fb[py][px] = "#"
        # 连线到下一个点
        nx, ny = points[(i+1) % len(points)]
        steps = int(max(abs(nx-x), abs(ny-y)) * scale) or 1
        for t in range(1, steps):
            xx, yy = x + (nx-x)*t/steps, y + (ny-y)*t/steps
            px, py = int(round(ox + xx*scale)), int(round(oy - yy*scale))
            if 0 <= px < w and 0 <= py < h:
                fb[py][px] = "#"
    return "\n".join("".join(row) for row in fb)


SQUARE = [(4,4),(8,4),(8,8),(4,8)]

print("== 原始正方形 ==")
print(render(SQUARE))

print("\n== 平移 (10, 3) ==")
print(render(transform_shape(translate(10,3), SQUARE)))

print("\n== 绕原点旋转 45° ==")
print(render(transform_shape(rotate(45), SQUARE)))

print("\n== 缩放 1.5× ==")
print(render(transform_shape(scale(1.5,1.5), SQUARE)))

print("\n== 复合变换：先绕原点转 30°，再平移 (12,2) ==")
M = mat_mul(translate(12,2), rotate(30))     # 注意顺序：右边的先作用
print(render(transform_shape(M, SQUARE)))

print("\n== 顺序不可交换 ==")
p = (4, 4)
M1 = mat_mul(translate(5,0), rotate(90))     # 先转后平移
M2 = mat_mul(rotate(90), translate(5,0))     # 先平移后转
print(f"  p={p}")
print(f"  平移∘旋转 = {tuple(round(v,3) for v in apply(M1, p))}")
print(f"  旋转∘平移 = {tuple(round(v,3) for v in apply(M2, p))}")
print("  矩阵乘法不满足交换律 -> 顺序不同结果不同")

print("\n== 绕任意点旋转：T(-c)·R·T(c) ==")
def rotate_around(cx, cy, deg):
    return mat_mul(translate(cx, cy), mat_mul(rotate(deg), translate(-cx, -cy)))
M3 = rotate_around(8, 8, 45)                 # 绕正方形右上角转
print(render(transform_shape(M3, SQUARE)))
print("  右上角 (8,8) 旋转后仍在 (8,8) 附近，整个形状绕它转动")

print("\n== 齐次坐标的意义 ==")
for line in (
    "  2D 仿射变换 = 3x3 矩阵；最后加 [0,0,1] 行让平移也能写成矩阵",
    "  w 分量非 1 时表示投影前的空间（3D 透视除法用同一套机制）",
    "  变换链 M_total = M_n·...·M_1 可预计算，几何体只需一次乘法",
    "  GPU 顶点着色器就是把几千个顶点各乘一次同一 M_total",
):
    print(" ", line)

print("\n== 逆变换 ==")
print("  平移的逆 = translate(-tx,-ty)；旋转的逆 = rotate(-θ)；缩放的逆 = scale(1/s)")
M = mat_mul(translate(5, 3), rotate(45))
Minv = mat_mul(rotate(-45), translate(-5, -3))   # 逆序 + 逆操作
p = (4, 4)
back = apply(Minv, apply(M, p))
print(f"  p={p} -> 变换{tuple(round(v,3) for v in apply(M,p))} -> 逆变换={tuple(round(v,4) for v in back)}")
print("  逆序使用逆操作即可还原（合成函数的逆 = 逆的逆序合成）")

# ===== 练习题 =====
# 1. 实现 3x3 矩阵求逆（伴随/高斯消元），支持任意仿射变换的逆。
# 2. 实现「绕任意点缩放」，并验证不动点确实是缩放中心。
# 3. 用变换矩阵做动画：旋转角从 0° 到 90° 每 10° 渲染一帧。
# 4. 思考：为什么齐次坐标能让平移也变成矩阵乘法？w 分量何时非 1？
