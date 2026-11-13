# ===== 第134课：网络机器人-案例-数据清洗(正则入门) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 正则表达式用模式描述文本规律，适合抽取年份、评分、人数
#   - re.search 找第一个匹配，re.findall 返回全部匹配，re.sub 替换
#   - \d 数字，\w 单词字符，\s 空白；+ * ? {m,n} 控制重复次数
#   - 原始字符串 r"..." 可避免反斜杠被二次转义
# 依赖：无（仅使用 Python 标准库 re）

import re

RAW_TEXT = "上映年份：1994，评分：9.7分，评价人数：2,345,678人，地区：美国"


def extract_year(text: str) -> str:
    match = re.search(r"\d{4}", text)
    return match.group() if match else ""


def extract_rating(text: str) -> float:
    match = re.search(r"\d+\.\d+", text)
    return float(match.group()) if match else 0.0


def extract_votes(text: str) -> int:
    match = re.search(r"[\d,]+(?=人)", text)   # 前瞻：后面紧跟“人”
    return int(match.group().replace(",", "")) if match else 0


def clean_region(text: str) -> str:
    return re.sub(r"^.*地区：", "", text).strip()


if __name__ == "__main__":
    print("年份：", extract_year(RAW_TEXT))
    print("评分：", extract_rating(RAW_TEXT))
    print("评价人数：", extract_votes(RAW_TEXT))
    print("地区：", clean_region(RAW_TEXT))
    print("全部数字：", re.findall(r"\d+", RAW_TEXT))
    print("是否以“上映”开头：", bool(re.match(r"上映", RAW_TEXT)))

# ===== 练习题 =====
# 1. 从“片长：142分钟”中提取 142，并转换为整数。
# 2. 把“9.7分”清洗为浮点数 9.7，写出所用模式。
# 3. 用 re.sub 删除文本中的所有空白字符，观察结果。
