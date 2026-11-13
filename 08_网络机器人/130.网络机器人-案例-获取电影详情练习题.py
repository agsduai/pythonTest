# ===== 第130课：网络机器人-案例-获取电影详情 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 列表页只给摘要，导演、主演、地区、简介需进入详情页
#   - 详情页解析先定位容器，再逐字段提取，降低耦合
#   - 文本混有换行和多余空格，用 strip 与 join 初步整理
#   - 用 urljoin 由列表页链接得到可请求的绝对地址
# 依赖：pip install requests lxml

from urllib.parse import urljoin

import requests
from lxml import html

BASE_URL = "https://movie.example.com"  # 说明性 URL
HEADERS = {"User-Agent": "StudyBot/1.0 (Python course example)"}

SAMPLE_DETAIL_HTML = """<div class="movie-detail">
  <h1><span class="title">肖申克的救赎</span><span class="year">(1994)</span></h1>
  <strong class="rating_num">9.7</strong>
  <div class="info">
    <span class="director">导演: 弗兰克·德拉邦特</span>
    <span class="actor">主演: 蒂姆·罗宾斯 / 摩根·弗里曼</span>
    <span class="region">地区: 美国</span>
  </div>
  <div class="summary"><p>一场关于希望与自由的救赎之旅。</p></div>
</div>"""


def fetch_detail(detail_url: str) -> str:
    """请求详情页并返回 HTML。"""
    response = requests.get(detail_url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def parse_detail(html_text: str) -> dict:
    """解析详情页，返回字段字典。"""
    doc = html.fromstring(html_text)
    title = doc.xpath("//h1/span[@class='title']/text()")
    year = doc.xpath("//h1/span[@class='year']/text()")
    rating = doc.xpath("//strong[@class='rating_num']/text()")
    director = doc.xpath("//div[@class='info']/span[@class='director']/text()")
    actor = doc.xpath("//div[@class='info']/span[@class='actor']/text()")
    region = doc.xpath("//div[@class='info']/span[@class='region']/text()")
    summary = doc.xpath("//div[@class='summary']//text()")
    return {
        "title": title[0].strip() if title else "",
        "year": year[0].strip("() ") if year else "",
        "rating": float(rating[0]) if rating else 0.0,
        "director": director[0].replace("导演:", "").strip() if director else "",
        "actors": actor[0].replace("主演:", "").strip() if actor else "",
        "region": region[0].replace("地区:", "").strip() if region else "",
        "summary": " ".join(summary).strip(),
    }


if __name__ == "__main__":
    print(parse_detail(SAMPLE_DETAIL_HTML))
    detail_url = urljoin(BASE_URL, "/movie/1")
    print("待抓取详情页：", detail_url)

# ===== 练习题 =====
# 1. 为什么先定位 //div[@class='info']，再取其中的 span？这样写有什么好处？
# 2. 详情页缺少 summary 时，parse_detail 应返回什么？请修改代码验证。
# 3. 增加字段 language，并从详情页 HTML 中补充对应的 span 后解析。
