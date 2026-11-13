# ===== 第126课：网络机器人-入门-入门程序(网页解析) =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - requests 负责取回 HTML，lxml 负责提取结构化数据
#   - 解析函数与下载函数分离，便于离线测试和复用
#   - 用 "".join(...//text()) 可拼接嵌套标签内的全部文字
#   - 抓取前确认 robots 协议，控制请求频率
# 依赖：pip install requests lxml

import requests
from lxml import html

URL = "https://quotes.toscrape.com/"
HEADERS = {"User-Agent": "StudyBot/1.0 (Python course example)"}


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def parse_quotes(html_text: str) -> list:
    doc = html.fromstring(html_text)
    rows = []
    for item in doc.xpath("//div[@class='quote']"):
        text = "".join(item.xpath("./span[@class='text']//text()")).strip()
        author = item.xpath("./span/small[@class='author']/text()")
        tags = item.xpath("./div[@class='tags']//a[@class='tag']/text()")
        rows.append({
            "text": text,
            "author": author[0].strip() if author else "",
            "tags": ",".join(tags),
        })
    return rows


if __name__ == "__main__":
    html_text = fetch_html(URL)
    rows = parse_quotes(html_text)
    print("共解析", len(rows), "条")
    for row in rows[:3]:                      # 只展示前三条
        print("-", row["author"], row["text"])
        print("  标签：", row["tags"])

# ===== 练习题 =====
# 1. 把 parse_quotes 改为解析 books.toscrape.com 的书名和价格。
# 2. 为每条记录增加 detail_url 字段，值为相对链接补全后的绝对地址。
# 3. 统计本页所有标签（tag）出现的次数，按次数从高到低输出。
