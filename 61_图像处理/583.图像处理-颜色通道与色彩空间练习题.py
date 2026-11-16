# ===== 第583课：图像处理-颜色通道与色彩空间 =====
# 知识点：
#   - RGB：红绿蓝三个通道；split 分离，merge 合并
#   - getchannel("R") 单独取通道；putalpha 设置透明度
#   - 灰度 L：亮度；convert("L") 按加权公式
#   - HSV：色相/饱和度/明度，适合按颜色筛选
#   - point 查找表：批量映射像素值（反色、阈值）
#   - histogram：各亮度级像素数，可判断曝光
#   - 与第27章 NumPy 的配合：图像就是三维数组（H×W×C）
# 依赖：pip install pillow numpy

import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    img = Image.new("RGB", (300, 200), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 100, 200], fill=(220, 50, 50))
    draw.rectangle([100, 0, 200, 200], fill=(50, 180, 80))
    draw.rectangle([200, 0, 300, 200], fill=(50, 80, 220))
    img.save(tmp / "rgb.png")

    # ---- 分离与合并 ----
    r, g, b = img.split()
    print("== 分离通道 ==")
    for name, ch in (("R", r), ("G", g), ("B", b)):
        print(f"  {name}: mode={ch.mode}, 极值={ch.getextrema()}")
        ch.save(tmp / f"channel_{name}.png")

    merged = Image.merge("RGB", (b, r, g))       # 交换通道
    merged.save(tmp / "swapped.png")
    print("  通道交换（R←B, G←R, B←G）：已保存")

    # ---- 单独增强某通道 ----
    arr = np.array(img).astype(np.float32)
    arr[..., 0] = np.clip(arr[..., 0] * 1.4, 0, 255)
    red_boost = Image.fromarray(arr.astype(np.uint8))
    red_boost.save(tmp / "red_boost.png")
    print("\n== 单通道增强 ==")
    print("  红色通道 ×1.4 已保存")

    # ---- 灰度与反色 ----
    gray = img.convert("L")
    inverted = gray.point(lambda v: 255 - v)
    print("\n== 灰度与反色 ==")
    print("  灰度中心像素：", gray.getpixel((150, 100)))
    print("  反色后：", inverted.getpixel((150, 100)))

    # ---- HSV 色彩空间 ----
    hsv = img.convert("HSV")
    print("\n== HSV ==")
    for x in (50, 150, 250):
        print(f"  x={x}: RGB={img.getpixel((x, 100))} → HSV={hsv.getpixel((x, 100))}")
    print("  H 色相 0~255 对应 0~360°，S 饱和度，V 明度")

    # 按色相筛选：保留红色区域
    h, s, v = hsv.split()
    mask = h.point(lambda v: 255 if v < 20 or v > 235 else 0)
    filtered = Image.composite(img, Image.new("RGB", img.size, "white"), mask)
    filtered.save(tmp / "red_only.png")
    print("  只保留红色区域：已保存")

    # ---- point 阈值二值化 ----
    binary = gray.point(lambda v: 255 if v > 128 else 0)
    binary.save(tmp / "binary.png")
    print("\n== 二值化 ==")
    print("  阈值 128：已保存")

    # ---- 直方图 ----
    hist = gray.histogram()
    print("\n== 直方图 ==")
    print("  灰度级数量：", len(hist))
    print("  最暗/最亮像素数：", hist[0], hist[-1])
    total = sum(hist)
    dark = sum(hist[:64]) / total
    bright = sum(hist[192:]) / total
    print(f"  暗部占比 {dark:.1%}，亮部占比 {bright:.1%}")

    # ---- NumPy 视角 ----
    arr = np.array(img)
    print("\n== NumPy 视角 ==")
    print("  形状：", arr.shape, "（高×宽×通道）")
    print("  每通道均值：", arr.mean(axis=(0, 1)).round(1))
    print("  红色区域坐标 (50,100) 的像素：", arr[100, 50])

# ---- 用途 ----
print("\n== 用途 ==")
for item in [
    "通道分离：做单色滤镜、通道混合特效",
    "HSV：按颜色筛选（红绿灯、车牌、皮肤检测）",
    "直方图：判断曝光（左堆积=欠曝，右堆积=过曝）",
    "二值化：OCR/文档扫描预处理",
    "NumPy：自定义卷积、像素级运算、批量统计",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 只保留绿色通道，生成“绿色滤镜”图。
# 2. 用 HSV 把蓝色区域替换成紫色。
# 3. 计算一张图的平均亮度，判断是否过暗。
# 4. 思考：为什么灰度转换不是简单的 (R+G+B)/3？
