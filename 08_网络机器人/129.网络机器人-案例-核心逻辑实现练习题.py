# ===== 第129课：网络机器人-案例-核心逻辑实现 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 核心逻辑拆成“构造 URL → 请求 → 解析 → 返回记录”四步
#   - 列表页每条记录包含排名、标题、评分和详情页链接
#   - lxml 的 //ol[@class="grid_view"]/li 定位榜单条目
#   - urljoin 把相对详情链接补全为绝对地址
# 依赖：pip install requests lxml

from urllib.parse import urljoin

import requests
from lxml import html

BASE_URL = "https://movie.example.com/top250"  # 说明性 URL
HEADERS = {"User-Agent": "StudyBot/1.0 (Python course example)"}

SAMPLE_LIST_HTML = """<ol class="grid_view">
  <li><em class="">1</em><div class="hd"><a href="/movie/1">
    <span class="title">肖申克的救赎</span></a></div>
    <span class="rating_num">9.7</span></li>
  <li><em class="">2</em><div class="hd"><a href="/movie/2">
    <span class="title">霸王别姬</span></a></div>
    <span class="rating_num">9.6</span></li>
</ol>"""


def build_list_url(page: int, page_size: int = 25) -> str:
    """构造第 page 页的列表页地址。"""
    return f"{BASE_URL}?start={(page - 1) * page_size}&filter="


def fetch_html(url: str) -> str:
    """发送请求并返回 HTML 文本。"""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def parse_list(html_text: str) -> list:
    """解析列表页，返回记录列表。"""
    doc = html.fromstring(html_text)
    rows = []
    for item in doc.xpath("//ol[@class='grid_view']/li"):
        rank = item.xpath("./em/text()")
        title = item.xpath(".//span[@class='title']/text()")
        rating = item.xpath(".//span[@class='rating_num']/text()")
        href = item.xpath(".//div[@class='hd']/a/@href")
        rows.append({
            "rank": int(rank[0]) if rank else 0,
            "title": title[0].strip() if title else "",
            "rating": float(rating[0]) if rating else 0.0,
            "detail_url": urljoin(BASE_URL, href[0]) if href else "",
        })
    return rows


if __name__ == "__main__":
    # 先用本地样例验证解析逻辑，再替换为 fetch_html(build_list_url(1))
    records = parse_list(SAMPLE_LIST_HTML)
    for record in records:
        print(record)
    print("列表页地址示例：", build_list_url(2))

# ===== 练习题 =====
# 1. 说明 parse_list 中 ./ 与 .// 的区别，以及各自适用场景。
# 2. 为记录增加 rank 缺失时的兜底逻辑，并说明为什么要兜底。
# 3. 用 fetch_html 替换本地样例，抓取前先确认 robots 协议是否允许。
