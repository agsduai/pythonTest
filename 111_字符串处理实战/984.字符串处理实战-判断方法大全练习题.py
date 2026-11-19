# ===== 第984课：字符串处理实战-判断方法大全 =====
# 知识点：
#   - isdigit() 是否全是数字（不含负号和小数点）
#   - isalpha() 是否全是字母
#   - isalnum() 是否全是字母或数字
#   - isspace() 是否全是空白字符
#   - isupper() / islower() 是否全大写/全小写
#   - 实际场景：输入验证、数据类型判断、格式检查

# 案例一：验证用户输入是否为纯数字
user_inputs = ["123", "12.5", "abc", "", " 123", "-5"]
print("== 判断是否为纯数字 ==")
for text in user_inputs:
    result = text.isdigit()
    print(f"  {text!r:>8}.isdigit() = {result}")

print("  注意: isdigit 不认负号和小数点，'12.5' 和 '-5' 都返回 False")

# 案例二：验证用户名（只允许字母和数字）
print("\n== 验证用户名 ==")
usernames = ["zhangsan", "lisi123", "wang wu", "赵六", ""]
for name in usernames:
    valid = name.isalnum() and len(name) > 0
    print(f"  {name!r:>12} -> {'合法' if valid else '不合法'}（含空格或为空）")

# 案例三：判断字符串内容类型
print("\n== 综合判断 ==")
test_strings = ["123", "abc", "ABC", "a1b2", "   ", "", "Hello World"]
for s in test_strings:
    info = []
    if s.isdigit():
        info.append("纯数字")
    if s.isalpha():
        info.append("纯字母")
    if s.isalnum() and not s.isdigit() and not s.isalpha():
        info.append("字母+数字")
    if s.isspace():
        info.append("纯空白")
    if not s:
        info.append("空字符串")
    if s.isupper():
        info.append("全大写")
    if s.islower() and s.isalpha():
        info.append("全小写")
    label = " + ".join(info) if info else "混合内容"
    print(f"  {s!r:>16} -> {label}")

# 案例四：手机号验证（简化版：11 位纯数字且以 1 开头）
print("\n== 手机号验证 ==")
phone_numbers = ["13812345678", "12345678901", "1381234567", "1381234567890"]
for phone in phone_numbers:
    is_valid = (len(phone) == 11 and phone.isdigit() and phone.startswith("1"))
    reason = ""
    if not is_valid:
        if len(phone) != 11:
            reason = f"长度 {len(phone)} ≠ 11"
        elif not phone.isdigit():
            reason = "含非数字字符"
        elif not phone.startswith("1"):
            reason = "不以 1 开头"
    print(f"  {phone}: {'有效' if is_valid else f'无效 ({reason})'}")

# ===== 练习题 =====
# 1. 判断 "Python3.8" 中哪些部分是字母、哪些是数字。
# 2. 写一个函数：接收字符串，返回 "纯数字"/"纯字母"/"混合" 的判断结果。
# 3. 验证密码 "Abc123!"：是否包含大写、小写和数字（用 isupper/islower/isdigit）。
# 4. 思考：为什么 "12.5".isdigit() 返回 False？有什么替代方案？
