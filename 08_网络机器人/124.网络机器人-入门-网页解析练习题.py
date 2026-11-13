# ===== 第124课：网络机器人-入门-网页解析 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - 网页解析 = 从 HTML 中定位节点并提取文本/属性
#   - lxml.html.fromstring 把 HTML 文本转成元素树
#   - XPath 用路径表达式定位，如 //div[@class="quote"]
#   - 解析结果通常组织成字典或列表，便于保存与复用
# 依赖：pip install lxml

from lxml import html

HTML_SAMPLE = """<div class="quote-list">
  <div class="quote">
    <span class="text">“生活不是等待暴风雨过去。”</span>
    <span class="author">示例作者甲</span>
  </div>
  <div class="quote">
    <span class="text">“每一步都算数。”</span>
    <span class="author">示例作者乙</span>
  </div>
</div>"""


def parse_quotes(html_text: str) -> list:
    """解析名言列表，返回字典组成的列表。"""
    doc = html.fromstring(html_text)
    result = []
    for item in doc.xpath("//div[@class='quote']"):
        text = item.xpath("./span[@class='text']/text()")
        author = item.xpath("./span[@class='author']/text()")
        result.append({
            "text": text[0].strip() if text else "",
            "author": author[0].strip() if author else "",
        })
    return result


if __name__ == "__main__":
    quotes = parse_quotes(HTML_SAMPLE)
    print("解析到", len(quotes), "条数据")
    for index, quote in enumerate(quotes, start=1):
        print(index, quote["author"], "：", quote["text"])

# ===== 练习题 =====
# 1. 说明 //div 与 ./span 两种路径写法的区别。
# 2. 给每个 quote 增加序号字段 index，从 1 开始。
# 3. 若页面没有 class 属性，还能用哪些特征定位节点？至少写出两种。
