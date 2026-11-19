# ===== 第1025课：推导式与内置函数-sorted与key排序 =====
# 知识点：
#   - sorted(列表)：返回排好序的新列表，原列表不变；列表.sort() 是原地改
#   - key 参数：指定"按什么排"，如按长度、按字典某字段、按绝对值
#   - reverse=True：从大到小 / 从后往前
#   - 多条件排序：key 返回元组，先比第一项，相同再比第二项

# 案例一：基础排序 —— 成绩从高到低
scores = [88, 92, 75, 100, 59]
print(f"升序：{sorted(scores)}")
print(f"降序：{sorted(scores, reverse=True)}")
print(f"原列表没变：{scores}")  # sorted 不改原列表

# 案例二：key 按长度排 —— 商品名按字数
# 场景：界面展示时短名字排前面
goods = ["酸奶", "新疆牛奶", "面包", "全麦吐司片"]
print(f"按长度升序：{sorted(goods, key=len)}")
print(f"按长度降序：{sorted(goods, key=len, reverse=True)}")

# 案例三：字典列表按字段排 —— 订单按金额
# 场景：订单列表要按金额从高到低显示
orders = [
    {"id": "A01", "amount": 120},
    {"id": "A02", "amount": 80},
    {"id": "A03", "amount": 200},
]
by_amount = sorted(orders, key=lambda o: o["amount"], reverse=True)
for o in by_amount:
    print(f"订单 {o['id']}：{o['amount']} 元")

# 案例四：多条件排序 —— 元组 key
# 场景：先按班级排，同班级按分数从高到低
students = [
    ("二班", 85),
    ("一班", 90),
    ("二班", 95),
    ("一班", 78),
]
# 班级升序，分数降序：对数字取负即可实现"同班级内降序"
by_class = sorted(students, key=lambda s: (s[0], -s[1]))
print(f"多条件排序：{by_class}")

# 案例五：忽略大小写排序
words = ["banana", "Apple", "cherry", "apple"]
print(f"默认排序：{sorted(words)}")  # 大写在前
print(f"忽略大小写：{sorted(words, key=str.lower)}")

# ===== 练习题 =====
# 1. 列表 ["bbb", "a", "cccc", "dd"]，按长度从短到长输出。
# 2. 商品列表 [("苹果", 5.5), ("牛奶", 8.0), ("面包", 12.0)]，按价格降序输出商品名。
# 3. 学生字典列表 [{"name":"小张","score":85},{"name":"小李","score":92},{"name":"小王","score":85}]，先按分数降序、同分按姓名升序，输出排序结果。
