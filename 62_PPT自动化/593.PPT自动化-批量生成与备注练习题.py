# ===== 第593课：PPT自动化-批量生成与备注 =====
# 知识点：
#   - 批量生成：一份模板 + 一组数据 → 多个 .pptx
#   - 备注（notes）：备注页不属于放映画面，用来写讲稿/提示
#   - slide.notes_slide.notes_text_frame.text = "讲稿"
#   - 文件命名要可追溯（姓名/日期/版本）
#   - 生成后做“存在性 + 页数 + 关键文本”校验
#   - 与第23章批量工资条（第287课）、第51章批量打包的思路一致
# 依赖：pip install python-pptx

import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.util import Pt


def build_template(path: Path):
    prs = Presentation()
    s0 = prs.slides.add_slide(prs.slide_layouts[0])
    s0.shapes.title.text = "绩效面谈"
    s0.placeholders[1].text = "2026 年 11 月"
    s1 = prs.slides.add_slide(prs.slide_layouts[1])
    s1.shapes.title.text = "{姓名} 的绩效摘要"
    s1.placeholders[1].text = "{内容}"
    prs.save(path)


def generate(template: Path, out_dir: Path, person: dict) -> Path:
    prs = Presentation(template)
    slide = prs.slides[1]
    slide.shapes.title.text = f"{person['name']} 的绩效摘要"

    tf = slide.placeholders[1].text_frame
    tf.text = f"得分：{person['score']}"
    for line in person["highlights"]:
        p = tf.add_paragraph()
        p.text = f"· {line}"
        p.font.size = Pt(18)

    # 备注：讲稿提示，不出现在幻灯片上
    notes = slide.notes_slide.notes_text_frame
    notes.text = f"面谈提示：{person['name']} 得分 {person['score']}，"
    if person["score"] >= 90:
        notes.text += "重点肯定，讨论晋升。"
    else:
        notes.text += "先认可亮点，再一起制定改进计划。"

    out = out_dir / f"{person['name']}_绩效面谈.pptx"
    prs.save(out)
    return out


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    template = tmp / "template.pptx"
    out_dir = tmp / "output"
    out_dir.mkdir()
    build_template(template)

    people = [
        {"name": "小明", "score": 92, "highlights": ["完成核心项目", "代码质量高"]},
        {"name": "小红", "score": 85, "highlights": ["客户满意度高", "跨部门协作好"]},
        {"name": "小刚", "score": 76, "highlights": ["按时交付", "需要加强测试意识"]},
    ]

    print("== 批量生成 ==")
    files = []
    for person in people:
        path = generate(template, out_dir, person)
        files.append(path)
        print(f"  {path.name}（{path.stat().st_size} 字节）")

    # ---- 校验 ----
    print("\n== 校验 ==")
    for path, person in zip(files, people):
        prs = Presentation(path)
        slide = prs.slides[1]
        title = slide.shapes.title.text
        notes = slide.notes_slide.notes_text_frame.text
        print(f"  {path.name}: 页数={len(prs.slides)}，"
              f"标题={title!r}")
        print(f"    备注：{notes}")

    total = sum(p.stat().st_size for p in files)
    print(f"\n  共 {len(files)} 个文件，总大小 {total / 1024:.1f} KB")

# ---- 批量生成清单 ----
print("\n== 批量生成清单 ==")
for item in [
    "数据先校验（姓名/分数/必填项），缺数据不生成",
    "文件名可追溯：姓名_主题_日期",
    "单个失败记录并继续，不要中断整批",
    "生成后抽查页数、关键文本、备注",
    "大量文件打包 zip 或上传对象存储（第277课）",
]:
    print("  -", item)

# ---- 备注技巧 ----
print("\n== 备注技巧 ==")
for item in [
    "备注写讲稿要点，不写逐字稿（避免照读）",
    "标注数据来源与可能被问到的问题",
    "不同受众可生成不同备注版本",
    "备注不会显示在放映画面，但导出 PDF 时可选包含",
]:
    print("  -", item)

# ===== 练习题 =====
# 1. 给每个人生成两页：绩效摘要 + 下季度目标。
# 2. 在备注里加入“数据来源”与“预期问题”。
# 3. 把生成的 PPT 打包成 zip（第277课）。
# 4. 思考：批量生成时，如何避免“模板改动导致旧数据错位”？
