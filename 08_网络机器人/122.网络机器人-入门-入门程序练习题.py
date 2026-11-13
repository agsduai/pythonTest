# ===== 第122课：网络机器人-入门-入门程序 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - requests.get 发送 GET 请求，timeout 防止程序无限等待
#   - raise_for_status 检查 HTTP 状态码，4xx/5xx 抛异常
#   - response.text 是解码后的网页文本，编码可由 apparent_encoding 推断
#   - 抓取结果应落盘保存，便于后续解析与复查
# 依赖：pip install requests

import requests

URL = "https://quotes.toscrape.com/"   # 公开的练习用抓取站点
HEADERS = {
    "User-Agent": "StudyBot/1.0 (Python course; contact: example@example.com)"
}


def download(url: str, path: str) -> tuple:
    """下载网页并以 UTF-8 保存，返回（状态码，字符数）。"""
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    html = response.text
    with open(path, "w", encoding="utf-8") as file:
        file.write(html)
    return response.status_code, len(html)


if __name__ == "__main__":
    status, size = download(URL, "quotes_index.html")
    print("HTTP 状态码：", status)
    print("保存字符数：", size)
    print("文件位置：当前目录/quotes_index.html")

# ===== 练习题 =====
# 1. 解释 timeout 与 raise_for_status 各自解决了什么问题。
# 2. 增加一个参数，让 download 可以自定义保存文件名。
# 3. 抓取前先打印 response.headers.get("Content-Type")，观察返回类型。
