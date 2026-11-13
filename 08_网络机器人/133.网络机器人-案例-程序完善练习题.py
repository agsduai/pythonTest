# ===== 第133课：网络机器人-案例-程序完善 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - requests.Session 复用连接并统一请求头
#   - HTTPAdapter + Retry 对 429/5xx 做有限次退避重试
#   - logging 记录页码、状态码和异常，比 print 更易排查
#   - 单页失败不应中断整个任务，异常要捕获并记录
# 依赖：pip install requests

import logging
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("movie_bot")

HEADERS = {"User-Agent": "StudyBot/1.0 (Python course example)"}


def build_session() -> requests.Session:
    """创建带重试策略的会话。"""
    session = requests.Session()
    retry = Retry(
        total=3,                              # 最多重试 3 次
        backoff_factor=0.5,                   # 退避等待：0.5s, 1s, 2s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session


def fetch(session: requests.Session, url: str) -> str:
    """请求单页；失败返回空字符串，由调用方决定是否跳过。"""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except requests.RequestException as error:
        logger.warning("请求失败 %s：%s", url, error)
        return ""


def crawl(session: requests.Session, urls: list, delay: float = 1.0) -> list:
    """依次抓取多个地址，跳过失败项。"""
    results = []
    for url in urls:
        html_text = fetch(session, url)
        if not html_text:
            continue
        results.append(html_text)
        logger.info("成功 %s（%d 字符）", url, len(html_text))
        time.sleep(delay)
    return results


if __name__ == "__main__":
    session = build_session()
    urls = ["https://example.com", "https://example.com/not-found"]
    pages = crawl(session, urls, delay=0)
    print("成功抓取页数：", len(pages))

# ===== 练习题 =====
# 1. 解释 Retry 的 total 与 backoff_factor 分别控制什么。
# 2. 把失败页面的 URL 收集到 failed 列表，循环结束后统一重试。
# 3. 将日志写入 crawl.log 文件，同时保留控制台输出。
