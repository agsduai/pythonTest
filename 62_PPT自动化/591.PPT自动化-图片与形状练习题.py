# ===== 第591课：PPT自动化-图片与形状 =====
# 知识点：
#   - add_picture(path, left, top, width/height)：插入图片，按比例缩放
#   - add_shape(MSO_SHAPE.xxx, ...)：矩形、圆角矩形、椭圆、箭头等
#   - shape.fill / shape.line：填充色、边框色与线宽
#   - shape.text_frame：形状里也能写字
#   - 图层顺序：后添加的在上层；可用 z-order 调整（本课不展开）
#   - 与第61章 Pillow 的配合：先用 Pillow 生成/处理图片，再插入 PPT
# 依赖：pip install python-pptx pillow

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    # ---- 用 Pillow 生成一张配图 ----
    img = Image.new("RGB", (400, 240), "#EAF2F8")
    draw = ImageDraw.Draw(img)
    draw.rectangle([30, 30, 370, 210], outline="#1F4E79", width=4)
    draw.ellipse([120, 70, 280, 190], fill="#4C78A8")
    img_path = tmp / "illustration.png"
    img.save(img_path)

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])   # 空白页

    # ---- 标题 ----
    title = slide.shapes.add_textbox(Inches(0.6), Inches(0.3), Inches(9), Inches(0.7))
    title.text_frame.text = "图片与形状"
    title.text_frame.paragraphs[0].font.size = Pt(28)
    title.text_frame.paragraphs[0].font.bold = True

    # ---- 插入图片 ----
    picture = slide.shapes.add_picture(
        str(img_path), Inches(0.6), Inches(1.3), width=Inches(4.2)
    )
    print("图片尺寸：", picture.width, "×", picture.height, "EMU")

    # ---- 圆角矩形 ----
    box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(5.2), Inches(1.3), Inches(4.2), Inches(1.4),
    )
    box.fill.solid()
    box.fill.fore_color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    box.line.color.rgb = RGBColor(0x0B, 0x2A, 0x43)
    box.line.width = Pt(2)
    box.text_frame.text = "圆角矩形 + 文字"
    box.text_frame.paragraphs[0].font.size = Pt(20)
    box.text_frame.paragraphs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # ---- 椭圆与箭头 ----
    oval = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(5.2), Inches(3.0), Inches(1.6), Inches(1.0)
    )
    oval.fill.solid()
    oval.fill.fore_color.rgb = RGBColor(0xF5, 0x85, 0x18)

    arrow = slide.shapes.add_shape(
        MSO_SHAPE.RIGHT_ARROW, Inches(7.0), Inches(3.2), Inches(2.2), Inches(0.6)
    )
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = RGBColor(0x54, 0xA2, 0x4B)

    # ---- 文字说明 ----
    caption = slide.shapes.add_textbox(Inches(0.6), Inches(5.2), Inches(9), Inches(0.5))
    caption.text_frame.text = "图片来自 Pillow 生成；形状均为可编辑的 PPT 原生对象"
    caption.text_frame.paragraphs[0].font.size = Pt(12)
    caption.text_frame.paragraphs[0].font.italic = True

    path = tmp / "shapes.pptx"
    prs.save(path)
    print("已保存 shapes.pptx")

    # ---- 读回形状 ----
    loaded = Presentation(path)
    slide = loaded.slides[0]
    print("\n== 形状清单 ==")
    for shape in slide.shapes:
        text = shape.text.replace("\n", " / ") if shape.has_text_frame else ""
        print(f"  {shape.shape_type} | 名称={shape.name} | 位置=({shape.left},{shape.top}) "
              f"| 文本={text[:20]!r}")

# ---- 布局建议 ----
print("\n== 布局建议 ==")
for item in [
    "图片保持宽高比：只给 width 或 height，另一个自动算",
    "一页最多 1 张主图 + 少量形状，避免拥挤",
    "形状颜色用主题色，保持全篇一致",
    "文字与背景对比度要够（深底白字/浅底黑字）",
    "用形状做流程图时，箭头要对齐",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 生成一张 16:9 的配图并插入，保持比例。
# 2. 用 3 个圆角矩形 + 2 个箭头画一个三步流程图。
# 3. 给图片加边框（picture.line.color）。
# 4. 思考：什么时候用 PPT 形状，什么时候直接用图片？
