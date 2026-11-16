# ===== 第783课：计算机图形学基础-Z缓冲与可见性 =====
# 知识点：
#   - 可见性问题：多个物体投影到同一像素，谁在前？三种经典解法
#   - 画家算法：按深度排序、从远到近画；简单但对「交叉」物体会出错
#   - Z-buffer：每像素存深度，逐像素比较，O(像素·覆盖次数)，与顺序无关
#   - Z-buffer 特点：无需排序、可任意顺序渲染，但内存大、透明物体难处理
#   - 深度精度：近处精度高远处低（透视除法后非线性），近远面比例是关键参数
#   - 本课用两个「重叠矩形」与两个交叉长方体演示三种方法差异
# 依赖：无（标准库）
import math


class ZFramebuffer:
    """颜色 + 深度双缓冲。z 越小越近（相机看向 +z）。"""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.color = [[" "]*w for _ in range(h)]
        self.depth = [[math.inf]*w for _ in range(h)]

    def plot(self, x, y, ch, z):
        if 0 <= x < self.w and 0 <= y < self.h:
            if z < self.depth[y][x]:                 # 只保留最近的
                self.depth[y][x] = z
                self.color[y][x] = ch
                return True
        return False

    def render(self):
        return "\n".join("".join(r) for r in self.color)


import math

print("== 方法 1：画家算法（按深度排序）==")
# 两个重叠的矩形：A 在前（z=2），B 在后（z=5）
painter = [[" "]*20 for _ in range(8)]
# 先画远的 B
for y in range(1, 6):
    for x in range(2, 14):
        painter[y][x] = "B"
# 再画近的 A（覆盖 B）
for y in range(3, 8):
    for x in range(9, 18):
        painter[y][x] = "A"
print("\n".join("".join(r) for r in painter))
print("  从远到近绘制，近者覆盖远者；顺序正确时结果正确")
print("  缺陷：两个长方体互相穿插时，无法用单一排序解决（需分割多边形）")

print("\n== 方法 2：Z-buffer（逐像素深度比较）==")
zb = ZFramebuffer(20, 8)
# B：z=5
for y in range(1, 6):
    for x in range(2, 14):
        zb.plot(x, y, "B", 5.0)
# A：z=2，与 B 重叠
for y in range(3, 8):
    for x in range(9, 18):
        zb.plot(x, y, "A", 2.0)
print(zb.render())
print("  重叠区 z=2 < z=5，A 胜出；结果与绘制顺序无关")
print("  再按相反顺序画一遍验证：")
zb2 = ZFramebuffer(20, 8)
for y in range(3, 8):
    for x in range(9, 18):
        zb2.plot(x, y, "A", 2.0)
for y in range(1, 6):
    for x in range(2, 14):
        zb2.plot(x, y, "B", 5.0)
print("  逆序绘制结果与正序完全一致:", zb2.render() == zb.render())

print("\n== Z-buffer 的逐像素裁决 ==")
zb3 = ZFramebuffer(12, 4)
# 同一像素被三个物体覆盖，深度分别为 1/3/2（任意顺序提交）
for ch, z in (("C", 3.0), ("A", 1.0), ("B", 2.0)):
    zb3.plot(6, 2, ch, z)
print(f"  像素 (6,2) 最终 = {zb3.color[2][6]!r}（深度 {zb3.depth[2][6]}，三者最近）")
print("  无论提交顺序如何，结果都一样 -> 天然支持多线程/乱序")

print("\n== 交叉长方体：画家算法会出错，Z-buffer 正确 ==")
# 长方体 1 沿 x，长方体 2 沿 z，互相穿插
print("  用 Z-buffer 渲染两个交叉长方体的轮廓：")
zbf = ZFramebuffer(30, 12)
for x in range(4, 26, 2):
    for y in range(4, 8):
        zbf.plot(x, y, "1", 4.0)
for x in range(10, 20, 2):
    for y in range(2, 10):
        zbf.plot(x, y, "2", 6.0)
print(zbf.render())
print("  交叉区域由每像素深度决定归属，无需排序")

print("\n== 三种方法对比 ==")
print(f"  {'方法':<14}{'排序需求':<14}{'交叉物体':<14}{'内存'}")
for row in (("画家算法", "按深度排序", "需分割多边形", "颜色缓冲"),
            ("Z-buffer", "无需排序", "天然正确", "+深度缓冲"),
            ("BSP/八叉树", "预建空间树", "部分支持", "树结构")):
    print(f"  {row[0]:<14}{row[1]:<14}{row[2]:<14}{row[3]}")

print("\n== 深度精度 ==")
for line in (
    "  透视除法后深度非线性：近处 0.99/1.0 的差异大于远处 10/20 的差异",
    "  近远面比例 (far/near) 越大，Z-fighting（深度冲突）越容易出现",
    "  缓解：减小 far/near、用对数深度缓冲、或多 pass 渲染",
    "  Z-fighting 现象：两个共面多边形闪烁/条纹",
):
    print(" ", line)

print("\n== 工程要点 ==")
for line in [
    "  透明物体不能用 Z-buffer 直接裁决，需要按从远到近排序后混合",
    "  Early-Z：先深度测试再着色，可省掉被遮挡像素的片元计算",
    "  GPU 的 depth test / depth write / depth func 都是 Z-buffer 参数",
    "  与第782课透视投影串联：投影输出的 z 就是 Z-buffer 的输入",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现「画家算法出错」的具体场景：两个交叉长方体用排序法渲染并截图对比。
# 2. 给 Z-buffer 增加深度偏移 polygon offset，缓解共面 Z-fighting。
# 3. 实现从远到近排序 + alpha 混合的透明物体渲染。
# 4. 思考：为什么透明物体不适合直接写深度缓冲？
