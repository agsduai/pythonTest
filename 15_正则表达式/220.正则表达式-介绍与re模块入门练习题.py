# ===== 第220课：正则表达式-介绍与re模块入门 =====
# 知识点：
#   - 正则表达式：用“模式字符串”描述一类文本，用于查找/替换/校验
#   - re.search：扫描全串，返回第一个 Match 对象
#   - re.match：只从字符串开头匹配，开头不符即 None
#   - re.findall：返回所有匹配组成的列表
#   - r"..." 原始字符串：写正则的标配，避免反斜杠转义问题

import re

text = "客服电话：400-800-1234，备用：400-666-8888，邮编：100000"

# search：找第一个匹配，Match 对象里有位置和内容
m = re.search(r"\d{3}-\d{3}-\d{4}", text)
print(m.group())              # 400-800-1234
print(m.start(), m.end())     # 匹配内容的起止下标

# match：只看开头，开头不匹配直接返回 None
print(re.match(r"\d+", text))            # None（开头是“客服”两个字）
print(re.match(r"\d+", "666号客服").group())   # 666

# findall：找全部，直接返回字符串列表
print(re.findall(r"400-\d{3}-\d{4}", text))
print(re.findall(r"[a-z]+", "abc DEF ghi"))    # 只匹配连续小写字母

# 切分与替换预览（后面课详解）
print(re.split(r"[，：]", text))               # 按多种分隔符切分
print(re.sub(r"\d", "*", text))                # 每个数字替换成 *

# ===== 练习题 =====
# 1. 从 "2026-11-12 发布, 2026-12-01 截止" 中提取所有日期。
# 2. 用 re.findall 统计一句话里的中文字符（提示：[\u4e00-\u9fa5]）。
# 3. 把 search 换成 match 跑一遍本课示例，观察哪些结果变了。
# 4. 思考：什么场景用 findall，什么场景用 search？
