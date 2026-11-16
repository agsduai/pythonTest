# ===== 第784课：计算机图形学基础-光照与着色模型 =====
# 知识点：
#   - 局部光照三分量：环境光 ambient（保底）+ 漫反射 diffuse（Lambert）+ 高光 specular（Phong）
#   - Lambert: I_diff = I_L · kd · max(0, N·L)——漫反射只与「法线与光夹角」有关
#   - Phong 高光: I_spec = I_L · ks · max(0, R·V)^shininess——视角与反射方向越接近越亮
#   - Blinn-Phong：用半程向量 H=(L+V)/|L+V| 替代反射向量，更快且高光更自然
#   - 距离衰减 I ∝ 1/d²（点光源）；方向光（如太阳）无衰减
#   - 本课用 Lambert+Phong 对一个球体逐像素着色，输出 ASCII 灰度图
# 依赖：无（标准库）
import math

EPS = 1e-9


def normalize(v):
    l = math.sqrt(sum(c*c for c in v)) or 1.0
    return tuple(c/l for c in v)


def dot(a, b): return sum(x*y for x, y in zip(a, b))


def shade_phong(N, L, V, kd=0.7, ks=0.35, shininess=24, ambient=0.18, light_intensity=1.0):
    """返回 [0,1] 亮度。N/L/V 必须已归一化。"""
    N, L, V = normalize(N), normalize(L), normalize(V)
    if dot(N, L) < 0:                       # 背光面
        return ambient
    diffuse = kd * max(0.0, dot(N, L))
    # 反射方向 R = 2(N·L)N - L
    refl = tuple(2*dot(N,L)*n - l for n, l in zip(N, L))
    specular = ks * max(0.0, dot(refl, V)) ** shininess
    v = ambient + light_intensity * (diffuse + specular)
    return min(1.0, v)


def shade_blinn(N, L, V, ks=0.35, shininess=24):
    N, L, V = normalize(N), normalize(L), normalize(V)
    if dot(N, L) < 0:
        return 0.0
    H = normalize(tuple(l+v for l, v in zip(L, V)))     # 半程向量
    return ks * max(0.0, dot(N, H)) ** shininess


def render_sphere(light_dir, view_dir=(0,0,-1), w=40, h=18, radius=7.0):
    """对球面逐像素求法线并着色，输出 ASCII 灰度。"""
    GRAY = " .:-=+*#%@"                       # 10 级灰度字符
    cx, cy = w//2, h//2
    out = []
    L = normalize(light_dir); V = normalize(view_dir)
    for row in range(h):
        line = []
        for col in range(w):
            x = (col - cx) / radius
            y = -(row - cy) / (radius*2.2)     # 字符高宽比补偿
            r2 = x*x + y*y
            if r2 > 1.0:
                line.append(" "); continue
            z = math.sqrt(1 - r2)
            N = normalize((x, y, z))           # 球面法线 = 归一化位置
            bright = shade_phong(N, L, V)
            line.append(GRAY[min(9, int(bright * 9.99))])
        out.append("".join(line))
    return "\n".join(out)


print("== Lambert 漫反射：亮度只取决于 N·L ==")
L = normalize((0.6, 0.3, -0.7))
for deg in (0, 30, 45, 60, 75, 90):
    ndl = math.cos(math.radians(deg))
    print(f"  N 与 L 夹角 {deg:>2}°: N·L={ndl:.3f} -> diffuse={0.7*max(0,ndl):.3f}")
print("  夹角超过 90° 时 N·L<0，该面背光只留环境光")

print("\n== Phong 高光：R·V 的 shininess 次方 ==")
for shin in (4, 8, 16, 32, 64):
    rv = math.cos(math.radians(10))          # 视线接近反射方向
    spec = 0.35 * rv ** shin
    print(f"  shininess={shin:>3}: 偏离 10° 的高光={spec:.4f}")
print("  shininess 越大高光越锐利（集中），越小越弥散")

print("\n== Phong vs Blinn-Phong 高光 ==")
N = normalize((0,0,1)); L = normalize((0.5,0.5,-0.7)); V = (0,0,-1)
for shin in (8, 24, 64):
    print(f"  shininess={shin:>3}: Phong={shade_phong(N,L,V,ks=0.35,shininess=shin):.4f} "
          f"Blinn={shade_blinn(N,L,V,ks=0.35,shininess=shin):.4f}")
print("  Blinn-Phong 每像素少算一次反射向量，高光形状略宽")

print("\n== 球体着色（光源从右上前方）==")
print(render_sphere(light_dir=(0.6, 0.4, -0.7)))

print("\n== 光源方向对明暗的影响 ==")
print("--- 光源从左上 ---")
print(render_sphere(light_dir=(-0.6, 0.4, -0.7)))
print("--- 光源从正后方（背光剪影）---")
print(render_sphere(light_dir=(0.0, 0.0, 0.9)))

print("\n== 环境光的作用 ==")
for amb in (0.0, 0.1, 0.25):
    bright_back = shade_phong((0,0,-1), normalize((0.6,0.4,-0.7)), (0,0,-1), ambient=amb)
    print(f"  ambient={amb}: 背光面亮度={bright_back:.2f}")
print("  环境光保证背光面不是纯黑（真实环境有多次反弹）")

print("\n== 着色发生在哪个阶段 ==")
for line in (
    "  Flat shading  : 每个面一个法线/一个颜色（快、块状）",
    "  Gouraud shading: 顶点算光照，像素间插值颜色（高光会丢失）",
    "  Phong shading : 每像素插值法线再算光照（本课做法，高光正确）",
    "  逐像素 PBR    : 金属度/粗糙度/能量守恒，现代引擎标准",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  法线矩阵不能直接用模型矩阵变换（非等比缩放会破坏正交性），要用逆转置",
    "  线性颜色空间 vs sRGB：计算在线性空间，输出前做 gamma 校正",
    "  光照计算在线性空间，显示前 gamma 校正 pow(c, 1/2.2)",
    "  真实感渲染还要考虑阴影贴图、环境遮蔽、多次弹射（全局光照）",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 给球体加第二个光源，观察两个高光与明暗过渡。
# 2. 实现 Flat vs Gouraud vs Phong 三种着色的对比渲染。
# 3. 加入 gamma 校正，对比线性输出的暗部细节差异。
# 4. 思考：为什么 Gouraud 插值颜色会把高光「抹掉」，而 Phong 不会？
