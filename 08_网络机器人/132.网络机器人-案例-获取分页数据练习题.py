# ===== 第132课：网络机器人-案例-获取分页数据 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 分页地址由页码换算偏移量：start = (page - 1) * page_size
#   - 循环抓取要有终止条件：达到最大页数或解析结果为空
#   - 页与页之间加 time.sleep，降低对站点的压力
#   - 多页结果用 extend 汇总，返回统一结构的列表
# 依赖：pip install requests lxml

import time
from urllib.parse import urljoin

import requests
from lxml import html

BASE_URL = "https://movie.example.com/top250"  # 说明性 URL
PAGE_SIZE = 25
HEADERS = {"User-Agent": "StudyBot/1.0 (Python course example)"}

SAMPLE_PAGE = """<ol class="grid_view">
  <li><div class="hd"><a href="/movie/{page}"><span class="title">第{page}页电影</span>
  </a></div><span class="rating_num">9.0</span></li>
</ol>"""


def build_page_url(page: int, page_size: int = PAGE_SIZE) -> str:
    return f"{BASE_URL}?start={(page - 1) * page_size}&filter="


def parse_list(html_text: str) -> list:
    if not html_text.strip():          # 空页面直接返回，避免解析报错
        return []
    doc = html.fromstring(html_text)
    rows = []
    for item in doc.xpath("//ol[@class='grid_view']/li"):
        title = item.xpath(".//span[@class='title']/text()")
        rating = item.xpath(".//span[@class='rating_num']/text()")
        href = item.xpath(".//div[@class='hd']/a/@href")
        rows.append({
            "title": title[0].strip() if title else "",
            "rating": float(rating[0]) if rating else 0.0,
            "detail_url": urljoin(BASE_URL, href[0]) if href else "",
        })
    return rows


def fetch_html(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


def crawl_pages(max_pages: int = 10, delay: float = 1.0) -> list:
    """按页抓取，结果为空时提前结束。"""
    all_rows = []
    for page in range(1, max_pages + 1):
        html_text = fetch_html(build_page_url(page))
        rows = parse_list(html_text)
        if not rows:
            break
        all_rows.extend(rows)
        time.sleep(delay)
    return all_rows

def demo_fetch(page: int) -> str:
    """离线演示：模拟第 1、2 页有数据，第 3 页为空。"""
    return SAMPLE_PAGE.format(page=page) if page <= 2 else ""


if __name__ == "__main__":
    rows = []
    for page in range(1, 4):
        page_rows = parse_list(demo_fetch(page))
        print("第", page, "页解析到", len(page_rows), "条")
        rows.extend(page_rows)
    print("共汇总", len(rows), "条，示例地址：", build_page_url(3))

# ===== 练习题 =====
# 1. 若每页 25 条，第 5 页的 start 是多少？
# 2. 为什么终止条件要同时检查空结果与 max_pages？
# 3. 给 crawl_pages 加 try/except，单页失败时记录并跳过该页。
