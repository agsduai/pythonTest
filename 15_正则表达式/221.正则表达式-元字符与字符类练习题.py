# ===== 第221课：正则表达式-元字符与字符类 =====
# 知识点：
#   - 常用元字符：. 任意字符（换行除外）；^ 开头；$ 结尾
#   - 预定义字符类：\d 数字、\w 字母数字下划线、\s 空白（大写取反）
#   - 自定义字符类 []：[abc] 多选一、[a-z] 范围、[^0-9] 取反
#   - 转义：\. \? 把元字符变回普通字符

import re

# .：任意一个字符（不含换行）
print(re.findall(r"a.c", "abc a-c a c aXc"))      # 4 个都能匹配
print(re.findall(r"a.c", "a\nc"))                             # []：. 不匹配换行
print(re.findall(r"a.c", "a\nc", flags=re.DOTALL))            # 加 DOTALL 就匹配了

# 预定义字符类
print(re.findall(r"\d+", "订单号 A1002，金额 88.5 元"))
print(re.findall(r"\w+", "python_3.12 快速入门"))
print(re.findall(r"\S+", "名 字 间 有 空 格"))                 # 连续非空白段

# ^ 与 $：锚定开头结尾（整串校验的标配）
print(bool(re.search(r"^\d{6}$", "100000")))     # True：正好 6 位数字
print(bool(re.search(r"^\d{6}$", "1000001")))    # False：多了
print(bool(re.search(r"^\d{6}$", "10000a")))     # False：有字母

# 自定义字符类
print(re.findall(r"[aeiou]", "python is fun"))
print(re.findall(r"[a-zA-Z0-9_]+", "user_01 登录成功"))
print(re.findall(r"[^0-9]+", "A1002-B88"))       # 取反：连续的非数字段

# 转义：让 . 表示“点”本身
print(re.findall(r"\d+\.\d+", "价格 3.5 和 88.8"))
print(re.findall(r"3\.5", "3.5 和 3x5"))         # 只匹配 3.5，不匹配 3x5

# ===== 练习题 =====
# 1. 编写校验：字符串必须是“2位字母+4位数字”组合（如 ab1234）。
# 2. 从 "2026-11-12" 中分别用 \d 提取年、月、日。
# 3. 解释 r"\d{6}$" 为什么能匹配 "abc100000" 的一部分，怎么改成整串匹配。
# 4. 思考：\. 转义后还能用字符类 [.] 达到同样效果吗？验证一下。
