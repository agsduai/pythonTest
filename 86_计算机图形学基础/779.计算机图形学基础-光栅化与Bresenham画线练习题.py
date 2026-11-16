# ===== 第779课：计算机图形学基础-光栅化与Bresenham画线 =====
# 知识点：
#   - 光栅化 rasterization：把连续几何（线/三角形）转成离散像素网格
#   - 朴素 DDA：每步 x+1、y += 斜率，四舍五入；有浮点累积误差
#   - Bresenham：只用整数加减与符号判断，无乘除/浮点，是经典画线算法
#   - 误差项 e：每步 e -= dx，e<0 时 y 步进并 e += dy（斜率 0~1 优化版）
#   - framebuffer：内存里的像素二维数组，最后一次性输出（ASCII 或图片）
#   - 与第61章 Pillow 不同：这里是「从零生成」，Pillow 是「处理已有图」
# 依赖：无（标准库）


class Framebuffer:
    """内存像素画布：字符 1B/格，便于 ASCII 输出。"""

    def __init__(self, w, h, bg=" "):
        self.w, self.h = w, h
        self.buf = [[bg]*w for _ in range(h)]

    def set(self, x, y, ch="#"):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.buf[y][x] = ch          # y 向下为正（屏幕坐标系）

    def get(self, x, y):
        return self.buf[y][x]

    def render(self):
        return "\n".join("".join(row) for row in self.buf)


def dda_line(fb, x0, y0, x1, y1):
    """朴素 DDA：浮点累加 + 四舍五入。"""
    dx, dy = x1-x0, y1-y0
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        fb.set(x0, y0); return
    xi, yi = x0, y0
    for _ in range(steps+1):
        fb.set(round(xi), round(yi))
        xi += dx/steps
        yi += dy/steps


def bresenham_line(fb, x0, y0, x1, y1):
    """Bresenham：全整数决策变量。"""
    dx, dy = abs(x1-x0), abs(y1-y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        fb.set(x, y)
        if (x, y) == (x1, y1):
            break
        e2 = 2*err
        if e2 > -dy:
            err -= dy; x += sx
        if e2 < dx:
            err += dx; y += sy


def bresenham_circle(fb, cx, cy, r):
    """中点圆算法：八分对称，只算 1/8 圆弧。"""
    x, y, err = r, 0, 1 - r
    while x >= y:
        for dx, dy in ((x,y),(y,x),(-x,y),(-y,x),(-x,-y),(-y,-x),(x,-y),(y,-x)):
            fb.set(cx+dx, cy+dy)
        y += 1
        if err < 0:
            err += 2*y + 1
        else:
            x -= 1; err += 2*(y-x) + 1


print("== Framebuffer 基础 ==")
fb = Framebuffer(24, 8)
bresenham_line(fb, 0, 6, 23, 1)
print(fb.render())

print("\n== DDA vs Bresenham：像素一致性 ==")
for x0,y0,x1,y1 in ((0,0,20,13),(2,7,30,0),(0,0,23,6)):
    f1 = Framebuffer(32,10); dda_line(f1, x0,y0,x1,y1)
    f2 = Framebuffer(32,10); bresenham_line(f2, x0,y0,x1,y1)
    same = f1.buf == f2.buf
    n1 = sum(r.count("#") for r in f1.buf)
    print(f"  ({x0},{y0})->({x1},{y1}): 像素完全一致={same} 点数={n1}")
print("  大多数直线两者相同；DDA 在长线上会因浮点累积产生 ±1 漂移")

print("\n== 中点圆算法 ==")
fb2 = Framebuffer(21, 13)
bresenham_circle(fb2, 10, 6, 5)
print(fb2.render())
print("  八分对称：只计算 1/8 圆弧，其余 7/8 镜像得到")

print("\n== 像素数与走线效率 ==")
for x1, y1 in ((100, 60), (100, 20), (100, 0)):
    fb3 = Framebuffer(120, 70)
    bresenham_line(fb3, 0, 0, x1, y1)
    n = sum(r.count("#") for r in fb3.buf)
    steps = max(x1, y1)
    print(f"  到 ({x1},{y1}): 像素数={n}（≈max(dx,dy)+1={steps+1}）")
print("  直线像素数 ≈ 长轴长度，与斜率无关")

print("\n== 为什么 Bresenham 是经典 ==")
for line in (
    "  全整数运算：1965 年为无浮点协处理器的硬件设计，至今仍用于绘图仪/打印机",
    "  每步只有加/减/比较：可微调为「中点算法」推广到圆/椭圆/任意二次曲线",
    "  增量思想：利用决策变量的单调性，避免重新计算斜率",
    "  现代 GPU 仍然用类似思想做光栅化的边缘函数判定",
):
    print(" ", line)

print("\n== 从 framebuffer 到真实图像 ==")
for line in [
    "  framebuffer -> PPM/PNG 文件（第862课综合案例）",
    "  每像素从 1 字符扩展到 RGB 三通道",
    "  反走样：超采样 2x2 或 4x4 再平均（第785课）",
    "  Pillow 可把像素数组转成图片：Image.frombytes / fromarray",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「粗线」Bresenham：线宽为 w（沿法向偏移复制）。
# 2. 实现椭圆中点算法（四分对称 + 两个区域）。
# 3. 统计 DDA 与 Bresenham 在 1000 条随机直线上的像素差异数。
# 4. 思考：为什么 Bresenham 的决策变量能用纯整数表示斜率信息？
