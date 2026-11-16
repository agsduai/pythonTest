# ===== 第645课：数据交换格式与协议设计-XML与配置文件格式对比 =====
# 知识点：
#   - XML：元素 + 属性 + 文本 + 命名空间；ElementTree 用 find/findall/iter 遍历
#   - XML 适合「文档型」数据（带混合内容、需校验 XSD），JSON 适合结构化数据
#   - INI（configparser）、TOML（tomllib，只读）、YAML 需要第三方库
#   - 对比维度：可读性、类型支持、注释、嵌套、模式校验、解析安全性
#   - XML 安全：禁止 DTD/外部实体（XXE），defusedxml 或禁用解析器实体
#   - 本课聚焦格式取舍，不引入 lxml/defusedxml
# 依赖：无（标准库，TOML 需 Python 3.11+）
import configparser
import io
import json
import tempfile
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

XML = """<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns:b="urn:book">
  <book id="101" lang="zh">
    <title>Python 入门</title>
    <author>张三</author>
    <price currency="CNY">59.90</price>
    <tags><tag>编程</tag><tag>教程</tag></tags>
  </book>
  <book id="102" lang="en">
    <title>Python Advanced</title>
    <author>Alice</author>
    <price currency="USD">39.00</price>
    <tags><tag>programming</tag></tags>
  </book>
  <b:meta generated="2026-11-14"/>
</catalog>
"""

print("== ElementTree 解析 ==")
root = ET.fromstring(XML)
print("  根标签:", root.tag, "| 子元素数:", len(root))
NS = {"b": "urn:book"}
for book in root.findall("book"):
    print(f"  id={book.get('id')} lang={book.get('lang')} "
          f"title={book.findtext('title')!r} price={book.findtext('price')} "
          f"{book.find('price').get('currency')} tags={[t.text for t in book.findall('tags/tag')]}")
print("  命名空间元素:", root.find("b:meta", NS).attrib)

print("\n== 属性 vs 子元素 ==")
for line in (
    "  属性: 标识/元数据（id、lang、currency），不可再嵌套，不能有重复名",
    "  子元素: 内容/可重复项（多个 tag），可继续嵌套、可带混合文本",
    "  没有绝对规则，但同一份协议里必须保持一致",
):
    print(line)

print("\n== 生成 XML ==")
new = ET.Element("users")
for name, age in (("张三", 30), ("Alice", 25)):
    u = ET.SubElement(new, "user", {"active": "true"})
    ET.SubElement(u, "name").text = name
    ET.SubElement(u, "age").text = str(age)
ET.indent(new, space="  ")
out = ET.tostring(new, encoding="unicode")
print(out)
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp) / "users.xml"
    ET.ElementTree(new).write(p, encoding="utf-8", xml_declaration=True)
    print(f"  写盘 {p.stat().st_size} 字节，读回根标签={ET.parse(p).getroot().tag}")

print("\n== INI（configparser）==")
ini = configparser.ConfigParser()
ini.read_string("""
[server]
host = 127.0.0.1
port = 8080
debug = true

[db]
dsn = sqlite:///app.db
""")
print("  sections:", ini.sections())
print(f"  host={ini['server']['host']}  port={ini.getint('server','port')}  "
      f"debug={ini.getboolean('server','debug')}")
print("  注意：INI 的值全是字符串，类型靠 getint/getboolean 显式转换")

print("\n== TOML（tomllib，标准库只读）==")
toml_text = """
title = "配置示例"
[server]
host = "0.0.0.0"
port = 9000
features = ["auth", "cache"]

[[users]]
name = "张三"
role = "admin"
"""
doc = tomllib.loads(toml_text)
print("  title:", doc["title"])
print("  server:", doc["server"])
print("  users:", doc["users"])
print("  TOML 原生支持数组、表、数组表与整数/布尔类型")

print("\n== 同一份数据的四种写法（体积）==")
data = {"server": {"host": "127.0.0.1", "port": 8080}, "debug": True}
j = json.dumps(data, separators=(",", ":"))
print(f"  JSON : {j}  ({len(j)} 字符)")
print(f"  INI  : [server]\\nhost = 127.0.0.1\\nport = 8080\\n[DEFAULT]\\ndebug = True")
print(f"  TOML : [server]\\nhost = '127.0.0.1'\\nport = 8080\\ndebug = true")
print(f"  XML  : <root><server host='127.0.0.1' port='8080'/><debug>true</debug></root>")

print("\n== 格式选型矩阵 ==")
print(f"  {'格式':<8}{'类型':<8}{'注释':<7}{'嵌套':<7}{'校验':<9}{'典型场景'}")
for row in (
    ("JSON", "有", "无", "好", "JSON Schema", "API / 配置"),
    ("XML", "靠约定", "有", "很好", "XSD", "文档 / 企业接口"),
    ("TOML", "有", "有", "表", "弱", "项目配置 pyproject"),
    ("INI", "无", "有", "弱", "无", "老式应用配置"),
    ("CSV", "无", "无", "无", "无", "表格数据交换"),
):
    print(f"  {row[0]:<8}{row[1]:<8}{row[2]:<7}{row[3]:<7}{row[4]:<9}{row[5]}")

print("\n== 安全性 ==")
for line in [
    "XML: 禁用 DTD 与外部实体，防 XXE / 十亿笑攻击；生产用 defusedxml",
    "YAML: 不用 yaml.load，只用 safe_load，避免任意对象构造",
    "JSON: 限制最大深度与长度，防栈溢出 / 内存打满",
    "任何格式：先校验再使用，绝不信任外部输入的结构",
]:
    print("  -", line)

# ===== 练习题 =====
# 1. 用 ElementTree 给 XML 增加 namespace 并写出，验证 find 需要传 namespaces。
# 2. 实现 xml_to_dict(elem)，把简单 XML 递归转成 dict（属性加 @ 前缀）。
# 3. 把同一份配置分别写成 TOML/INI/JSON，写个加载器统一返回 dict。
# 4. 思考：为什么 XML 在企业接口里仍常见，而新项目更倾向 JSON？
