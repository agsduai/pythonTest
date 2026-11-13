# ===== 第288课：办公自动化-Word文档生成 =====
# 知识点：
#   - python-docx：程序化生成 .docx 报告
#   - add_heading 标题（level 0=大标题）、add_paragraph 段落
#   - add_table 表格；table.style = "Table Grid" 加边框线
#   - 生成的文档与手工排版完全一致，可交给 Word/WPS 打开
# 依赖：pip install python-docx

import os

from docx import Document

doc = Document()

# 大标题（level=0）与一级标题
doc.add_heading("月度学习报告", level=0)
doc.add_heading("一、学习概况", level=1)
doc.add_paragraph("本月完成 Python 进阶课程学习，涵盖并发、数据库与测试等章节，整体进度符合预期。")

doc.add_heading("二、成绩明细", level=1)

# 表格：先建 1 行 2 列的表头，再逐行追加
table = doc.add_table(rows=1, cols=2)
table.style = "Table Grid"                  # 自带样式：全边框
header = table.rows[0].cells
header[0].text = "章节"
header[1].text = "得分"
for name, score in [
    ("装饰器与生成器", "95"),
    ("并发编程", "88"),
    ("数据库操作", "92"),
]:
    row = table.add_row().cells
    row[0].text = name
    row[1].text = score

doc.add_heading("三、小结", level=1)
doc.add_paragraph("继续保持节奏，下月进入算法与设计模式章节。")

doc.save("report_288.docx")
print("已生成 report_288.docx（标题/段落/表格齐全）")

# 说明：doc.add_paragraph 返回段落对象，段落里可以继续加带样式的 run
p = doc.add_paragraph("运行时提示：")
p.add_run("这份文档完全由代码生成。").bold = True
doc.save("report_288.docx")
print("追加粗体 run 后重新保存")

os.remove("report_288.docx")

# ===== 练习题 =====
# 1. 给报告加页眉页脚（提示：doc.sections[0].header / footer）。
# 2. 从 Excel 成绩表读数据，自动生成每位学生的 Word 成绩单（结合第287课）。
# 3. 思考：run 和 paragraph 是什么关系？为什么改字体要先拿到 run？
