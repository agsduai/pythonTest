# ===== 第225课：正则表达式-常用函数与编译 =====
# 知识点：
#   - re.compile：预编译模式，反复使用更快、代码更清晰
#   - re.sub / re.subn：替换（后者额外返回替换次数）
#   - re.split：按模式切分，支持多分隔符
#   - re.finditer：返回迭代器，省内存且保留位置信息
#   - sub 的替换参数可以是函数：动态生成替换内容

import re

# compile：编译一次，到处使用
PHONE = re.compile(r"1[3-9]\d{9}")
for m in PHONE.finditer("联系电话 13812345678，应急 15987654321"):
    print(m.group(), "位置", m.start())

print(PHONE.sub("[已隐藏]", "张三 13812345678 李四 15987654321"))

# subn：返回 (新字符串, 替换次数)
new, n = re.subn(r"\s+", " ", "a   b\t\nc")
print(new, "替换了", n, "处")

# split：多分隔符切分
print(re.split(r"[,;，；]+", "苹果,香蕉；橙子，西瓜"))

# 替换函数：把每个数字翻倍
def double(m):
    return str(int(m.group()) * 2)


print(re.sub(r"\d+", double, "A1 B22 C333"))


# 替换函数：手机号脱敏
def mask(m):
    phone = m.group()
    return phone[:3] + "****" + phone[-4:]


print(re.sub(r"1[3-9]\d{9}", mask, "手机 13812345678"))

# finditer vs findall：需要位置信息时用 finditer
for m in re.finditer(r"\d+", "第1章 第22页 第333行"):
    print(f"{m.group()} 起始位置 {m.start()}")

# ===== 练习题 =====
# 1. 用 compile + subn 把文本里的所有数字替换为 #，并输出替换次数。
# 2. 编写函数 clean_text(s)：去掉多余空白并把标点 ，。统一换成 , .
# 3. 用替换函数把每串连续字母改为首字母大写（提示：m.group().capitalize()）。
# 4. 思考：同一个模式要在一百万行日志上跑，compile 的收益体现在哪？
