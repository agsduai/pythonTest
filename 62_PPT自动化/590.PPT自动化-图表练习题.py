# ===== 第590课：PPT自动化-图表 =====
# 知识点：
#   - CategoryChartData：类别 + 多个系列的数据容器
#   - add_chart(图表类型, 位置, 尺寸)：嵌入原生可编辑图表
#   - 常用类型：COLUMN_CLUSTERED 柱状、LINE 折线、PIE 饼图
#   - chart.has_title / chart_title.text_frame：图表标题
#   - chart.has_legend / legend.position：图例
#   - 与第30章 Matplotlib 的区别：pptx 图表是 PowerPoint 原生对象，可在 PPT 里继续编辑
# 依赖：pip install python-pptx

import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.util import Inches

with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "charts.pptx"
    prs = Presentation()

    # ---------------- 柱状图 ----------------
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "各品类销售额（万元）"

    chart_data = CategoryChartData()
    chart_data.categories = ["数码", "服饰", "食品", "图书"]
    chart_data.add_series("本月", (520, 380, 260, 120))
    chart_data.add_series("上月", (480, 350, 240, 110))

    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED,
        Inches(0.6), Inches(1.5), Inches(8.5), Inches(4.5),
        chart_data,
    ).chart
    chart.has_title = True
    chart.chart_title.text_frame.text = "本月 vs 上月"
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False

    # ---------------- 饼图 ----------------
    slide2 = prs.slides.add_slide(prs.slide_layouts[5])
    slide2.shapes.title.text = "销售额占比"

    pie_data = CategoryChartData()
    pie_data.categories = ["数码", "服饰", "食品", "图书"]
    pie_data.add_series("占比", (0.42, 0.30, 0.18, 0.10))

    pie = slide2.shapes.add_chart(
        XL_CHART_TYPE.PIE,
        Inches(1.2), Inches(1.5), Inches(7), Inches(4.5),
        pie_data,
    ).chart
    pie.has_title = True
    pie.chart_title.text_frame.text = "品类结构"
    pie.has_legend = True
    pie.legend.position = XL_LEGEND_POSITION.RIGHT
    pie.plots[0].has_data_labels = True
    pie.plots[0].data_labels.show_percentage = True

    # ---------------- 折线图 ----------------
    slide3 = prs.slides.add_slide(prs.slide_layouts[5])
    slide3.shapes.title.text = "月度趋势"

    line_data = CategoryChartData()
    line_data.categories = ["7月", "8月", "9月", "10月", "11月"]
    line_data.add_series("销售额", (900, 950, 1020, 1150, 1280))
    line = slide3.shapes.add_chart(
        XL_CHART_TYPE.LINE_MARKERS,
        Inches(0.8), Inches(1.6), Inches(8.2), Inches(4.2),
        line_data,
    ).chart
    line.has_title = True
    line.chart_title.text_frame.text = "近 5 个月趋势"

    prs.save(path)
    print("已保存 charts.pptx")

    # ---- 读回图表信息 ----
    loaded = Presentation(path)
    print("\n== 读回图表 ==")
    for i, slide in enumerate(loaded.slides, 1):
        for shape in slide.shapes:
            if not shape.has_chart:
                continue
            chart = shape.chart
            print(f"  第 {i} 页：类型={chart.chart_type}，"
                  f"系列数={len(chart.series)}，"
                  f"标题={(chart.chart_title.text_frame.text if chart.has_title else '无')}")
            for series in chart.series:
                values = list(series.values)
                print(f"    - 系列 {series.name}: {values}")

# ---- 图表选择建议 ----
print("\n== 图表选择 ==")
rows = [
    ("柱状图", "类别对比", "类别数 <= 6"),
    ("折线图", "时间趋势", "连续时间点"),
    ("饼图", "占比结构", "类别 <= 5，且占比有意义"),
    ("散点图", "相关性", "两组数值"),
]
print(f"  {'类型':<8}{'用途':<14}{'注意'}")
for r in rows:
    print(f"  {r[0]:<8}{r[1]:<14}{r[2]}")

# ---- 注意 ----
print("\n== 注意 ==")
for item in [
    "pptx 图表是原生对象，可在 PowerPoint 里继续改数据",
    "数据量大时先在 pandas 聚合，再喂给图表（第28章）",
    "饼图类别太多会看不清，超过 5 类用柱状图",
    "颜色使用模板主题色，保持全篇一致",
    "图表标题要写“结论”而不只是“数据”",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 新增一个“退款率”折线图，双轴概念在 PPT 里通常拆成两张图。
# 2. 给柱状图加数据标签（data_labels.show_value）。
# 3. 把饼图改成环形图（DOUGHNUT）。
# 4. 思考：为什么 PPT 图表不直接放 1000 行原始数据？
