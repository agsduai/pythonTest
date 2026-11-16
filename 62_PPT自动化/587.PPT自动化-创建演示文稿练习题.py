# ===== 第587课：PPT自动化-创建演示文稿 =====
# 知识点：
#   - python-pptx：用代码创建/修改 .pptx（pip install python-pptx）
#   - Presentation()：新建演示文稿；slide_layouts 是版式模板
#   - add_slide(layout)：按版式加一页；常用 0=标题页、1=标题+内容、6=空白
#   - shapes.title / placeholders：版式自带的占位符
#   - save(path)：保存；重新 Presentation(path) 可读回结构
#   - 与第23章 Excel/Word 自动化的关系：同一套“生成办公文档”思路
# 依赖：pip install python-pptx

import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "demo.pptx"

    # ---- 新建演示文稿 ----
    prs = Presentation()
    print("== 版式列表 ==")
    for i, layout in enumerate(prs.slide_layouts):
        print(f"  {i}: {layout.name}")

    # 第 1 页：标题页（版式 0）
    slide1 = prs.slides.add_slide(prs.slide_layouts[0])
    slide1.shapes.title.text = "Python 自动化月报"
    slide1.placeholders[1].text = "2026 年 11 月 · 数据组"

    # 第 2 页：标题 + 内容（版式 1）
    slide2 = prs.slides.add_slide(prs.slide_layouts[1])
    slide2.shapes.title.text = "本月要点"
    slide2.placeholders[1].text = "完成 3 个数据管道\n上线 2 个报表\n缺陷率下降 15%"

    # 第 3 页：空白页 + 文本框
    slide3 = prs.slides.add_slide(prs.slide_layouts[6])
    box = slide3.shapes.add_textbox(Inches(1), Inches(1.5), Inches(8), Inches(3))
    box.text_frame.text = "这一页只有文本框，没有占位符"
    box.text_frame.paragraphs[0].font.size = Pt(24)

    prs.save(path)
    print(f"\n已保存：{path.name}（{path.stat().st_size} 字节）")

    # ---- 读回结构 ----
    loaded = Presentation(path)
    print("\n== 读回结构 ==")
    print("  幻灯片数量：", len(loaded.slides))
    print("  页面尺寸：", loaded.slide_width, "×", loaded.slide_height, "EMU")
    for index, slide in enumerate(loaded.slides, 1):
        print(f"\n  第 {index} 页（版式：{slide.slide_layout.name}）：")
        for shape in slide.shapes:
            kind = shape.shape_type
            has_text = getattr(shape, "has_text_frame", False)
            text = shape.text.replace("\n", " / ") if has_text else ""
            print(f"    - {kind} | 文本框={has_text} | {text[:40]!r}")

# ---- 常用版式含义 ----
print("\n== 常用版式 ==")
rows = [
    ("0", "Title Slide", "标题 + 副标题"),
    ("1", "Title and Content", "标题 + 正文占位符"),
    ("5", "Title Only", "只有标题"),
    ("6", "Blank", "完全空白，自己放控件"),
]
print(f"  {'索引':<5}{'名称':<22}{'用途'}")
for r in rows:
    print(f"  {r[0]:<5}{r[1]:<22}{r[2]}")

# ---- 单位说明 ----
print("\n== 单位 ==")
print("  Inches(1) / Cm(2.5) / Pt(18)：pptx 内部用 EMU")
print("  1 英寸 = 914400 EMU；页面默认 10×7.5 英寸（4:3）")
print("  16:9 可设 prs.slide_width = Inches(13.333)")

# ===== 练习题 =====
# 1. 新建一个 3 页演示文稿（标题、内容、空白）。
# 2. 打印默认模板的所有版式名称。
# 3. 把页面改成 16:9 并保存。
# 4. 思考：为什么用 python-pptx 而不是“用脚本操作 PowerPoint 窗口”？
