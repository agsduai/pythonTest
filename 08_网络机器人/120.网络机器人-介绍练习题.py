# ===== 第120课：网络机器人-介绍 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 网络机器人（爬虫）是按照规则自动获取网页数据的程序
#   - 基本流程：发送请求 → 获取响应 → 解析网页 → 保存数据
#   - 常见用途：搜索引擎索引、比价、舆情分析、数据集构建
#   - 开发前提：遵守 robots 协议、网站条款和法律法规，控制访问频率
# 依赖：pip install requests

import requests


def fetch_page(url: str) -> str:
    """获取网页文本，返回 HTML 字符串。"""
    headers = {"User-Agent": "StudyBot/1.0 (Python course example)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()                       # 4xx/5xx 时抛出异常
    response.encoding = response.apparent_encoding    # 依据内容推断编码
    return response.text


def crawl_once(url: str) -> dict:
    """演示“请求 → 响应”两步，返回本次抓取的概况。"""
    html = fetch_page(url)
    return {"url": url, "chars": len(html), "preview": html[:60]}


if __name__ == "__main__":
    # 使用公开示例站点，避免给真实业务站点造成压力
    info = crawl_once("https://example.com")
    print("抓取地址：", info["url"])
    print("网页字符数：", info["chars"])
    print("内容预览：", info["preview"].replace("\n", " "))

# ===== 练习题 =====
# 1. 用一句话概括网络机器人的四个基本步骤，并说明每一步的产出。
# 2. 修改 fetch_page，使其返回状态码和 HTML 文本组成的元组。
# 3. 思考：为什么抓取前要先查看目标站点的 robots 协议？
