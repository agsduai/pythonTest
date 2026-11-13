# ===== 第136课：网络机器人-案例-数据清洗(程序优化) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 把反复使用的模式预编译为模块级常量，避免循环内重复编译
#   - 拆分“单字段清洗”和“整条记录清洗”，职责单一便于测试
#   - 用列表推导式批量处理，代码更简洁
#   - 用 time.perf_counter 对比优化前后的耗时，验证效果
# 依赖：无（仅使用 Python 标准库 re、time）

import re
import time

YEAR_RE = re.compile(r"(19|20)\d{2}")
RATING_RE = re.compile(r"\d+(?:\.\d+)?")
VOTES_RE = re.compile(r"[\d,]+(?=\s*人)")
SPACE_RE = re.compile(r"\s+")
TAG_RE = re.compile(r"<[^>]+>")

RAW_MOVIES = [
    {"title": " 肖申克的救赎 ", "year": "(1994)", "rating": "9.7分",
     "votes": "2,345,678人评价", "summary": "<p>希望让人自由。</p>"},
    {"title": "霸王别姬", "year": "1993年", "rating": "9.6",
     "votes": "1,876,543人评价", "summary": "<p>人生如戏。</p>"},
]


def clean_text(text: str) -> str:
    """去标签、压缩空白、去首尾空格。"""
    return SPACE_RE.sub(" ", TAG_RE.sub("", text)).strip()


def parse_year(text: str) -> int:
    match = YEAR_RE.search(text)
    return int(match.group()) if match else 0


def parse_rating(text: str) -> float:
    match = RATING_RE.search(text)
    return float(match.group()) if match else 0.0


def parse_votes(text: str) -> int:
    match = VOTES_RE.search(text)
    return int(match.group().replace(",", "")) if match else 0


def clean_movie(raw: dict) -> dict:
    """单条记录清洗：字段缺失时返回默认值。"""
    return {
        "title": clean_text(raw.get("title", "")),
        "year": parse_year(raw.get("year", "")),
        "rating": parse_rating(raw.get("rating", "")),
        "votes": parse_votes(raw.get("votes", "")),
        "summary": clean_text(raw.get("summary", "")),
    }


def clean_all(rows: list) -> list:
    return [clean_movie(row) for row in rows]


if __name__ == "__main__":
    start = time.perf_counter()
    cleaned = clean_all(RAW_MOVIES)
    cost = time.perf_counter() - start
    for row in cleaned:
        print(row)
    print(f"清洗 {len(cleaned)} 条耗时：{cost:.4f} 秒")

# ===== 练习题 =====
# 1. 为什么把 re.compile 放在循环外？用 1 万条数据对比耗时验证。
# 2. 给 clean_movie 增加异常兜底，单条脏数据不应中断整批清洗。
# 3. 把结果写入 CSV，字段顺序固定为 title/year/rating/votes/summary。
