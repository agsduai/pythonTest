# ===== 第127课：网络机器人-案例-csv操作 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - csv 是逗号分隔的纯文本表格格式，适合保存爬取结果
#   - csv.DictWriter 按字段名写入，writerow/writerows 写入一行/多行
#   - open 时必须用 newline=""，否则 Windows 会出现空行
#   - 用 encoding="utf-8" 保存中文；DictReader 读取时返回字典
# 依赖：无（仅使用 Python 标准库 csv）

import csv

FIELDS = ["rank", "title", "year", "rating"]
MOVIES = [
    {"rank": 1, "title": "肖申克的救赎", "year": 1994, "rating": 9.7},
    {"rank": 2, "title": "霸王别姬", "year": 1993, "rating": 9.6},
    {"rank": 3, "title": "阿甘正传", "year": 1994, "rating": 9.5},
]


def save_csv(path: str, rows: list, fields: list) -> None:
    """覆盖写入 CSV，并写表头。"""
    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path: str, rows: list, fields: list) -> None:
    """追加写入；文件为空时才补表头。"""
    with open(path, "a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        if file.tell() == 0:
            writer.writeheader()
        writer.writerows(rows)


def read_csv(path: str) -> list:
    with open(path, "r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


if __name__ == "__main__":
    path = "movies_demo.csv"
    save_csv(path, MOVIES, FIELDS)
    append_csv(path, [{"rank": 4, "title": "泰坦尼克号", "year": 1997, "rating": 9.5}], FIELDS)
    rows = read_csv(path)
    print("共读取", len(rows), "行")
    for row in rows:
        print(row["rank"], row["title"], row["year"], row["rating"])

# ===== 练习题 =====
# 1. 解释 newline="" 的作用，以及缺失时在 Windows 上的表现。
# 2. 增加函数 update_csv，按 title 找到记录并修改 rating。
# 3. 将字段顺序改为 rating、title、year、rank，观察表头与数据的关系。
