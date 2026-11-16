# ===== 第399课：配置与序列化-XML与ElementTree =====
# 知识点：
#   - XML：标签 + 属性 + 文本，企业系统/旧接口常见
#   - ElementTree：parse/fromstring 解析，find/findall 查找，attrib 取属性
#   - 生成：Element/SubElement 建树，ET.indent 美化，write 输出
#   - 命名空间：标签会变成 {namespace}tag，查找时要带前缀
#   - 安全：不要解析不可信 XML 的实体（XXE）；生产可用 defusedxml
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

XML_TEXT = """<?xml version="1.0" encoding="utf-8"?>
<library>
  <book id="1" category="programming">
    <title>Python 入门</title>
    <price>59.0</price>
  </book>
  <book id="2" category="data">
    <title>数据分析实战</title>
    <price>79.5</price>
  </book>
</library>
"""

# ---- 解析 ----
root = ET.fromstring(XML_TEXT)
print("根标签：", root.tag)
print("书籍数量：", len(root.findall("book")))

for book in root.findall("book"):
    book_id = book.get("id")
    category = book.get("category")
    title = book.findtext("title")           # 直接取子节点文本
    price = float(book.findtext("price"))
    print(f"  #{book_id} [{category}] {title} — {price} 元")

# ---- 按条件筛选 ----
cheap = [b.findtext("title") for b in root.findall("book")
         if float(b.findtext("price")) < 70]
print("\n70 元以下：", cheap)

# ---- 构建 XML 并输出 ----
new_root = ET.Element("catalog", {"generated": "2026-11-13"})
for name, price, tags in [("键盘", 199, ["外设", "办公"]), ("显示器", 1299, ["外设"])]:
    item = ET.SubElement(new_root, "item", {"name": name})
    ET.SubElement(item, "price").text = str(price)
    for tag in tags:
        ET.SubElement(item, "tag").text = tag

ET.indent(new_root, space="  ")              # 缩进美化（3.9+）
xml_out = ET.tostring(new_root, encoding="unicode")
print("\n== 生成的 XML ==")
print(xml_out)

# ---- 写文件再读回 ----
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "catalog.xml"
    tree = ET.ElementTree(new_root)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print("\n文件大小：", path.stat().st_size, "字节")

    back = ET.parse(path).getroot()
    print("读回后商品数：", len(back.findall("item")))
    print("第一个商品：", back.find("item").get("name"))

# ---- 命名空间演示 ----
NS_XML = """<root xmlns:h="http://example.com/html">
  <h:table><h:tr><h:td>单元格</h:td></h:tr></h:table>
</root>"""
ns_root = ET.fromstring(NS_XML)
print("\n带命名空间的标签：", ns_root[0].tag)
print("正确查找：", ns_root.find("h:table", {"h": "http://example.com/html"}).tag)

# ===== 练习题 =====
# 1. 给 catalog 增加“库存数量”节点，并按数量排序输出。
# 2. 用 iter("tag") 递归找出所有 tag 节点（不限层级）。
# 3. 把 XML 转成 dict 列表（name/price/tags），再用 json 写出（第232课）。
# 4. 思考：XML 与 JSON 各自的优势场景是什么？
