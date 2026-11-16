# ===== 第644课：数据交换格式与协议设计-CSV与表格数据交换 =====
# 知识点：
#   - csv.reader / DictReader / writer / DictWriter；newline="" 必须加，否则 Windows 多空行
#   - delimiter / quotechar / quoting / escapechar：处理字段里的逗号、引号、换行
#   - 编码：中文 CSV 常用 utf-8-sig（带 BOM，Excel 直接打开不乱码）
#   - 类型全靠「约定」：CSV 没有类型，数字/日期/空值都要显式解析
#   - Sniffer 猜测方言（分隔符），但生产应显式声明而非猜
#   - 与 JSON 对比：CSV 更省空间、适合表格与追加写；缺类型、缺嵌套
# 依赖：无（标准库）
import csv
import io
import json
import tempfile
from pathlib import Path

rows = [
    {"id": 1, "name": "张三", "city": "北京", "score": 95.5, "note": "优秀"},
    {"id": 2, "name": "李四", "city": "上海", "score": 88.0, "note": "含,逗号"},
    {"id": 3, "name": "王五", "city": "广州", "score": None, "note": '带"引号"'},
]

print("== DictWriter 写内存文本 ==")
buf = io.StringIO(newline="")
w = csv.DictWriter(buf, fieldnames=["id", "name", "city", "score", "note"])
w.writeheader()
w.writerows(rows)
text = buf.getvalue()
print(text, end="")

print("\n== 特殊字符被自动引用 ==")
for line in text.splitlines()[1:]:
    print("  ", line)

print("\n== DictReader 读回（全部是字符串）==")
buf2 = io.StringIO(text, newline="")
read_back = list(csv.DictReader(buf2))
print("  行数:", len(read_back))
print("  首行:", read_back[0])
print("  score 的类型:", type(read_back[0]["score"]).__name__, "（CSV 不保留类型）")

print("\n== 显式类型转换 ==")
def parse_row(r):
    return {"id": int(r["id"]), "name": r["name"], "city": r["city"],
            "score": float(r["score"]) if r["score"] else None, "note": r["note"]}

parsed = [parse_row(r) for r in read_back]
print("  ", parsed[0])
print("  空值处理: score=None ->", parsed[2]["score"])

print("\n== 不同方言 ==")
for delim, quote in ((",", '"'), (";", '"'), ("\t", "'")):
    b = io.StringIO(newline="")
    wr = csv.writer(b, delimiter=delim, quotechar=quote, quoting=csv.QUOTE_MINIMAL)
    wr.writerow(["a,b", "c", "d"])
    print(f"  delimiter={delim!r:<6} quotechar={quote!r}: {b.getvalue().strip()!r}")

print("\n== Sniffer 猜方言 ==")
sample = "name;age;city\n张三;30;北京\n李四;25;上海\n"
try:
    dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    print(f"  猜到 delimiter={dialect.delimiter!r}")
    print("  读回:", list(csv.DictReader(io.StringIO(sample, newline=""), dialect=dialect)))
except csv.Error as e:
    print("  猜测失败:", e)
print("  注意：生产环境应显式 delimiter，Sniffer 只用于探索未知文件")

print("\n== BOM 与 Excel 兼容 ==")
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "中文.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["name", "city"])
        wr.writeheader(); wr.writerow({"name": "张三", "city": "北京"})
    print("  文件前 3 字节:", p.read_bytes()[:3].hex(" "), "（EF BB BF = UTF-8 BOM）")
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        print("  按 utf-8-sig 读:", list(csv.DictReader(f)))
    with p.open("r", encoding="utf-8", newline="") as f:
        first = f.readline()
        print("  按 utf-8 读表头:", repr(first), "（首字段会带 \\ufeff）")

print("\n== CSV vs JSON ==")
print("  CSV  体积:", len(text), "字符")
print("  JSON 体积:", len(json.dumps(rows, ensure_ascii=False)), "字符")
for line in (
    "  CSV : 省空间、可追加、Excel 友好；无类型/嵌套/模式约束",
    "  JSON: 有类型与嵌套、生态广；体积大、不能增量追加",
    "  选型: 表格导出用 CSV，API/配置用 JSON，海量列式分析用 Parquet",
):
    print(line)

print("\n== 常见坑 ==")
for line in [
    "open 必须带 newline=''，否则 Windows 上每行之间多一个空行",
    "字段含换行符也合法，但很多下游工具处理不好，尽量先清洗",
    "None / 空字符串 / 'NULL' 三种空值语义要在协议里写清楚",
    "大文件用生成器逐行 yield，别 list(reader) 全读入内存",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 实现 csv_to_json(path)，按显式 schema 把 CSV 转成带类型的 JSON。
# 2. 写一个流式过滤函数，只保留 score>=90 的行并写入新 CSV。
# 3. 处理含嵌入换行的字段，验证 csv.reader 能正确还原一条记录。
# 4. 思考：为什么 CSV 里「空值语义」必须由协议约定，而不能靠库自动推断？
