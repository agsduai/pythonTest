# ===== 第223课：正则表达式-分组与引用 =====
# 知识点：
#   - () 分组：把模式的一部分“圈”出来单独提取
#   - findall 遇到分组：返回分组内容而不是整段匹配
#   - 命名分组 (?P<名字>...)：按名字取值，可读性强
#   - 反向引用 \1：匹配“与第1组相同”的内容
#   - (?:...) 只分组不捕获：影响 findall 的返回结构

import re

# 分组提取
m = re.search(r"(\d{4})-(\d{2})-(\d{2})", "发布日期：2026-11-12")
print(m.group(0))    # 整个匹配
print(m.group(1), m.group(2), m.group(3))
print(m.groups())    # ('2026', '11', '12')

# findall 带分组：返回分组组成的元组列表
print(re.findall(r"(\d+)元", "苹果 5元，香蕉 3元"))           # 只返回分组
print(re.findall(r"(\w+) (\d+)元", "苹果 5元，香蕉 3元"))     # 多组返回元组

# 命名分组
m = re.search(r"(?P<year>\d{4})年(?P<month>\d{1,2})月", "2026年11月")
print(m.group("year"), m.group("month"))

# 或 |：多分支任选其一
print(re.findall(r"cat|dog", "cat dog cow catdog"))
print(re.search(r"https?://[\w.]+", "访问 https://www.python.org 官网").group())

# 反向引用：匹配“重复的单词”
print(re.findall(r"\b(\w+) \1\b", "hello hello world world abc"))

# 分组替换：交换日期的年与日
print(re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3-\2-\1", "2026-11-12"))

# (?:...) 非捕获分组：不改变 findall 的返回
print(re.findall(r"(?:py|py)thon", "python"))    # 与 (py|py) 结果不同
print(re.findall(r"(py|py)thon", "python"))      # 捕获组让 findall 只返回组

# ===== 练习题 =====
# 1. 用命名分组从 "姓名:小明,分数:92" 中提取姓名与分数。
# 2. 把 "2026年11月12日" 替换成 "12/11/2026"（用分组引用）。
# 3. 解释为什么 findall(r"(a|b)+", "ab") 返回 ['b'] 而不是 ['ab']。
# 4. 思考：什么时候用普通分组，什么时候用 (?:...)？
