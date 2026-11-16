# ===== 第592课：PPT自动化-模板与占位符 =====
# 知识点：
#   - 模板 = 预先设计好版式/配色/字体的 .pptx，代码只填内容
#   - 占位符（placeholder）：按 idx 或 placeholder_format.type 定位
#   - 常见占位符：title（标题）、subtitle（副标题）、body（正文）
#   - 用模板生成：Presentation(template_path) → 填占位符 → 另存
#   - 新增页仍可用模板自带的 slide_layouts
#   - 与第23章 Word 模板填充（第289课）的思路一致
# 依赖：pip install python-pptx

import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.util import Pt


def build_template(path: Path):
    """制作一个简单模板：标题页 + 内容页。"""
    prs = Presentation()
    # 标题页
    s0 = prs.slides.add_slide(prs.slide_layouts[0])
    s0.shapes.title.text = "{标题}"
    s0.placeholders[1].text = "{副标题}"
    # 内容页
    s1 = prs.slides.add_slide(prs.slide_layouts[1])
    s1.shapes.title.text = "{章节标题}"
    s1.placeholders[1].text = "{正文内容}"
    prs.save(path)
    print("模板已生成：", path.name)


def fill_template(template: Path, output: Path, data: dict):
    prs = Presentation(template)
    title_slide = prs.slides[0]
    title_slide.shapes.title.text = data["title"]
    title_slide.placeholders[1].text = data["subtitle"]
    title_slide.placeholders[1].text_frame.paragraphs[0].font.size = Pt(18)

    content_slide = prs.slides[1]
    content_slide.shapes.title.text = data["section"]
    content_slide.placeholders[1].text = data["body"]
    # 正文逐段设置字号
    for para in content_slide.placeholders[1].text_frame.paragraphs:
        para.font.size = Pt(20)

    # 追加一页“总结”，仍使用模板版式
    extra = prs.slides.add_slide(prs.slide_layouts[1])
    extra.shapes.title.text = "总结"
    extra.placeholders[1].text = data["summary"]

    prs.save(output)
    print(f"  已生成 {output.name}（{len(prs.slides)} 页）")


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    template = tmp / "template.pptx"
    build_template(template)

    reports = [
        {
            "title": "技术部月报",
            "subtitle": "2026 年 11 月",
            "section": "本月进展",
            "body": "完成数据平台迁移\n上线实时通知服务\n修复 12 个线上问题",
            "summary": "下月重点：性能优化与安全加固",
        },
        {
            "title": "市场部月报",
            "subtitle": "2026 年 11 月",
            "section": "本月活动",
            "body": "完成 3 场线上活动\n新增线索 1200 条\n转化率提升 2.1pp",
            "summary": "下月重点：渠道拓展与内容运营",
        },
    ]

    print("\n== 基于模板生成 ==")
    outputs = []
    for i, data in enumerate(reports, 1):
        out = tmp / f"report_{i}.pptx"
        fill_template(template, out, data)
        outputs.append((out, data))

    # ---- 读回验证 ----
    print("\n== 读回内容 ==")
    for out, data in outputs:
        loaded = Presentation(out)
        print(f"\n  {out.name}：")
        for index, slide in enumerate(loaded.slides, 1):
            texts = []
            for shape in slide.shapes:
                if shape.has_text_frame and shape.text.strip():
                    texts.append(shape.text.replace("\n", " / "))
            print(f"    第{index}页：{texts}")

# ---- 模板使用清单 ----
print("\n== 模板使用清单 ==")
for item in [
    "模板放固定目录，版本化（第297/502课）",
    "占位符命名/顺序要稳定，代码按 idx 填",
    "颜色/字体在模板里定，代码不硬编码样式",
    "新增页用模板自带版式，保持风格统一",
    "生成后检查溢出：文字过长会超出占位符",
]:
    print("  -", item)

# ---- 常见问题 ----
print("\n== 常见问题 ==")
for item in [
    "placeholder 不存在 → KeyError/IndexError，先打印 idx 与类型",
    "文字太多溢出 → 缩短内容或缩小字号/增大占位符",
    "模板改了版式 → 旧代码按 idx 可能错位，需要回归测试",
    "字体缺失 → 接收方电脑没有该字体，用常见字体或嵌入",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给模板再加一页“图表页”版式，并在生成时填入数据。
# 2. 用 placeholder_format.type 而不是 idx 定位占位符。
# 3. 生成 10 份报告并统计总大小。
# 4. 思考：为什么“模板 + 代码填充”比“完全从零画每一页”更稳？
