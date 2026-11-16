# ===== 第588课：PPT自动化-文本与版式 =====
# 知识点：
#   - 文本框：add_textbox(left, top, width, height)
#   - TextFrame：word_wrap、auto_size、vertical_anchor
#   - Paragraph：alignment、level（层级）、space_before/after、line_spacing
#   - Run：一段连续文本，可单独设字体、字号、加粗、颜色
#   - 一个段落可以包含多个 run（局部强调），这是“富文本”的关键
#   - 与第23章 Word 的 paragraph/run 模型一致
# 依赖：pip install python-pptx

import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "text.pptx"
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[6])   # 空白页

    # ---- 标题文本框 ----
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(9), Inches(0.9))
    title_tf = title_box.text_frame
    title_tf.text = "文本与版式演示"
    title_run = title_tf.paragraphs[0].runs[0]
    title_run.font.size = Pt(32)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    # ---- 正文文本框：多段落 + 多 run ----
    body_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(8.5), Inches(4.5))
    tf = body_box.text_frame
    tf.word_wrap = True

    p1 = tf.paragraphs[0]
    p1.text = "第一段：普通文本，"
    run_bold = p1.add_run()
    run_bold.text = "这里是加粗强调"
    run_bold.font.bold = True
    run_bold.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
    p1.add_run().text = "，后面继续普通文本。"

    p2 = tf.add_paragraph()
    p2.text = "第二段：居中对齐"
    p2.alignment = PP_ALIGN.CENTER
    p2.font.size = Pt(18)

    p3 = tf.add_paragraph()
    p3.text = "第三段：项目符号层级"
    p3.font.size = Pt(18)
    p3.space_before = Pt(12)

    for level, text in ((1, "一级要点 A"), (1, "一级要点 B"), (2, "二级子要点 B1")):
        p = tf.add_paragraph()
        p.text = text
        p.level = level
        p.font.size = Pt(16)
        p.space_before = Pt(4)

    p4 = tf.add_paragraph()
    p4.text = "第四段：右对齐 + 斜体 + 灰色"
    p4.alignment = PP_ALIGN.RIGHT
    p4.font.size = Pt(14)
    p4.font.italic = True
    p4.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

    prs.save(path)
    print("已保存 text.pptx")

    # ---- 读回并检查格式 ----
    loaded = Presentation(path)
    slide = loaded.slides[0]
    print("\n== 读回文本结构 ==")
    for shape in slide.shapes:
        if not shape.has_text_frame:
            continue
        print(f"\n  形状：{shape.name}")
        print(f"  word_wrap={shape.text_frame.word_wrap}")
        for i, para in enumerate(shape.text_frame.paragraphs):
            print(f"    段落{i}: 对齐={para.alignment}, 层级={para.level}")
            for j, run in enumerate(para.runs):
                font = run.font
                size = font.size.pt if font.size else None
                bold = font.bold
                color = None
                try:
                    if font.color and font.color.rgb:
                        color = str(font.color.rgb)
                except Exception:
                    pass
                print(f"      run{j}: {run.text!r} size={size} bold={bold} color={color}")

# ---- 文本排版建议 ----
print("\n== 排版建议 ==")
for item in [
    "标题 28~36pt，正文 16~20pt，注释 12~14pt",
    "每页文字不超过 6 行要点，避免密密麻麻",
    "强调用加粗/颜色，不要整段变色",
    "中文字体在模板里指定（如微软雅黑）",
    "长文本用 word_wrap=True，避免溢出页面",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 生成一页“标题 + 3 个要点 + 1 个结论”的文本页。
# 2. 用两个 run 实现“前半句黑色、后半句红色加粗”。
# 3. 设置段落行距为 1.5 倍（line_spacing）。
# 4. 思考：段落和 run 的区别是什么？为什么需要 run？
