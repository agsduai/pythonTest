# ===== 第781课：计算机图形学基础-多边形填充与裁剪 =====
# 知识点：
#   - 扫描线填充：逐行求边交点、成对填充，比逐像素点包含快得多
#   - 顶点/水平边处理：用「半开区间」规则避免顶点被数两次
#   - Cohen-Sutherland 裁剪：9 区域编码 + 逐位裁剪，快速拒绝/接受
#   - 裁剪后线段端点用参数 t 求交，保证端点落在窗口边界上
#   - 多边形裁剪（Sutherland-Hodgman）：逐条裁剪边，输出/输入顶点入队
#   - 本课用 ASCII framebuffer 展示填充与裁剪结果
# 依赖：无（标准库）
import math


class Framebuffer:
    def __init__(self, w, h, bg=" "):
        self.w, self.h = w, h
        self.buf = [[bg]*w for _ in range(h)]
    def set(self, x, y, ch="#"):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.buf[y][x] = ch
    def render(self):
        return "\n".join("".join(r) for r in self.buf)


def scanline_fill(fb, poly, ch="#"):
    """扫描线填充：对每行 y 求与多边形边的交点 x，成对填充。"""
    ys = [p[1] for p in poly]
    y_min, y_max = min(ys), max(ys)
    n = len(poly)
    for y in range(y_min, y_max+1):
        xs = []
        for i in range(n):
            a, b = poly[i], poly[(i+1)%n]
            y0, y1 = a[1], b[1]
            if y0 == y1:
                continue                       # 水平边不产生交点
            # 半开区间：[min, max) 才计入，顶点只算一次
            if min(y0,y1) <= y < max(y0,y1):
                t = (y - y0)/(y1 - y0)
                xs.append(a[0] + t*(b[0]-a[0]))
        xs.sort()
        for k in range(0, len(xs)-1, 2):       # 成对填充
            for x in range(math.ceil(xs[k]), math.floor(xs[k+1])+1):
                fb.set(x, y, ch)



POLY = [(6,2),(18,2),(20,7),(12,11),(4,7)]

print("== 扫描线填充 ==")
fb = Framebuffer(26, 14)
scanline_fill(fb, POLY)
# 描边
for i in range(len(POLY)):
    a, b = POLY[i], POLY[(i+1)%len(POLY)]
    steps = max(abs(b[0]-a[0]), abs(b[1]-a[1]))
    for t in range(steps+1):
        x = round(a[0] + (b[0]-a[0])*t/steps)
        y = round(a[1] + (b[1]-a[1])*t/steps)
        fb.set(x, y, "O")
print(fb.render())
print("  #=填充区域 O=多边形边界")

print("\n== 与逐像素点包含的一致性 ==")
def point_in_poly(p, poly):
    x,y = p; inside=False; n=len(poly)
    for i in range(n):
        a,b = poly[i], poly[(i+1)%n]
        if (a[1]>y)!=(b[1]>y):
            xi = a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])
            if x < xi: inside = not inside
    return inside
mismatch = 0
for y in range(14):
    for x in range(26):
        filled = fb.buf[y][x] == "#"
        poly_pt = point_in_poly((x,y), POLY)
        if filled != poly_pt and fb.buf[y][x] != "O":
            mismatch += 1
print(f"  边界外不一致像素数={mismatch}（半开区间规则下应≈0，边界属于描边）")


def encode(x, y, xmin, ymin, xmax, ymax):
    code = 0
    if x < xmin: code |= 1
    if x > xmax: code |= 2
    if y < ymin: code |= 4
    if y > ymax: code |= 8
    return code


def cohen_sutherland(p, q, xmin, ymin, xmax, ymax):
    """Cohen-Sutherland 线段裁剪：返回裁剪后的两端点或 None。"""
    x1, y1 = p; x2, y2 = q
    c1, c2 = encode(x1,y1,xmin,ymin,xmax,ymax), encode(x2,y2,xmin,ymin,xmax,ymax)
    for _ in range(8):
        if c1 == 0 and c2 == 0:
            return (x1,y1),(x2,y2)             # 完全在窗口内
        if c1 & c2:
            return None                        # 完全在窗口外同一侧
        # 取至少一个在外的端点裁剪
        c_out = c1 if c1 else c2
        if c_out & 1:   y = y1 + (y2-y1)*(xmin-x1)/(x2-x1); x = xmin
        elif c_out & 2: y = y1 + (y2-y1)*(xmax-x1)/(x2-x1); x = xmax
        elif c_out & 4: x = x1 + (x2-x1)*(ymin-y1)/(y2-y1); y = ymin
        else:           x = x1 + (x2-x1)*(ymax-y1)/(y2-y1); y = ymax
        if c_out == c1: x1, y1, c1 = x, y, encode(x,y,xmin,ymin,xmax,ymax)
        else:           x2, y2, c2 = x, y, encode(x,y,xmin,ymin,xmax,ymax)
    return None


print("\n== Cohen-Sutherland 线段裁剪（窗口 8..20, 3..9）==")
XMIN, YMIN, XMAX, YMAX = 8, 3, 20, 9
fb2 = Framebuffer(26, 14)
for y in range(YMIN, YMAX+1): fb2.set(XMIN, y, "|"); fb2.set(XMAX, y, "|")
for x in range(XMIN, XMAX+1): fb2.set(x, YMIN, "-"); fb2.set(x, YMAX, "-")

LINES = [((0,0),(26,12)), ((2,6),(24,6)), ((10,1),(10,13)), ((0,0),(2,2))]
for p, q in LINES:
    r = cohen_sutherland(p, q, XMIN, YMIN, XMAX, YMAX)
    print(f"  {p}->{q} 裁剪后 = {r}")
    if r:
        (x1,y1),(x2,y2) = r
        x1,y1,x2,y2 = round(x1),round(y1),round(x2),round(y2)   # 裁剪交点是浮点
        steps = max(abs(x2-x1), abs(y2-y1))
        for t in range(steps+1):
            fb2.set(round(x1+(x2-x1)*t/steps), round(y1+(y2-y1)*t/steps), "#")
print(fb2.render())

print("\n== Sutherland-Hodgman 多边形裁剪 ==")
def clip_polygon(poly, xmin, ymin, xmax, ymax):
    def clip_edge(pts, inside, intersect):
        out = []
        n = len(pts)
        for i in range(n):
            cur, nxt = pts[i], pts[(i+1)%n]
            ci, cn = inside(cur), inside(nxt)
            if ci: out.append(cur)
            if ci != cn: out.append(intersect(cur, nxt))
        return out

    def inside_left(p): return p[0] >= xmin
    def ix_left(a,b): t=(xmin-a[0])/(b[0]-a[0]); return (a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]))
    def inside_right(p): return p[0] <= xmax
    def ix_right(a,b): t=(xmax-a[0])/(b[0]-a[0]); return (a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]))
    def inside_top(p): return p[1] >= ymin
    def ix_top(a,b): t=(ymin-a[1])/(b[1]-a[1]); return (a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]))
    def inside_bottom(p): return p[1] <= ymax
    def ix_bottom(a,b): t=(ymax-a[1])/(b[1]-a[1]); return (a[0]+t*(b[0]-a[0]), a[1]+t*(b[1]-a[1]))

    poly = clip_edge(poly, inside_left, ix_left)
    poly = clip_edge(poly, inside_right, ix_right)
    poly = clip_edge(poly, inside_top, ix_top)
    poly = clip_edge(poly, inside_bottom, ix_bottom)
    return poly

BIGPOLY = [(-4,2),(24,2),(24,12),(-4,12)]
clipped = clip_polygon(BIGPOLY, XMIN, YMIN, XMAX, YMAX)
print(f"  原多边形 {BIGPOLY} 与窗口 [{XMIN},{YMIN},{XMAX},{YMAX}] 相交")
print(f"  裁剪后 {len(clipped)} 顶点: {[(round(x,1),round(y,1)) for x,y in clipped]}")

print("\n== 扫描线填充 vs 泛洪填充 ==")
for line in (
    "  扫描线: 按行成对填充，适合凸/简单多边形，速度快",
    "  泛洪: 从种子点扩散，适合任意区域（如画图工具油漆桶）",
    "  裁剪在「先裁剪后填充」管线里能大幅减少需要处理的像素",
    "  Cohen-Sutherland 的区域编码思想可用于任何轴对齐包围盒问题",
):
    print(" ", line)

# ===== 练习题 =====
# 1. 给扫描线填充处理「自交多边形」或改用偶奇/绕数规则。
# 2. 实现 Liang-Barsky 裁剪（参数法），对比与 Cohen-Sutherland 的效率。
# 3. 把 Sutherland-Hodgman 扩展为 Weiler-Atherton（能输出多个裁剪结果多边形）。
# 4. 思考：为什么半开区间规则能避免顶点被扫描线计数两次？
