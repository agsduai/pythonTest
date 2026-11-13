# ===== 第226课：正则表达式-常见实战案例 =====
# 知识点：
#   - 校验类：手机号、邮箱、身份证、URL
#   - 提取类：从日志/文本中抽取结构化字段
#   - 实战原则：先松后紧 —— 先让正确数据都能过，再逐步收紧规则
#   - 教学版规则：真实业务要按官方标准完善（如手机号段会新增）

import re

# 手机号：1 开头，第二位 3-9，共 11 位
PHONE = re.compile(r"^1[3-9]\d{9}$")
print(bool(PHONE.match("13812345678")), bool(PHONE.match("12812345678")))

# 邮箱（简化版）：用户名@域名（可多级）
EMAIL = re.compile(r"^[\w.%+-]+@[\w-]+(\.[\w-]+)+$")
for e in ("tom@example.com", "li+tag@mail.co.uk", "bad@", "@no.com"):
    print(e, bool(EMAIL.match(e)))

# 身份证：18 位（末位可为 X）或 15 位
ID_CARD = re.compile(r"^\d{17}[\dXx]$|^\d{15}$")
print(bool(ID_CARD.match("11010119900307867X")))

# URL（简化版）
URL = re.compile(r"https?://[\w.-]+(?:/[\w./?%&=-]*)?")
print(URL.findall("文档 https://docs.python.org/3/library/re.html 与 http://a.com"))

# 日志行解析：时间 + 级别 + 消息
LOG = re.compile(
    r"(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"\[(?P<level>\w+)\] (?P<msg>.+)"
)
m = LOG.match("2026-11-12 10:23:01 [ERROR] 数据库连接超时")
print(m.group("level"), "→", m.group("msg"))

# 金额提取：支持千分位逗号和小数
print(re.findall(
    r"\d{1,3}(?:,\d{3})*(?:\.\d+)?",
    "总销售额 1,234,567.89 元，成本 89.5 元",
))

# ===== 练习题 =====
# 1. 编写车牌校验：1位省份简称（汉字）+ 1位字母 + 5位字母数字。
# 2. 从 "2026-11-12 08:30:05 [INFO] xxx" 格式的多行文本中提取全部时间。
# 3. 给金额正则增加“可选的￥前缀”支持。
# 4. 思考：为什么邮箱正则“完全正确”几乎不可能？教学版够用在哪里？
