# ===== 第581课：图像处理-滤镜与增强 =====
# 知识点：
#   - ImageFilter：BLUR、GaussianBlur、SHARPEN、EDGE_ENHANCE、FIND_EDGES 等
#   - ImageEnhance：Brightness、Contrast、Color、Sharpness，factor=1 原样
#   - ImageOps：autocontrast、equalize、grayscale、invert
#   - 滤镜会改变像素值，注意保存质量与格式
#   - 与第30章 Matplotlib 图像显示的区别：这里直接处理像素矩阵
#   - 与第27章 NumPy 的配合：np.array(img) 可把图像变成数组做自定义运算
# 依赖：pip install pillow numpy

import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    # ---- 生成测试图：色块 + 细线 ----
    img = Image.new("RGB", (300, 200), "#202030")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 120, 100], fill="#4C78A8")
    draw.ellipse([160, 30, 260, 130], fill="#F58518")
    for x in range(20, 280, 20):
        draw.line([(x, 150), (x, 190)], fill="#E45756", width=2)
    img.save(tmp / "base.png")

    # ---- 模糊与锐化 ----
    print("== 滤镜 ==")
    filters = {
        "gaussian": img.filter(ImageFilter.GaussianBlur(radius=3)),
        "sharpen": img.filter(ImageFilter.SHARPEN),
        "edge": img.filter(ImageFilter.FIND_EDGES),
        "emboss": img.filter(ImageFilter.EMBOSS),
    }
    for name, out in filters.items():
        path = tmp / f"{name}.png"
        out.save(path)
        print(f"  {name:10s} → {path.name}（{path.stat().st_size} 字节）")

    # ---- 增强：亮度/对比度/饱和度/锐度 ----
    print("\n== ImageEnhance ==")
    for name, enhancer, factor in (
        ("亮度", ImageEnhance.Brightness(img), 1.5),
        ("对比度", ImageEnhance.Contrast(img), 1.5),
        ("饱和度", ImageEnhance.Color(img), 1.8),
        ("锐度", ImageEnhance.Sharpness(img), 2.0),
    ):
        out = enhancer.enhance(factor)
        path = tmp / f"enhance_{name}.png"
        out.save(path)
        print(f"  {name} ×{factor} → {path.name}")

    # ---- ImageOps ----
    print("\n== ImageOps ==")
    gray = ImageOps.grayscale(img)
    auto = ImageOps.autocontrast(gray)
    equalized = ImageOps.equalize(gray)
    inverted = ImageOps.invert(img)
    print("  灰度：", gray.mode, gray.size)
    print("  自动对比度：", auto.getextrema())
    print("  均衡化：", equalized.getextrema())
    print("  反色：", inverted.getpixel((0, 0)), "（原", img.getpixel((0, 0)), "）")

    # ---- NumPy 自定义滤镜：提高红色通道 ----
    print("\n== NumPy 自定义滤镜 ==")
    arr = np.array(img).astype(np.int16)
    arr[..., 0] = np.clip(arr[..., 0] + 40, 0, 255)   # R 通道 +40
    boosted = Image.fromarray(arr.astype(np.uint8))
    boosted.save(tmp / "red_boost.png")
    print("  红色通道增强已保存")
    print("  原图均值：", np.array(img).mean(axis=(0, 1)).round(1))
    print("  增强后均值：", np.array(boosted).mean(axis=(0, 1)).round(1))

    # ---- 滤镜对体积的影响 ----
    print("\n== 体积对比 ==")
    for name in ("base", "gaussian", "edge", "enhance_亮度"):
        path = tmp / f"{name}.png"
        if path.exists():
            print(f"  {name:14s} {path.stat().st_size:6d} 字节")

# ---- 滤镜选择建议 ----
print("\n== 选择建议 ==")
for item in [
    "缩略图前轻微锐化，显示更清晰",
    "隐私处理：高斯模糊人脸/车牌",
    "文档扫描：灰度 + autocontrast + 锐化",
    "艺术效果：FIND_EDGES / EMBOSS / 自定义卷积",
    "批量处理注意保留原图，所有操作输出到新文件",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把高斯模糊半径从 3 改成 10，观察效果与体积。
# 2. 用 ImageEnhance 组合出“复古”效果（低饱和 + 偏黄）。
# 3. 用 NumPy 实现“只保留绿色通道”的自定义滤镜。
# 4. 思考：为什么“锐化”不能真正恢复模糊掉的细节？
