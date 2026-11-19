# ===== 第987课：字符串处理实战-综合案例2-格式转换 =====
# 知识点：
#   - 字符串方法组合使用完成格式转换
#   - 命名风格转换：snake_case ↔ camelCase ↔ kebab-case
#   - 日期格式转换：多种格式互转
#   - 实际场景：前后端字段名统一、日志格式统一

# 案例一：snake_case 转 camelCase
def snake_to_camel(snake):
    """user_name -> userName"""
    parts = snake.split("_")
    # 第一个词保持小写，后面的首字母大写
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


print("== snake_case → camelCase ==")
for name in ["user_name", "get_user_info", "is_valid_email", "a"]:
    print(f"  {name} -> {snake_to_camel(name)}")

# 案例二：camelCase 转 snake_case
def camel_to_snake(camel):
    """userName -> user_name"""
    result = []
    for ch in camel:
        if ch.isupper():
            result.append("_")
            result.append(ch.lower())
        else:
            result.append(ch)
    return "".join(result)


print("\n== camelCase → snake_case ==")
for name in ["userName", "getUserInfo", "isValidEmail", "x"]:
    print(f"  {name} -> {camel_to_snake(name)}")

# 案例三：kebab-case 转换
def to_kebab(camel):
    """userName -> user-name"""
    return camel_to_snake(camel).replace("_", "-")


print("\n== camelCase → kebab-case ==")
for name in ["backgroundColor", "fontSize", "marginTop"]:
    print(f"  {name} -> {to_kebab(name)}")

# 案例四：日期格式转换
def convert_date(date_str):
    """'2024/01/15' -> '2024-01-15' -> '15 Jan 2024'"""
    parts = date_str.split("/")
    year, month, day = parts
    months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{day} {months[int(month)]} {year}"


print("\n== 日期格式转换 ==")
for date in ["2024/01/15", "2023/12/25", "2024/06/01"]:
    print(f"  {date} -> {convert_date(date)}")

# 案例五：手机号格式化
def format_phone(raw):
    """13812345678 -> 138-1234-5678"""
    digits = raw.replace("-", "").replace(" ", "")
    if len(digits) != 11:
        return raw                             # 不是 11 位就不处理
    return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"


print("\n== 手机号格式化 ==")
for phone in ["13812345678", "138 1234 5678", "138-1234-5678", "123"]:
    print(f"  {phone!r:>20} -> {format_phone(phone)}")

# 案例六：金额格式化
def format_money(amount):
    """1234567.8 -> ¥1,234,567.80"""
    whole = int(amount)
    decimal = int(round((amount - whole) * 100))
    parts = []
    while whole > 0:
        parts.append(str(whole % 1000))
        whole //= 1000
    if not parts:
        parts = ["0"]
    thousand = ",".join(reversed(parts))
    return f"¥{thousand}.{decimal:02d}"


print("\n== 金额格式化 ==")
for amount in [1234567.8, 999, 0.5, 10000000]:
    print(f"  {amount} -> {format_money(amount)}")

# ===== 练习题 =====
# 1. 写一个函数把 "HELLO_WORLD" 转为 "helloWorld"（大写蛇形 → 小驼峰）。
# 2. 写一个函数把 "2024-01-15" 转为 "2024年1月15日"。
# 3. 写一个函数把 "abc123def456" 中的数字提取出来放到列表中。
# 4. 思考：格式转换函数为什么要「先解析再生成」而不是直接 replace？
