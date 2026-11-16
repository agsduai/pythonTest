# ===== 第580课：图像处理-缩放裁剪旋转 =====
# 知识点：
#   - resize((w,h))：强制拉伸；thumbnail 等比缩略（原地修改，保持比例）
#   - 重采样：Image.Resampling.LANCZOS 质量最好（缩小/放大都推荐）
#   - crop((left,top,right,bottom))：裁剪矩形区域
#   - rotate(angle, expand=True)：旋转；expand 自动扩大画布避免截断
#   - transpose：FLIP_LEFT_RIGHT / FLIP_TOP_BOTTOM / ROTATE_90 等
#   - 与第30章图表缩放的区别：这里是位图重采样，会损失/插值像素
# 依赖：pip install pillow

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    # ---- 生成一张带网格的图，便于观察变形 ----
    img = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(img)
    for x in range(0, 400, 50):
        draw.line([(x, 0), (x, 300)], fill="lightgray")
    for y in range(0, 300, 50):
        draw.line([(0, y), (400, y)], fill="lightgray")
    draw.rectangle([150, 100, 250, 200], fill="#4C78A8")
    draw.ellipse([20, 20, 80, 80], fill="#F58518")
    img.save(tmp / "base.png")

    print("== 原图 ==", img.size)

    # ---- 1. resize 强制尺寸 ----
    resized = img.resize((200, 150), Image.Resampling.LANCZOS)
    print("  resize(200,150)：", resized.size)
    resized.save(tmp / "resized.png")

    # 非等比拉伸（会变形）
    stretched = img.resize((200, 300), Image.Resampling.BILINEAR)
    print("  resize(200,300) 非等比：", stretched.size)

    # ---- 2. thumbnail 等比缩略 ----
    thumb = img.copy()
    thumb.thumbnail((120, 120), Image.Resampling.LANCZOS)
    print("  thumbnail(120,120)：", thumb.size, "（保持比例，不会超过 120）")
    thumb.save(tmp / "thumb.png")

    # ---- 3. crop 裁剪 ----
    cropped = img.crop((100, 50, 300, 250))
    print("  crop(100,50,300,250)：", cropped.size)
    cropped.save(tmp / "cropped.png")

    # ---- 4. rotate 旋转 ----
    rotated = img.rotate(45, expand=True, fillcolor="white")
    print("  rotate(45, expand=True)：", rotated.size)
    rotated.save(tmp / "rotated.png")

    rotated_fixed = img.rotate(45, expand=False, fillcolor="white")
    print("  rotate(45, expand=False)：", rotated_fixed.size, "（四角被裁掉）")

    # ---- 5. transpose 翻转 ----
    flipped = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    flipped.save(tmp / "flipped.png")
    print("  FLIP_LEFT_RIGHT：", flipped.size)
    print("  旋转 90°：", img.transpose(Image.Transpose.ROTATE_90).size)

    # ---- 重采样对比 ----
    print("\n== 重采样算法 ==")
    small = img.resize((80, 60))
    for name, method in (
        ("NEAREST（最快、锯齿）", Image.Resampling.NEAREST),
        ("BILINEAR（平滑）", Image.Resampling.BILINEAR),
        ("BICUBIC（更平滑）", Image.Resampling.BICUBIC),
        ("LANCZOS（质量最好）", Image.Resampling.LANCZOS),
    ):
        out = small.resize((320, 240), method)
        out.save(tmp / f"resample_{method.name}.png")
        print(f"  {name}: 已保存 resample_{method.name}.png")

    # ---- 输出文件 ----
    print("\n== 生成文件 ==")
    for p in sorted(tmp.glob("*.png")):
        with Image.open(p) as im:
            print(f"  {p.name:24s} {im.size[0]:4d}×{im.size[1]:<4d} "
                  f"{p.stat().st_size:6d} 字节")

# ---- 使用建议 ----
print("\n== 使用建议 ==")
for item in [
    "缩小用 LANCZOS；放大也建议 LANCZOS（避免锯齿）",
    "thumbnail 原地修改，想保留原图先 copy()",
    "crop 的坐标是 (左,上,右,下)，右下是开区间",
    "rotate 默认逆时针；expand=True 才不会裁掉角",
    "批量处理先统一 EXIF 方向（第584课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把 400×300 图裁剪成正方形（居中）。
# 2. 生成 120×120 缩略图并保持比例，打印实际尺寸。
# 3. 旋转 30° 后保存为 JPEG，观察四个角是否是白色。
# 4. 思考：为什么“先缩略再裁剪”和“先裁剪再缩略”结果不同？
