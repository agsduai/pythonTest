# ===== 第785课：计算机图形学基础-贝塞尔曲线与反走样 =====
# 知识点：
#   - 参数曲线：P(t) 用参数 t∈[0,1] 描述点集，比显式 y=f(x) 更适合图形
#   - Bézier：线性(两点)/二次(控制点 3)/三次(控制点 4)，Bernstein 基加权
#   - de Casteljau 算法：递归线性插值求 Bézier 上任意点，数值稳定
#   - 凸包性质：曲线始终在控制点凸包内 -> 天然可控、安全
#   - 反走样：走样来自「像素只有开/关」；超采样 SSAA（N×N 子像素平均）最简单有效
#   - 覆盖率估计：对像素四角/中心采样，或计算几何覆盖比例（第758课）
# 依赖：无（标准库）
import math


def bernstein(n, i, t):
    return math.comb(n, i) * (1-t)**(n-i) * t**i


def bezier_point(ctrl, t):
    """de Casteljau 递归求 Bézier 曲线上的点。"""
    pts = [tuple(p) for p in ctrl]
    while len(pts) > 1:
        pts = [((1-t)*a[0] + t*b[0], (1-t)*a[1] + t*b[1])
               for a, b in zip(pts, pts[1:])]
    return pts[0]


def bezier_polyline(ctrl, n=64):
    return [bezier_point(ctrl, i/n) for i in range(n+1)]


class FB:
    def __init__(self, w, h, bg=" "):
        self.w, self.h = w, h
        self.buf = [[bg]*w for _ in range(h)]
    def set(self, x, y, ch="#"):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.buf[y][x] = ch
    def render(self): return "\n".join("".join(r) for r in self.buf)


def draw_polyline(fb, pts):
    for i in range(len(pts)-1):
        x0,y0 = pts[i]; x1,y1 = pts[i+1]
        steps = int(max(abs(x1-x0), abs(y1-y0))*2) or 1
        for t in range(steps+1):
            x = round(x0+(x1-x0)*t/steps); y = round(y0+(y1-y0)*t/steps)
            fb.set(x, y)


print("== Bézier 曲线 ==")
CTRL = [(2,10),(8,1),(16,12),(24,3)]       # 三次：4 个控制点
print(f"  控制点: {CTRL}")
poly = bezier_polyline(CTRL, n=48)
fb = FB(28, 14)
for c in CTRL: fb.set(*c, "O")              # 控制点标 O
draw_polyline(fb, poly)
# 控制多边形（虚线感用 .）
for i in range(len(CTRL)-1):
    x0,y0 = CTRL[i]; x1,y1 = CTRL[i+1]
    for t in range(8):
        x = round(x0+(x1-x0)*t/8); y = round(y0+(y1-y0)*t/8)
        if fb.buf[y][x] == " ": fb.set(x, y, ".")
print(fb.render())
print("  O=控制点 .=控制多边形 #=曲线（始终在控制点凸包内）")

print("\n== de Casteljau 的几何意义 ==")
ctrl = [(0,0),(4,8),(10,2)]
for t in (0.0, 0.25, 0.5, 0.75, 1.0):
    a = [((1-t)*p0[0]+t*p1[0], (1-t)*p0[1]+t*p1[1]) for p0,p1 in zip(ctrl,ctrl[1:])]
    b = ((1-t)*a[0][0]+t*a[1][0], (1-t)*a[0][1]+t*a[1][1])
    print(f"  t={t:.2f}: 第一层={[(round(x,2),round(y,2)) for x,y in a]} -> 点={tuple(round(v,3) for v in b)}")
print("  每层都是「在相邻控制点连线上按 t 插值」，两层后得到曲线点")

print("\n== 升阶与凸包性质 ==")
for ctrl in ([(2,10),(8,1),(16,12),(24,3)],
             [(2,10),(8,12),(16,1),(24,3)],
             [(2,10),(2,12),(24,12),(24,3)]):
    curve = bezier_polyline(ctrl, n=64)
    # 曲线是否在控制点凸包内（用第756课凸包 + 第758课点包含粗验）
    pts = ctrl + [p for p in curve]
    inside = all(min(p[0] for p in ctrl)-1 <= p[0] <= max(p[0] for p in ctrl)+1 and
                 min(p[1] for p in ctrl)-1 <= p[1] <= max(p[1] for p in ctrl)+1
                 for p in curve)
    print(f"  控制点={ctrl} 曲线均在包围盒内={inside}")

print("\n== 走样：1 bit 像素的锯齿 ==")
def diagonal(fb, w=30, h=14):
    for x in range(w):
        y = round((h-2) * x / (w-1))
        fb.set(x, y)
fb1 = FB(30, 14); diagonal(fb1)
print("  无抗锯齿（硬边 #）:")
print(fb1.render())

print("\n== 超采样 SSAA：2x2 子像素平均 ==")
def draw_supersampled(fb, w, h, ss=2):
    """对每个终端像素取 ss×ss 个子样本，按覆盖率选灰度字符。"""
    GRAY = " ░▒▓█"
    W, H = w, h
    cov = [[0]*W for _ in range(H)]
    for py in range(H*ss):
        for px in range(W*ss):
            # 直线 y = (h-2)*x/(w-1)，判定子像素中心是否在线附近
            x = (px + 0.5)/ss; y = (py + 0.5)/ss
            ideal = (H-2) * x / (W-1)
            if abs(y - ideal) < 0.75:
                cov[int(py/ss)][int(px/ss)] += 1    # cov[行y][列x]
    for y in range(H):
        for x in range(W):
            c = cov[y][x] / (ss*ss)
            if c > 0:
                fb.set(x, y, GRAY[min(4, int(c*4.99))])

fb2 = FB(30, 14)
draw_supersampled(fb2, 30, 14, ss=3)
print("  3×3 超采样（边缘用灰度渐变）:")
print(fb2.render())
print("  边缘出现中间灰度，人眼感觉线条更平滑，代价是 ss² 倍采样量")

print("\n== 覆盖率与灰度级的量化 ==")
for cov in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
    idx = min(4, int(cov*4.99))
    print(f"  覆盖率={cov:.2f} -> 字符级 {idx}/4")
print("  5 级灰度有限；真实抗锯齿用 8bit/通道 alpha 混合")

print("\n== 抗锯齿方法对比 ==")
print(f"  {'方法':<16}{'质量':<10}{'成本':<14}{'典型'}")
for row in (("无 AA", "锯齿明显", "1×", "像素艺术"),
            ("SSAA 超采样", "最好", "ss² 倍渲染", "离线/影视"),
            ("MSAA", "仅边缘好", "4~8×(分摊)", "游戏 GPU 标准"),
            ("FXAA/TAA", "整体柔化", "≈1×", "实时渲染")):
    print(f"  {row[0]:<16}{row[1]:<10}{row[2]:<14}{row[3]}")

print("\n== Bézier 的应用 ==")
for line in (
    "  字体轮廓：TrueType 用二次、OpenType/CFF 用三次 Bézier",
    "  UI 动画缓动曲线、CSS cubic-bezier()",
    "  矢量绘图工具的钢笔工具（Path 直接对应控制点）",
    "  与第780课变换矩阵结合：控制点先变换，曲线跟着变换",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  de Casteljau 数值稳定；直接用 Bernstein 公式在大 n 时会溢出",
    "  高阶 Bézier 控制点多了不直观，工程上用多段三次曲线拼接（C1/C2 连续）",
    "  曲线细分到像素级可用自适应平坦度判据（弦高 < 0.5px 停止细分）",
    "  字体渲染还要提示 hinting 与 gamma 校正的灰度抗锯齿",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 Bézier 的升阶（把 n 次曲线精确表示成 n+1 次控制点）。
# 2. 给 Bresenham 画线加 2×2 超采样灰度，对比硬边版本。
# 3. 用自适应平坦度细分渲染一条高曲率三次曲线。
# 4. 思考：为什么 Bézier 曲线一定落在控制点的凸包内？
