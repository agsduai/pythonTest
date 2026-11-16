# ===== 第582课：图像处理-绘制与水印 =====
# 知识点：
#   - ImageDraw：rectangle / ellipse / line / polygon / text
#   - 文字需要 ImageFont：truetype 加载系统字体，默认字体不支持中文
#   - 水印：新建 RGBA 叠加层，写半透明文字，再用 alpha_composite 合并
#   - textbbox 计算文字尺寸，用于居中/背景框
#   - 平铺水印：循环绘制多个倾斜文字，防裁剪盗用
#   - 与第23章 Excel/Word 水印的区别：那是文档层，这里是像素层
# 依赖：pip install pillow

import os
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",        # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",      # 黑体
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def load_font(size: int):
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size), True
            except OSError:
                continue
    return ImageFont.load_default(), False


def draw_shapes():
    img = Image.new("RGB", (400, 240), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 160, 100], fill="#4C78A8", outline="black", width=2)
    draw.ellipse([200, 20, 320, 140], fill="#F58518", outline="#8B4513", width=2)
    draw.line([(20, 160), (380, 160)], fill="#E45756", width=4)
    draw.polygon([(40, 220), (100, 180), (160, 220)], fill="#54A24B")
    return img


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    font, has_cjk = load_font(28)
    small_font, _ = load_font(14)

    # ---- 基础图形 ----
    img = draw_shapes()
    draw = ImageDraw.Draw(img)
    text = "课程水印" if has_cjk else "DEMO"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((400 - text_w) / 2, 200), text, fill="#333333", font=font)
    img.save(tmp / "shapes.png")
    print("== 基础图形 ==")
    print(f"  中文字体可用：{has_cjk}，文字尺寸：{text_w}×{text_h}")

    # ---- 半透明水印 ----
    base = Image.new("RGB", (500, 300), "#EFEFEF")
    bd = ImageDraw.Draw(base)
    bd.rectangle([50, 50, 450, 250], fill="#BFD7EA")
    bd.text((70, 70), "原图内容", fill="black", font=font)

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    watermark = "课程水印" if has_cjk else "DEMO"
    wm_font, _ = load_font(36)
    box = od.textbbox((0, 0), watermark, font=wm_font)
    wm_w, wm_h = box[2] - box[0], box[3] - box[1]
    od.text(((base.width - wm_w) / 2, (base.height - wm_h) / 2),
            watermark, font=wm_font, fill=(255, 0, 0, 80))
    base_rgba = base.convert("RGBA")
    watermarked = Image.alpha_composite(base_rgba, overlay).convert("RGB")
    watermarked.save(tmp / "watermark.png")
    print("\n== 半透明水印 ==")
    print("  已保存 watermark.png（alpha=80）")

    # ---- 平铺水印 ----
    tiled = base.copy()
    tile_overlay = Image.new("RGBA", tiled.size, (0, 0, 0, 0))
    td = ImageDraw.Draw(tile_overlay)
    tile_text = "SAMPLE" if not has_cjk else "内部资料"
    for y in range(-20, tiled.height, 80):
        for x in range(-20, tiled.width, 160):
            td.text((x, y), tile_text, font=small_font, fill=(0, 0, 0, 45))
    tiled = Image.alpha_composite(tiled.convert("RGBA"), tile_overlay).convert("RGB")
    tiled.save(tmp / "tiled.png")
    print("  已保存 tiled.png（平铺）")

    # ---- 文字背景框 ----
    label = "标签"
    box_img = Image.new("RGB", (200, 80), "white")
    bd2 = ImageDraw.Draw(box_img)
    bbox = bd2.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bd2.rectangle([10, 20, 10 + tw + 16, 20 + th + 16], fill="#4C78A8")
    bd2.text((18, 28), label, fill="white", font=font)
    box_img.save(tmp / "label.png")
    print("  已保存 label.png（文字+背景框）")

    # ---- 输出清单 ----
    print("\n== 生成文件 ==")
    for p in sorted(tmp.glob("*.png")):
        with Image.open(p) as im:
            print(f"  {p.name:16s} {im.size}")

# ---- 水印设计建议 ----
print("\n== 水印建议 ==")
for item in [
    "透明度 20~40，既能看见又不遮内容",
    "位置可选右下角、居中、平铺；敏感图用平铺",
    "文字+日期+用户 ID，便于追溯泄露源",
    "真正防泄露要靠权限/水印+审计，不能只靠图片水印",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给图片右下角加“用户名 + 日期”水印。
# 2. 实现斜向 45° 平铺水印（提示：先画到透明层再 rotate）。
# 3. 给文字加描边（stroke_width/stroke_fill）。
# 4. 思考：为什么“图片水印”不能真正阻止截图泄露？
