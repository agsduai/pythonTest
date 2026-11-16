# ===== 第579课：图像处理-打开保存与基本信息 =====
# 知识点：
#   - Pillow：Python 最常用的图像处理库（pip install pillow）
#   - Image.open：打开图像（惰性加载，读取时才解码）
#   - 常用属性：size（宽,高）、mode（RGB/RGBA/L/P）、format（PNG/JPEG）
#   - save：按扩展名推断格式；quality 控制 JPEG 质量
#   - convert：颜色模式转换（RGB↔RGBA↔L）
#   - 与第30章 Matplotlib 的区别：Matplotlib 画图，Pillow 处理像素
# 依赖：pip install pillow

import tempfile
from pathlib import Path

from PIL import Image

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    # ---- 生成一张渐变测试图 ----
    width, height = 240, 120
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            pixels[x, y] = (x, y, (x + y) % 256)

    print("== 新图属性 ==")
    print("  尺寸：", img.size)
    print("  模式：", img.mode)
    print("  格式：", img.format, "（内存中新建，没有格式）")

    # ---- 保存为不同格式 ----
    paths = {
        "png": tmp / "test.png",
        "jpg": tmp / "test.jpg",
        "bmp": tmp / "test.bmp",
    }
    for fmt, path in paths.items():
        save_kwargs = {"quality": 85} if fmt == "jpg" else {}
        img.save(path, **save_kwargs)
        print(f"  保存 {fmt.upper():4s}：{path.stat().st_size} 字节")

    # ---- 重新打开并读取 ----
    print("\n== 重新打开 ==")
    for fmt, path in paths.items():
        with Image.open(path) as opened:
            print(f"  {fmt.upper():4s}: size={opened.size}, mode={opened.mode}, "
                  f"format={opened.format}")

    # ---- 颜色模式转换 ----
    print("\n== 模式转换 ==")
    rgba = img.convert("RGBA")
    gray = img.convert("L")
    palette = img.convert("P")
    print("  RGB → RGBA：", rgba.mode)
    print("  RGB → L（灰度）：", gray.mode)
    print("  RGB → P（调色板）：", palette.mode)
    print("  灰度图中心像素：", gray.getpixel((width // 2, height // 2)))

    # ---- JPEG 质量与体积 ----
    print("\n== JPEG 质量 ==")
    for quality in (95, 75, 30):
        path = tmp / f"q{quality}.jpg"
        img.save(path, quality=quality)
        print(f"  quality={quality}: {path.stat().st_size} 字节")

    # ---- 读取像素 ----
    print("\n== 像素访问 ==")
    print("  (0,0)：", img.getpixel((0, 0)))
    print("  (120,60)：", img.getpixel((120, 60)))
    print("  (239,119)：", img.getpixel((239, 119)))

# ---- 常用格式对照 ----
print("\n== 格式对照 ==")
rows = [
    ("PNG", "无损、支持透明", "截图、图标、需要透明"),
    ("JPEG", "有损、体积小", "照片、网页大图"),
    ("WebP", "有损/无损、更小", "现代浏览器图片"),
    ("BMP", "无压缩、很大", "几乎不用"),
    ("GIF", "256 色、支持动画", "简单动图"),
]
print(f"  {'格式':<8}{'特点':<22}{'场景'}")
for r in rows:
    print(f"  {r[0]:<8}{r[1]:<22}{r[2]}")

# ---- 注意 ----
print("\n== 注意 ==")
for item in [
    "Image.open 是惰性的，with 块结束文件关闭，需 copy() 后再用",
    "JPEG 不支持透明，RGBA 存 JPEG 会报错，要先 convert('RGB')",
    "保存格式由扩展名或 format 参数决定，不要混用",
    "大图处理注意内存（第366课内存画像）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 生成 100×100 纯红图并保存为 PNG。
# 2. 把一张 RGB 图转灰度，比较保存后的体积。
# 3. 用 Image.open 打开不存在的文件，捕获异常。
# 4. 思考：为什么 JPEG 不支持透明？PNG 为什么更大？
