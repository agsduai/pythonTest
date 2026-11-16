# ===== 第589课：PPT自动化-表格 =====
# 知识点：
#   - add_table(rows, cols, left, top, width, height)
#   - table.cell(row, col).text：写单元格；合并单元格用 cell.merge
#   - 列宽：table.columns[i].width；行高：table.rows[i].height
#   - 表头样式：cell.fill.solid() + fore_color；字体加粗/白色
#   - 对齐：cell.text_frame.paragraphs[0].alignment
#   - 与第23章 Excel 表格的区别：PPT 表格是展示用，不适合大数据
# 依赖：pip install python-pptx

import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "table.pptx"
    prs = Presentation()

    # 标题页
    slide = prs.slides.add_slide(prs.slide_layouts[5])   # Title Only
    slide.shapes.title.text = "2026 年 11 月经营指标"

    # ---- 创建表格 ----
    rows, cols = 5, 4
    left, top, width, height = Inches(0.6), Inches(1.5), Inches(9), Inches(3)
    shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = shape.table

    headers = ["指标", "本月", "上月", "环比"]
    data = [
        ["销售额（万元）", "1,280", "1,150", "+11.3%"],
        ["订单数", "8,420", "7,980", "+5.5%"],
        ["客单价（元）", "152", "144", "+5.6%"],
        ["退款率", "2.1%", "2.4%", "-0.3pp"],
    ]

    # 表头
    for c, header in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = header
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0x1F, 0x4E, 0x79)
        para = cell.text_frame.paragraphs[0]
        para.alignment = PP_ALIGN.CENTER
        para.font.size = Pt(18)
        para.font.bold = True
        para.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    # 数据行
    for r, row in enumerate(data, 1):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = value
            para = cell.text_frame.paragraphs[0]
            para.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            para.font.size = Pt(16)
            if c == 3 and value.startswith("+"):
                para.font.color.rgb = RGBColor(0x2E, 0x7D, 0x32)
            elif c == 3 and value.startswith("-"):
                para.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)

    # 列宽
    widths = [Inches(3.2), Inches(1.8), Inches(1.8), Inches(1.8)]
    for i, w in enumerate(widths):
        table.columns[i].width = w

    prs.save(path)
    print("已保存 table.pptx")

    # ---- 读回表格 ----
    loaded = Presentation(path)
    slide = loaded.slides[0]
    for shape in slide.shapes:
        if not shape.has_table:
            continue
        table = shape.table
        print(f"\n== 表格：{len(table.rows)} 行 × {len(table.columns)} 列 ==")
        for r in range(len(table.rows)):
            values = [table.cell(r, c).text for c in range(len(table.columns))]
            print("  ", values)

    # ---- 合并单元格示例 ----
    print("\n== 合并单元格 ==")
    prs2 = Presentation()
    s = prs2.slides.add_slide(prs2.slide_layouts[6])
    t = s.shapes.add_table(3, 3, Inches(1), Inches(1), Inches(6), Inches(2)).table
    for r in range(3):
        for c in range(3):
            t.cell(r, c).text = f"{r},{c}"
    t.cell(0, 0).merge(t.cell(0, 2))         # 第一行合并
    t.cell(1, 0).merge(t.cell(2, 0))         # 第一列合并
    print("  已合并第一行与第一列")
    print("  (0,0) 文本：", t.cell(0, 0).text)
    print("  (1,0) 文本：", t.cell(1, 0).text)
    print("  合并后表格仍可正常读回")

# ---- 表格设计建议 ----
print("\n== 设计建议 ==")
for item in [
    "PPT 表格不超过 6~8 行，细节放附录/Excel",
    "表头深色底 + 白字，数据行浅色交替（可选）",
    "数字右对齐/居中，文字左对齐",
    "重点变化用颜色强调，但只标一处",
    "列宽按内容分配，别让数字换行",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给表格增加一行“毛利率”，并标绿色。
# 2. 把表头改成两行合并（如“销售额”跨“本月/上月”）。
# 3. 设置行高为 0.5 英寸，观察页面占用。
# 4. 思考：为什么 PPT 表格不适合放几百行数据？
