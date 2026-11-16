# ===== 第452课：ETL与数据质量-抽取层统一接口 =====
# 知识点：
#   - 抽取器统一接口：extract() -> list[dict]，调用方不关心数据来自哪
#   - CSV、Excel、SQLite、API 各写一个适配器（第262课适配器思想）
#   - 分页 API：循环翻页直到没有下一页，记录每页条数
#   - 统一输出“记录字典”，为后续转换层保持稳定契约
#   - 真实项目还要处理：编码、表头不一致、超时、限流（第446课）
import csv
import sqlite3
import tempfile
from pathlib import Path
from typing import Protocol

from openpyxl import Workbook

# ---------------- 接口 ----------------
class Extractor(Protocol):
    name: str

    def extract(self) -> list[dict]: ...


# ---------------- CSV ----------------
class CsvExtractor:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.name = f"csv:{self.path.name}"

    def extract(self) -> list[dict]:
        with open(self.path, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))


# ---------------- Excel ----------------
class ExcelExtractor:
    def __init__(self, path: Path, sheet: str | None = None):
        self.path = Path(path)
        self.sheet = sheet
        self.name = f"excel:{self.path.name}"

    def extract(self) -> list[dict]:
        from openpyxl import load_workbook
        wb = load_workbook(self.path, data_only=True)
        ws = wb[self.sheet] if self.sheet else wb.active
        rows = list(ws.iter_rows(values_only=True))
        headers = [str(h) for h in rows[0]]
        return [dict(zip(headers, row)) for row in rows[1:]]


# ---------------- SQLite ----------------
class SqlExtractor:
    def __init__(self, conn: sqlite3.Connection, query: str, params=()):
        self.conn = conn
        self.query = query
        self.params = params
        self.name = "sqlite"

    def extract(self) -> list[dict]:
        self.conn.row_factory = sqlite3.Row
        rows = self.conn.execute(self.query, self.params).fetchall()
        return [dict(r) for r in rows]


# ---------------- API（模拟分页） ----------------
class FakePagedApi:
    """模拟分页接口：每页 3 条，共 7 条。"""

    def __init__(self):
        self.data = [{"id": i, "name": f"用户{i}"} for i in range(1, 8)]

    def fetch_page(self, page: int, size: int = 3) -> dict:
        start = (page - 1) * size
        items = self.data[start:start + size]
        return {
            "items": items,
            "page": page,
            "has_next": start + size < len(self.data),
        }


class ApiExtractor:
    def __init__(self, api: FakePagedApi, size: int = 3):
        self.api = api
        self.size = size
        self.name = "api"

    def extract(self) -> list[dict]:
        page, records = 1, []
        while True:
            resp = self.api.fetch_page(page, self.size)
            records.extend(resp["items"])
            print(f"    第 {page} 页：{len(resp['items'])} 条")
            if not resp["has_next"]:
                break
            page += 1
        return records


# ---------------- 演示 ----------------
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    # 准备 CSV
    csv_path = tmp / "users.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "city"])
        writer.writerow([1, "小明", "北京"])
        writer.writerow([2, "小红", "上海"])

    # 准备 Excel
    xlsx_path = tmp / "users.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["id", "name", "city"])
    ws.append([3, "小刚", "广州"])
    ws.append([4, "小丽", "深圳"])
    wb.save(xlsx_path)

    # 准备 SQLite
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INT, name TEXT, city TEXT)")
    conn.executemany("INSERT INTO users VALUES (?, ?, ?)",
                     [(5, "小强", "杭州"), (6, "小美", "成都")])

    extractors: list[Extractor] = [
        CsvExtractor(csv_path),
        ExcelExtractor(xlsx_path),
        SqlExtractor(conn, "SELECT * FROM users WHERE id > ?", (4,)),
        ApiExtractor(FakePagedApi()),
    ]

    print("== 统一抽取 ==")
    all_records = []
    for extractor in extractors:
        print(f"\n  [{extractor.name}]")
        records = extractor.extract()
        print(f"    共 {len(records)} 条：{records[:2]}{' …' if len(records) > 2 else ''}")
        all_records.extend(records)

    print(f"\n合计抽取：{len(all_records)} 条")
    print("统一字段示例：", all_records[0])

    conn.close()

# 对比：没有统一接口时，调用方要写 if 判断数据来源，新增来源就要改代码
# 有统一接口后，新增 Kafka/HTTP/日志文件抽取器只需实现 extract()

# ===== 练习题 =====
# 1. 给 CsvExtractor 增加“列名映射”参数（源列名 → 标准字段名）。
# 2. 实现 RetryExtractor：包装任意抽取器，失败自动重试（第443课）。
# 3. 给 ApiExtractor 增加 rate_limit：每页之间 sleep。
# 4. 思考：抽取层要不要做数据清洗？为什么？（提示：职责边界）
