# ===== 第125课：网络机器人-入门-Xpath语法 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - // 从任意位置选后代，/ 选直接子节点，. 表示当前节点
#   - @属性、text()、[条件]、[位置]、last() 是常用限定手段
#   - contains()、starts-with()、normalize-space() 可做模糊匹配与清洗
#   - and/or 组合条件；.. 取父节点
# 依赖：pip install lxml

from lxml import etree

XML_SAMPLE = """<bookstore>
  <book category="web" price="59.9">
    <title>Python 编程</title>
    <author>张三</author>
  </book>
  <book category="web" price="89.0">
    <title>数据结构</title>
    <author>李四</author>
  </book>
  <book category="ai" price="108.5">
    <title>机器学习入门</title>
    <author>王五</author>
  </book>
</bookstore>"""


def main() -> None:
    root = etree.fromstring(XML_SAMPLE)
    print("全部书名：", root.xpath("//title/text()"))
    print("第一本书：", root.xpath("/bookstore/book[1]/title/text()"))
    print("最后一本书：", root.xpath("//book[last()]/title/text()"))
    print("web 类图书：", root.xpath("//book[@category='web']/title/text()"))
    print("价格大于 80：", root.xpath("//book[price > 80]/title/text()"))
    print("包含“数据”：", root.xpath("//title[contains(text(), '数据')]/text()"))
    print("以“机器”开头：", root.xpath("//title[starts-with(text(), '机器')]/text()"))
    print("第一本书分类：", root.xpath("/bookstore/book[1]/@category"))
    print("作者去空白：", [s.strip() for s in root.xpath("//author/text()")])


if __name__ == "__main__":
    main()

# ===== 练习题 =====
# 1. 写出选取第二本书作者的 XPath，并说明 [2] 与 [last()] 的区别。
# 2. 组合条件：选取 category 为 web 且 price 小于 70 的书名。
# 3. 用 normalize-space() 改写“作者去空白”，直接在 XPath 中完成。
