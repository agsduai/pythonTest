# ===== 第1023课：推导式与内置函数-集合推导式与去重 =====
# 知识点：
#   - 集合推导式：{表达式 for 变量 in 可迭代对象}，注意不是字典（没有冒号）
#   - 集合自动去重，最快的去重方法：list(set(列表))
#   - 去重后顺序会乱；要保序去重需要用 dict.fromkeys() 或循环判断
#   - 统计"出现过哪些值"类问题，集合是最合适的工具

# 案例一：快速去重 —— 用户提交的标签列表
# 场景：用户填了一堆重复标签，要合并成唯一标签列表
tags = ["Python", "python", "编程", "Python", "学习", "编程"]
unique_tags = set(tags)  # 注意 "Python" 和 "python" 是不同的
print(f"去重后：{unique_tags}")

# 案例二：保序去重 —— 去重但保持第一次出现的顺序
logs = ["login", "pay", "login", "view", "pay", "logout"]
seen = []
for action in logs:
    if action not in seen:
        seen.append(action)
print(f"保序去重：{seen}")  # ['login', 'pay', 'view', 'logout']
# 一行写法：dict.fromkeys 保持插入顺序（Python 3.7+ 字典有序）
print(f"fromkeys：{list(dict.fromkeys(logs))}")

# 案例三：集合推导式 —— 找出所有出现过的字母（统一小写）
comments = ["Good", "good", "Nice", "NICE", "ok"]
letters = {c.lower() for text in comments for c in text if c.isalpha()}
print(f"出现过的字母：{letters}")

# 案例四：集合运算 —— 找共同点
# 场景：两人购物车里的相同商品和各自独有的商品
cart_a = {"牛奶", "面包", "鸡蛋"}
cart_b = {"鸡蛋", "酸奶", "牛奶"}
print(f"共同购买：{cart_a & cart_b}")  # 交集
print(f"只有A买：{cart_a - cart_b}")  # 差集
print(f"合计覆盖：{cart_a | cart_b}")  # 并集

# ===== 练习题 =====
# 1. 列表 [1, 2, 2, 3, 3, 3, 4]，分别用 set() 和 dict.fromkeys() 去重，打印两种结果并比较顺序。
# 2. 用集合推导式从 ["apple", "Avocado", "banana", "Apricot"] 中提取所有首字母（统一小写），输出 {'a', 'b'}。
# 3. 两个班名单 a = ["小张","小李","小王"]，b = ["小李","小赵","小王"]，用集合运算输出：两人都选的课代表、只在 a 班的、两班合计名单。
