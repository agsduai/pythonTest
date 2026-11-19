# ===== 第979课：字符串处理实战-大小写与去空格 =====
# 知识点：
#   - strip() 去除首尾空格，lstrip() 只去左边，rstrip() 只去右边
#   - upper() 全大写，lower() 全小写，title() 每个单词首字母大写
#   - swapcase() 大小写互换，capitalize() 只第一个字母大写
#   - 实际场景：用户输入的姓名/邮箱往往带多余空格或大小写混乱

# 案例一：清理用户注册信息
name = "  张三  "
email = "  ZhangSan@Email.COM  "
clean_name = name.strip()
clean_email = email.strip().lower()
print(f"清理前: 姓名={name!r} 邮箱={email!r}")
print(f"清理后: 姓名={clean_name!r} 邮箱={clean_email}")
print(f"名字长度对比: 清理前 {len(name)} -> 清理后 {len(clean_name)}")

# 案例二：标题格式化
title_input = "python is awesome"
print(f"\n原始: {title_input}")
print(f"title():   {title_input.title()}")
print(f"capitalize(): {title_input.capitalize()}")
print(f"upper():   {title_input.upper()}")
print(f"swapcase(): {title_input.swapcase()}")

# 案例三：只去一边的空格
url = "  https://example.com  "
print(f"\n原始 URL: {url!r}")
print(f"strip()  两边都去: {url.strip()!r}")
print(f"lstrip() 只去左边: {url.lstrip()!r}")
print(f"rstrip() 只去右边: {url.rstrip()!r}")

# 案例四：去空格不影响中间内容
text = "  hello   world  "
print(f"\n中间的多个空格不会被 strip 去掉: {text.strip()!r}")
print(f"要去掉所有空格需要用 replace: {text.replace(' ', '')!r}")

# 案例五：密码比较前统一格式
password_input = "  MyPass123  "
password_saved = "MyPass123"
# 密码通常不去空格（空格可能是有效字符），只做精确比较
print(f"\n密码精确匹配: {password_input == password_saved}")
print(f"去空格后匹配: {password_input.strip() == password_saved}")

# ===== 练习题 =====
# 1. 用户输入 "  Hello World  "，分别输出 strip()、upper()、title() 的结果。
# 2. 有一个变量 text = "  Python  "，只去掉左边的空格，打印结果和长度。
# 3. 把 "hello world python" 转换为 "Hello World Python"（提示：用 title）。
# 4. 思考：什么场景该用 strip()，什么场景不该用？（提示：密码中的空格
#    可能是用户故意输入的）
