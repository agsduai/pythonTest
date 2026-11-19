# ===== 第1016课：常见错误与调试-ValueError与转换失败 =====
# 知识点：
#   - ValueError：类型对了但值不对，如 int("abc") 类型是字符串但内容不是数字
#   - int() / float() 转换失败最常见，用户输入不可信，必须 try
#   - strip() 先去空格再转换，" 12 " 带空格也可能转换失败
#   - 转换前可以先用 isdigit() 预检查，但 try 更保险

# 案例一：int("abc") —— 字符串转数字失败
text = "abc"
# num = int(text)  # 报 ValueError: invalid literal for int() with base 10: 'abc'
# 解读：int() 只接受"长得像数字"的字符串
try:
    num = int(text)
except ValueError:
    print(f"'{text}' 不是合法数字，转换失败")  # 不崩溃，给出友好提示

# 案例二：带空格和单位的输入
# 场景：用户输入 " 18 " 或 "18岁"
raw = "  18  "
num = int(raw.strip())  # 先去掉首尾空格
print(f"年龄：{num}")
raw2 = "18岁"
if raw2.isdigit():
    num2 = int(raw2)
else:
    num2 = 0
    print(f"'{raw2}' 含非数字字符，预检查不通过，按 0 处理")

# 案例三：循环重试 —— 输错了就再问一次
# 场景：收集用户年龄，输错不让程序崩溃
for attempt in range(3):
    # age_str = input("请输入年龄：")  # 真实场景
    age_str = ["12", "abc", "20"][attempt]  # 模拟三次输入
    try:
        age = int(age_str)
        print(f"第 {attempt + 1} 次输入成功，年龄 {age}")
        break
    except ValueError:
        print(f"第 {attempt + 1} 次输入 '{age_str}' 无效，请重试")
else:
    print("三次都输错了，先退出")

# 案例四：float 转换与非法值
# 场景：读取金额字段，可能是 "9.9"、"免费"、空字符串
amounts = ["9.9", "免费", "", "  20.5 "]
for a in amounts:
    try:
        value = float(a)
        print(f"'{a}' -> {value}")
    except ValueError:
        print(f"'{a}' -> 无法转成数字，跳过")  # 空字符串也转不了

# ===== 练习题 =====
# 1. 分别尝试 int("3.14")、float("3.14")、int(float("3.14"))，运行后用注释解释为什么 int("3.14") 报错而最后一种可行。
# 2. 写函数 to_int(text)：能转就返回整数，不能转返回 -1，用 "25"、"1e3"、" 7 "、"x" 四个值测试。
# 3. 模拟用户输入金额列表 ["10", "-3", "abc", "0"]，写程序把能转的转成数字，并只保留大于 0 的，输出结果 [10]。
