# ===== 第135课：网络机器人-案例-数据清洗(正则表达式) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 分组 (...)：提取子串；命名分组 (?P<name>...) 让结果可读
#   - 贪婪 .* 会尽量多匹配，.*? 为非贪婪，适合截取标签内文本
#   - re.S 让 . 匹配换行，便于处理多行简介
#   - re.compile 预编译模式，重复使用更清晰、更高效
# 依赖：无（仅使用 Python 标准库 re）

import re

INFO_TEXT = "导演: 弗兰克·德拉邦特  主演: 蒂姆·罗宾斯 / 摩根·弗里曼  年份: 1994  地区: 美国"
SUMMARY_HTML = "<div class='summary'><p>希望让人自由。</p>\n<p>恐惧让人囚禁。</p></div>"

INFO_PATTERN = re.compile(
    r"导演:\s*(?P<director>.+?)\s+主演:\s*(?P<actors>.+?)\s+"
    r"年份:\s*(?P<year>\d{4})\s+地区:\s*(?P<region>\S+)"
)


def parse_info(text: str) -> dict:
    match = INFO_PATTERN.search(text)
    return match.groupdict() if match else {}


def extract_summary(html_text: str) -> str:
    paragraphs = re.findall(r"<p>(.*?)</p>", html_text, flags=re.S)
    return " ".join(re.sub(r"\s+", " ", p).strip() for p in paragraphs)


def clean_movie(record: dict) -> dict:
    """对解析后的记录做二次清洗。"""
    cleaned = dict(record)
    cleaned["director"] = re.sub(r"\s+", " ", cleaned.get("director", "")).strip()
    cleaned["actors"] = re.sub(r"\s*/\s*", " / ", cleaned.get("actors", "")).strip()
    year = cleaned.get("year", "")
    cleaned["year"] = int(year) if str(year).isdigit() else 0
    return cleaned


if __name__ == "__main__":
    info = parse_info(INFO_TEXT)
    print("命名分组结果：", info)
    print("清洗后：", clean_movie(info))
    print("简介：", extract_summary(SUMMARY_HTML))
    for match in re.finditer(r"\d{4}", INFO_TEXT):
        print("年份位置：", match.start(), match.end(), match.group())

# ===== 练习题 =====
# 1. 把 INFO_PATTERN 中的 .+? 改成 .+ 会发生什么？用实际文本验证。
# 2. 为“主演”拆分出演员列表，去掉多余空格并按“/”分隔。
# 3. 编写模式，从“1234人评价”中提取数字并转为整数。
