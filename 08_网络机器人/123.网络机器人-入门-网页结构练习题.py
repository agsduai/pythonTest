# ===== 第123课：网络机器人-入门-网页结构 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - HTML 由标签、属性、文本组成，浏览器将其解析为树形 DOM
#   - 常用标签：html/head/body/div/ul/li/a/h1/p
#   - class、id、href 等属性是定位元素的重要依据
#   - lxml 可把 HTML 字符串解析成可遍历的元素树
# 依赖：pip install lxml

from lxml import etree

HTML_SAMPLE = """<!DOCTYPE html>
<html>
  <head><title>图书示例</title></head>
  <body>
    <div class="box" id="main">
      <h1>畅销书榜单</h1>
      <ul class="book-list">
        <li><a href="/book/1">Python 入门</a></li>
        <li><a href="/book/2">数据结构基础</a></li>
      </ul>
    </div>
  </body>
</html>
"""


def walk(node, depth: int = 0) -> None:
    """深度优先打印元素树，非标签节点（注释等）跳过。"""
    if not isinstance(node.tag, str):
        return
    print("  " * depth + f"<{node.tag}>", dict(node.attrib))
    for child in node:
        walk(child, depth + 1)


if __name__ == "__main__":
    root = etree.HTML(HTML_SAMPLE)
    print("根元素：", root.tag)                 # html
    print("页面标题：", root.xpath("//title/text()"))
    print("元素树：")
    walk(root)
    first_link = root.xpath("//ul[@class='book-list']/li[1]/a")[0]
    print("第一个链接文本：", first_link.text)
    print("第一个链接地址：", first_link.get("href"))
    print("父元素：", first_link.getparent().tag)

# ===== 练习题 =====
# 1. 画出 HTML_SAMPLE 的元素树，标出 h1 与两个 a 的层级关系。
# 2. 用 xpath 统计 li 元素个数，并打印每个 a 的 href。
# 3. 修改 walk，使其同时打印元素的文本内容（去掉首尾空白）。
