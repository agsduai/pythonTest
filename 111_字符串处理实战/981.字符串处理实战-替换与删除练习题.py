# ===== 第981课：字符串处理实战-替换与删除 =====
# 知识点：
#   - replace(旧, 新) 替换所有匹配，replace(旧, 新, 次数) 只替换前几次
#   - strip(参数) 可以去除指定字符而不只是空格
#   - translate + maketrans 可以批量替换多个字符
#   - 实际场景：清洗数据、统一格式、去除特殊字符

# 案例一：批量替换
text = "2024-01-15"
print(f"原始日期: {text}")
print(f"替换 - 为 /: {text.replace('-', '/')}")
print(f"只替换第一个: {text.replace('-', '/', 1)}")
print(f"去掉所有 -: {text.replace('-', '')}")

# 案例二：清除指定字符（不只是空格）
data = "###123###"
print(f"\n原始: {data!r}")
print(f"去掉所有 #: {data.strip('#')!r}")
print(f"只去左边的 #: {data.lstrip('#')!r}")
print(f"只去右边的 #: {data.rstrip('#')!r}")

# 案例三：手机号脱敏
phone = "13812345678"
masked = phone[:3] + "****" + phone[-4:]
print(f"\n手机号脱敏: {phone} -> {masked}")

# 案例四：批量替换多个字符（translate）
text = "hello world"
table = str.maketrans("lo", "01")
print(f"\n原文: {text}")
print(f"l→0, o→1: {text.translate(table)}")
# 也可以用 translate 直接删除字符
table2 = str.maketrans("", "", "aeiou")
print(f"删除所有元音: {text.translate(table2)}")

# 案例五：统一手机号格式
phone_numbers = ["13812345678", "138-1234-5678", "138 1234 5678"]
print("\n统一手机号格式:")
for phone in phone_numbers:
    clean = phone.replace("-", "").replace(" ", "")
    print(f"  {phone} -> {clean}")

# 案例六：replace 的链式调用
messy = "  Hello   World  "
clean = messy.strip().replace("   ", " ").lower()
print(f"\n链式清理: {messy!r} -> {clean!r}")

# ===== 练习题 =====
# 1. 把 "2024年01月15日" 中的中文替换为 "-"，得到 "2024-01-15"。
# 2. 有一个字符串 "  a  b  c  "，去掉所有空格，只留字母。
# 3. 用 translate 把 "hello" 中的 h 替换为 H。
# 4. 思考：replace 和 strip 都能去掉字符，它们有什么区别？
