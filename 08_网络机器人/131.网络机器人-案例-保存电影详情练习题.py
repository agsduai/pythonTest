# ===== 第131课：网络机器人-案例-保存电影详情 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 详情记录是字典，多个字典组成列表后可用 DictWriter 保存
#   - 字段顺序由 fieldnames 决定，写入前要保证每条记录键齐全
#   - 追加模式适合分批抓取，文件为空时才写表头
#   - 保存后立即读回抽样检查，可尽早发现编码或字段问题
# 依赖：无（仅使用 Python 标准库 csv、os）

import csv
import os

FIELDS = ["rank", "title", "year", "rating",
          "director", "actors", "region", "summary"]

MOVIES = [
    {"rank": 1, "title": "肖申克的救赎", "year": "1994", "rating": 9.7,
     "director": "弗兰克·德拉邦特", "actors": "蒂姆·罗宾斯 / 摩根·弗里曼",
     "region": "美国", "summary": "一场关于希望与自由的救赎之旅。"},
    {"rank": 2, "title": "霸王别姬", "year": "1993", "rating": 9.6,
     "director": "陈凯歌", "actors": "张国荣 / 张丰毅",
     "region": "中国", "summary": "两位京剧演员跨越时代的悲欢。"},
]


def normalize(record: dict) -> dict:
    """确保每个字段都存在，缺失值写空字符串。"""
    return {field: record.get(field, "") for field in FIELDS}


def save_movies(path: str, rows: list, append: bool = False) -> None:
    """保存电影详情；append=True 时追加写入。"""
    mode = "a" if append else "w"
    write_header = (not append) or (not os.path.exists(path)) or os.path.getsize(path) == 0
    with open(path, mode, encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerows(normalize(row) for row in rows)


def load_movies(path: str) -> list:
    with open(path, "r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


if __name__ == "__main__":
    path = "movies_detail.csv"
    save_movies(path, MOVIES)
    save_movies(path, MOVIES[:1], append=True)
    rows = load_movies(path)
    print("文件行数：", len(rows))
    print("第一条：", rows[0]["title"], rows[0]["rating"], rows[0]["region"])

# ===== 练习题 =====
# 1. 解释 newline="" 的作用，以及缺失时在 Windows 上会出现什么现象。
# 2. 改为 utf-8-sig 编码有什么好处？在什么场景下使用？
# 3. 增加去重逻辑：按 title 去重后再追加写入。
