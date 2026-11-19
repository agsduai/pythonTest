# ===== 第1020课：推导式与内置函数-列表推导式基础 =====
# 知识点：
#   - 列表推导式：[表达式 for 变量 in 可迭代对象]，一行生成列表
#   - 它是"for 循环 + append"的简写，效果完全一样
#   - 表达式里可以直接做运算或调用函数，如 [x * 2 for x in nums]
#   - 适合"对每个元素做同样处理"的批量任务

# 案例一：批量打折 —— 老写法 vs 推导式
# 场景：全场商品打 8 折
prices = [100, 80, 45, 120]
# 老写法：先建空列表，循环，追加
discounted = []
for p in prices:
    discounted.append(p * 0.8)
print(f"老写法：{discounted}")

# 推导式：一行搞定
discounted2 = [p * 0.8 for p in prices]
print(f"推导式：{discounted2}")

# 案例二：生成订单编号 —— 表达式里可以用 f-string
# 场景：给 5 笔订单生成编号 ORD-001 ~ ORD-005
order_ids = [f"ORD-{i:03d}" for i in range(1, 6)]
print(f"订单编号：{order_ids}")

# 案例三：字符串处理 —— 提取所有商品名并转大写
goods = ["milk", "bread", "egg"]
upper_goods = [g.upper() for g in goods]
print(f"大写商品名：{upper_goods}")

# 案例四：字符串转数字 —— 读 CSV 数据常用
# 场景：文件里读出来的是一列字符串数字，要转成数字参与计算
raw = ["12.5", "8", "9.9", "20"]
nums = [float(x) for x in raw]
print(f"转数字：{nums}，总价：{sum(nums)}")

# ===== 练习题 =====
# 1. 用推导式生成 1~10 中每个数的平方，输出 [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]。
# 2. 有列表 [" apple ", "banana ", " cherry"]，用推导式把每个元素 strip 后首字母大写。
# 3. 用推导式生成 2024 年 1~3 月的月份标签 ["2024-01", "2024-02", "2024-03"]（用 :02d 补零）。
