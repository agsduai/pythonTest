# ===== 第024课：核心语法-流程控制语句-if进阶(if...else)-案例 =====
# 课程来源：B站 BV1sHU9BmEne
# 知识点：
#   - if...else 双分支语法
#   - else 后面不加条件，与最近的 if 配对
#   - 两个分支必有且只有一个会执行
#   - else 同样需要用冒号和缩进

# 案例一：判断是否成年
age = 16
if age >= 18:
    print("已成年")
else:
    print("未成年")  # age 为 16，执行 else 分支

# 案例二：判断整数奇偶（% 取余）
number = 7
if number % 2 == 0:
    print(f"{number} 是偶数")
else:
    print(f"{number} 是奇数")

# 案例三：登录密码校验
password = "abc123"
if password == "abc123":
    print("登录成功")
else:
    print("密码错误，请重试")

# 案例四：根据余额判断能否付款
balance = 30
price = 45
if balance >= price:
    print("付款成功")
else:
    print(f"余额不足，还差 {price - balance} 元")

# 案例五：判断成绩是否达到优秀
score = 88
if score >= 90:
    print("成绩优秀")
else:
    print("继续努力")

# ===== 练习题 =====
# 1. 定义变量 score = 58，用 if...else 判断是否及格，及格输出“及格”，否则输出“不及格”。
# 2. 定义变量 year = 2024，用 if...else 判断能否被 4 整除，能则输出“可能是闰年”，否则输出“不是闰年”。
# 3. 定义变量 username = "admin"，判断是否等于 "admin"，是则输出“管理员登录”，否则输出“普通用户登录”。
