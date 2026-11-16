# ===== 第665课：模板引擎与文本生成-多格式输出与报表渲染 =====
# 知识点：
#   - 同一份「报表模型」渲染成 text / Markdown / HTML / CSV，逻辑只写一遍
#   - 分层：数据模型（rows + meta）-> 格式化器（按输出格式）-> 模板（可选包装）
#   - 输出格式各管各的转义：纯文本不转义、HTML 要 escape、CSV 要引用逗号
#   - 渲染器接口统一为 render(report, sink)，sink 可注入（StringIO/文件）
#   - 表格列宽按「显示宽度」算，中文占 2 列（第607课 east_asian_width）
#   - 内容协商：HTTP Accept / CLI --format 决定用哪个渲染器
# 依赖：无（标准库）
import csv
import html
import io
import json
import unicodedata
from dataclasses import dataclass, field


@dataclass
class Report:
    title: str
    columns: list
    rows: list
    meta: dict = field(default_factory=dict)


def display_width(s):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in str(s))


def pad(s, width):
    return str(s) + " " * max(0, width - display_width(s))


def render_text(r, sink):
    widths = [max([display_width(c)] + [display_width(row[i]) for row in r.rows])
              for i, c in enumerate(r.columns)]
    print(r.title, file=sink)
    print("  ".join(pad(c, w) for c, w in zip(r.columns, widths)), file=sink)
    print("  ".join("-" * w for w in widths), file=sink)
    for row in r.rows:
        print("  ".join(pad(v, w) for v, w in zip(row, widths)), file=sink)


def render_markdown(r, sink):
    print(f"# {r.title}", file=sink)
    print("", file=sink)
    print("| " + " | ".join(r.columns) + " |", file=sink)
    print("|" + "|".join("---" for _ in r.columns) + "|", file=sink)
    for row in r.rows:
        print("| " + " | ".join(str(v) for v in row) + " |", file=sink)


def render_html(r, sink):
    print("<!doctype html><meta charset='utf-8'>", file=sink)
    print(f"<h1>{html.escape(r.title)}</h1>", file=sink)
    print("<table border='1'><thead><tr>", file=sink)
    for c in r.columns:
        print(f"<th>{html.escape(str(c))}</th>", end="", file=sink)
    print("</tr></thead><tbody>", file=sink)
    for row in r.rows:
        print("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in row) + "</tr>",
              file=sink)
    print("</tbody></table>", file=sink)


def render_csv(r, sink):
    w = csv.writer(sink, lineterminator="\n")
    w.writerow(r.columns)
    w.writerows(r.rows)


def render_json(r, sink):
    json.dump({"title": r.title, "columns": r.columns,
               "rows": [dict(zip(r.columns, row)) for row in r.rows], "meta": r.meta},
              sink, ensure_ascii=False, indent=2)


RENDERERS = {"text": render_text, "md": render_markdown, "html": render_html,
             "csv": render_csv, "json": render_json}

report = Report(
    title="月度销售 <报表>",
    columns=["产品", "销量", "单价", "备注"],
    rows=[["键盘", 120, 199, "含,逗号"], ["鼠标", 300, 89, '<b>热销</b>'],
          ["显示器", 45, 1299, "中文宽度"]],
    meta={"period": "2026-11", "generated_by": "demo"},
)

print("== 同一份 Report，五种输出 ==")
for fmt, fn in RENDERERS.items():
    buf = io.StringIO()
    fn(report, buf)
    print(f"\n--- {fmt} ({len(buf.getvalue())} 字符) ---")
    print(buf.getvalue(), end="" if fmt != "json" else "\n")

print("\n== 转义正确性 ==")
buf = io.StringIO(); render_html(report, buf)
h = buf.getvalue()
print("  HTML 标题被转义:", "&lt;报表&gt;" in h)
print("  HTML 单元格 <b> 被转义:", "&lt;b&gt;热销&lt;/b&gt;" in h)
print("  原始 <script> 不出现:", "<b>热销</b>" not in h)

buf = io.StringIO(); render_csv(report, buf)
c = buf.getvalue()
print("  CSV 含逗号字段被引用:", '"含,逗号"' in c)
import csv as _csv
print("  CSV 可无损读回:", list(_csv.reader(io.StringIO(c)))[3][3] == "含,逗号")

print("\n== 中文显示宽度对齐 ==")
buf = io.StringIO(); render_text(report, buf)
for line in buf.getvalue().splitlines()[:4]:
    print("  ", repr(line))

print("\n== 内容协商 ==")
def choose_renderer(accept):
    prefs = [p.strip().split(";")[0] for p in accept.split(",")]
    mapping = {"text/html": "html", "text/markdown": "md", "text/csv": "csv",
               "application/json": "json", "text/plain": "text"}
    for p in prefs:
        if p in mapping:
            return mapping[p]
    return "text"

for accept in ("text/html,application/json", "application/json", "text/plain", "*/*"):
    print(f"  Accept: {accept:<34} -> {choose_renderer(accept)}")

print("\n== 分层收益 ==")
for line in [
    "  数据模型与格式解耦：新增一种输出只加一个渲染函数",
    "  转义责任在渲染层：不会污染数据，也不会漏掉某种格式",
    "  sink 可注入：单测用 StringIO，生产直接写文件/HTTP 响应",
    "  同一 report 可同时产出邮件正文(text) + 附件(csv) + 归档(json)",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 增加 render_latex 与 render_excel_xml，验证转义规则各不相同。
# 2. 给 Report 增加「合计行」，让五种渲染器都正确输出它。
# 3. 实现按 Accept 权重 q= 排序的内容协商，而不只是取第一个匹配。
# 4. 思考：为什么转义逻辑必须放在渲染层，而不是提前写进数据模型？
