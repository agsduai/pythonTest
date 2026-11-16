# ===== 第594课：PPT自动化-综合案例-月度经营分析PPT =====
# 知识点：
#   - 综合运用：标题页（587）+ 文本（588）+ 表格（589）+ 图表（590）
#     + 图片/形状（591）+ 备注（593）
#   - 结构：封面 → 核心指标表 → 品类销售额柱状图 → 结构饼图 → 结论
#   - 数据先聚合（第28章 pandas/纯 Python），再映射成 PPT 元素
#   - 生成后读回校验：页数、表格行列、图表系列、备注
#   - 交付：一份可在 PowerPoint/WPS 中继续编辑的原生 PPT
# 依赖：pip install python-pptx

import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# ---------------- 模拟聚合后的数据 ----------------
KPI = [
    ("销售额（万元）", "1,280", "1,150", "+11.3%"),
    ("订单数", "8,420", "7,980", "+5.5%"),
    ("客单价（元）", "152", "144", "+5.6%"),
    ("退款率", "2.1%", "2.4%", "-0.3pp"),
]
CATEGORY_SALES = {"数码": 520, "服饰": 380, "食品": 260, "图书": 120}
MONTHLY_TREND = {"7月": 900, "8月": 950, "9月": 1020, "10月": 1150, "11月": 1280}
CONCLUSIONS = [
    "销售额环比增长 11.3%，主要由数码品类拉动",
    "客单价提升 5.6%，但订单数增长只有 5.5%",
    "退款率下降到 2.1%，售后质量改善",
    "下月重点：服饰品类促销 + 食品复购",
]


def build_deck(path: Path):
    prs = Presentation()
    # 16:9
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # ---------------- 1. 封面 ----------------
    cover = prs.slides.add_slide(prs.slide_layouts[0])
    cover.shapes.title.text = "2026 年 11 月经营分析"
    cover.placeholders[1].text = "数据组 · 2026-11-13"
    cover.notes_slide.notes_text_frame.text = "开场：先讲整体结论，再展开明细。"

    # ---------------- 2. 核心指标表 ----------------
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "核心指标"
    rows, cols = len(KPI) + 1, 4
    table = slide.shapes.add_table(
        rows, cols, Inches(0.7), Inches(1.6), Inches(12), Inches(3.2)
    ).table
    headers = ["指标", "本月", "上月", "环比"]
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(0x1F, 0x4E, 0x79)
        p = cell.text_frame.paragraphs[0]
        p.font.bold = True
        p.font.size = Pt(18)
        p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.alignment = PP_ALIGN.CENTER
    for r, row in enumerate(KPI, 1):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = value
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(16)
            p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
            if c == 3:
                p.font.color.rgb = (RGBColor(0x2E, 0x7D, 0x32)
                                    if value.startswith("+")
                                    else RGBColor(0xC0, 0x00, 0x00))
    for i, w in enumerate((4.0, 2.5, 2.5, 2.5)):
        table.columns[i].width = Inches(w)
    slide.notes_slide.notes_text_frame.text = "表格数据来自数仓 dw_orders，口径见指标注册表。"

    # ---------------- 3. 品类销售额柱状图 ----------------
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "品类销售额（万元）"
    data = CategoryChartData()
    data.categories = list(CATEGORY_SALES.keys())
    data.add_series("销售额", list(CATEGORY_SALES.values()))
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(0.7), Inches(1.6), Inches(11.8), Inches(5.2), data,
    ).chart
    chart.has_title = True
    chart.chart_title.text_frame.text = "数码品类贡献最大"
    chart.has_legend = False
    slide.notes_slide.notes_text_frame.text = "数码 520 万，占 40.6%；图书基数小但增速快。"

    # ---------------- 4. 结构饼图 ----------------
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "销售额结构"
    pie_data = CategoryChartData()
    total = sum(CATEGORY_SALES.values())
    pie_data.categories = list(CATEGORY_SALES.keys())
    pie_data.add_series("占比", [v / total for v in CATEGORY_SALES.values()])
    pie = slide.shapes.add_chart(
        XL_CHART_TYPE.PIE,
        Inches(3.0), Inches(1.6), Inches(7.5), Inches(5.2), pie_data,
    ).chart
    pie.has_title = True
    pie.chart_title.text_frame.text = "品类占比"
    pie.has_legend = True
    pie.legend.position = XL_LEGEND_POSITION.RIGHT
    pie.plots[0].has_data_labels = True
    pie.plots[0].data_labels.show_percentage = True
    slide.notes_slide.notes_text_frame.text = "饼图类别不超过 5 个，超过就改柱状图。"

    # ---------------- 5. 趋势与结论 ----------------
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "趋势与结论"
    line_data = CategoryChartData()
    line_data.categories = list(MONTHLY_TREND.keys())
    line_data.add_series("销售额", list(MONTHLY_TREND.values()))
    line = slide.shapes.add_chart(
        XL_CHART_TYPE.LINE_MARKERS,
        Inches(0.6), Inches(1.6), Inches(7.2), Inches(5.0), line_data,
    ).chart
    line.has_title = True
    line.chart_title.text_frame.text = "近 5 个月持续增长"

    box = slide.shapes.add_textbox(Inches(8.1), Inches(1.8), Inches(4.6), Inches(4.6))
    tf = box.text_frame
    tf.word_wrap = True
    tf.text = "结论"
    tf.paragraphs[0].font.size = Pt(22)
    tf.paragraphs[0].font.bold = True
    for item in CONCLUSIONS:
        p = tf.add_paragraph()
        p.text = f"· {item}"
        p.font.size = Pt(14)
        p.space_before = Pt(8)
    slide.notes_slide.notes_text_frame.text = "结论先行：增长由数码拉动；下月资源向服饰与食品倾斜。"

    prs.save(path)
    return prs


with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "monthly_report.pptx"
    prs = build_deck(path)
    print(f"已生成：{path.name}（{path.stat().st_size / 1024:.1f} KB）")

    # ---------------- 读回校验 ----------------
    loaded = Presentation(path)
    print("\n== 结构校验 ==")
    print("  页数：", len(loaded.slides))
    print("  页面尺寸：", loaded.slide_width, "×", loaded.slide_height)
    for index, slide in enumerate(loaded.slides, 1):
        shapes = list(slide.shapes)
        tables = [s for s in shapes if s.has_table]
        charts = [s for s in shapes if s.has_chart]
        title = slide.shapes.title.text if slide.shapes.title else "(无标题)"
        notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        print(f"\n  第{index}页：{title}")
        print(f"    形状 {len(shapes)} 个，表格 {len(tables)} 个，图表 {len(charts)} 个")
        for t in tables:
            table = t.table
            print(f"    表格 {len(table.rows)}×{len(table.columns)}，"
                  f"首行：{[table.cell(0, c).text for c in range(len(table.columns))]}")
        for c in charts:
            chart = c.chart
            print(f"    图表类型 {chart.chart_type}，系列 {len(chart.series)}")
        if notes:
            print(f"    备注：{notes[:50]}")

# ---------------- 交付清单 ----------------
print("\n== 交付清单 ==")
for item in [
    "封面：主题 + 日期 + 汇报人",
    "KPI 表：本月/上月/环比，重点数字标色",
    "图表：1~2 张，标题写结论",
    "结论页：3~4 条，可直接照着讲",
    "备注：讲稿提示与数据来源",
    "文件命名：主题_年月_版本",
]:
    print("  -", item)

# ---------------- 可扩展 ----------------
print("\n== 可扩展 ==")
for item in [
    "数据从 SQLite/Excel 读取，自动刷新（第13/23章）",
    "按部门批量生成多份（第593课）",
    "生成后转 PDF（需 PowerPoint/LibreOffice，本机未装）",
    "模板化设计，代码只填数据（第592课）",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 把 KPI 表改成“本月/上月/去年同期”三列。
# 2. 给结论页加一个“下月行动计划”表格。
# 3. 用第586课的图片处理生成封面配图并插入。
# 4. 思考：为什么经营分析 PPT 要“结论先行”，而不是先放数据？
