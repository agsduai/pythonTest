# ===== 第289课：办公自动化-Word模板填充 =====
# 知识点：
#   - 模板思路：先做含 {占位符} 的模板，再逐人替换生成
#   - 替换要作用在 run 上：Word 可能把一句话拆成多个 run
#   - 保险做法：整段替换（清空 runs 后重写），避免拆分带来的遗漏
# 依赖：pip install python-docx

import glob
import os

from docx import Document

# ---- 1. 生成模板 ----
doc = Document()
doc.add_heading("表扬信", level=1)
doc.add_paragraph("尊敬的 {name} 同学：")
doc.add_paragraph("你在 {course} 课程中取得 {score} 分的好成绩，特此表扬！")
doc.add_paragraph("课程组")
doc.save("template_289.docx")
print("模板已生成：template_289.docx")

# ---- 2. 逐人填充 ----
students = [
    ("小明", "Python进阶", 95),
    ("小红", "Python进阶", 92),
]


def fill_doc(template_path, out_path, mapping):
    """把模板里的 {占位符} 替换成 mapping 的值。"""
    d = Document(template_path)
    for paragraph in d.paragraphs:
        # 做法①：优先在 run 内替换（大多数情况够用）
        for run in paragraph.runs:
            for key, value in mapping.items():
                if key in run.text:
                    run.text = run.text.replace(key, value)
        # 做法②：run 替换后仍残留占位符 → 整段重写（防 run 拆分）
        text = "".join(run.text for run in paragraph.runs)
        for key, value in mapping.items():
            text = text.replace(key, value)
        if text != "".join(run.text for run in paragraph.runs):
            for run in paragraph.runs:
                run.text = ""
            paragraph.runs[0].text = text if paragraph.runs else text
    d.save(out_path)


for name, course, score in students:
    fill_doc(
        "template_289.docx",
        f"通知_{name}.docx",
        {"{name}": name, "{course}": course, "{score}": str(score)},
    )
    print(f"已生成 通知_{name}.docx")

# ---- 3. 验证生成结果 ----
check = Document("通知_小明.docx")
for p in check.paragraphs:
    if "同学" in p.text:
        print("抽查：", p.text)

for f in glob.glob("通知_*.docx") + ["template_289.docx"]:
    os.remove(f)

# ===== 练习题 =====
# 1. 模板里加一个 {date} 占位符，填充时用 datetime.now() 自动填当天。
# 2. 用 Excel 名单驱动批量生成 10 份通知（结合第285课）。
# 3. 思考：为什么 Word 会把一句话拆成多个 run？（提示：拼写检查、局部格式）
