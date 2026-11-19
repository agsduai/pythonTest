# ===== 第989课：数据验证与转换-用户输入验证 =====
# 知识点：
#   - input() 永远返回字符串，需要手动转换类型
#   - 验证要做三件事：检查是否为空、检查格式、检查范围
#   - 循环 + break 让用户反复输入直到合法
#   - 好的验证要告诉用户『错在哪』，不能只说『错了』

# 案例一：验证年龄输入
def get_age():
    """循环获取合法的年龄输入。"""
    while True:
        text = input("请输入年龄 (1-150): ").strip()
        if not text:
            print("  不能为空，请重新输入")
            continue
        if not text.isdigit():
            print(f"  {text!r} 不是纯数字，请重新输入")
            continue
        age = int(text)
        if age < 1 or age > 150:
            print(f"  {age} 超出范围 (1-150)，请重新输入")
            continue
        return age


print("== 年龄输入验证（模拟 3 次输入）==")
simulated = ["", "abc", "200"]                # 模拟用户先输错再输对
inputs = iter(simulated + ["25"])
for text in inputs:
    if not text:
        print(f"  输入 {text!r}: 不能为空")
        continue
    if not text.isdigit():
        print(f"  输入 {text!r}: 不是纯数字")
        continue
    age = int(text)
    if 1 <= age <= 150:
        print(f"  输入 {text!r}: 合法，年龄 = {age}")
        break
    else:
        print(f"  输入 {text!r}: 超出范围")

# 案例二：验证手机号
def validate_phone(phone):
    """验证手机号格式，返回 (是否合法, 错误信息)。"""
    phone = phone.strip()
    if not phone:
        return False, "手机号不能为空"
    if not phone.isdigit():
        return False, "手机号只能包含数字"
    if len(phone) != 11:
        return False, f"手机号长度应为 11 位，当前 {len(phone)} 位"
    if not phone.startswith("1"):
        return False, "手机号应以 1 开头"
    return True, "格式正确"


print("\n== 手机号验证 ==")
test_phones = ["13812345678", "", "138abc56789", "12345678901", "1381234"]
for phone in test_phones:
    valid, msg = validate_phone(phone)
    print(f"  {phone!r:>16} -> {'✓' if valid else '✗ ' + msg}")

# 案例三：验证密码强度
print("\n== 密码强度检查 ==")
passwords = ["123456", "abcDEF", "Abc12345", "short"]
for pwd in passwords:
    issues = []
    if len(pwd) < 8:
        issues.append("长度不足 8 位")
    if not any(c.isupper() for c in pwd):
        issues.append("缺少大写字母")
    if not any(c.islower() for c in pwd):
        issues.append("缺少小写字母")
    if not any(c.isdigit() for c in pwd):
        issues.append("缺少数字")
    strength = "强" if not issues else "弱: " + "、".join(issues)
    print(f"  {pwd!r:>12} -> {strength}")

# ===== 练习题 =====
# 1. 写一个函数验证邮箱格式：必须包含 @ 和 .，且 @ 在 . 之前。
# 2. 写一个函数验证用户输入的是否为正整数，返回转换后的 int。
# 3. 增加密码强度检查规则：不能包含连续 3 个相同字符。
# 4. 思考：为什么要告诉用户具体错在哪，而不只是说「输入不合法」？
