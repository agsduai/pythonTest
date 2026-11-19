# ===== 第1021课：推导式与内置函数-带条件与嵌套的列表推导式 =====
# 知识点：
#   - 带过滤：[x for x in 数据 if 条件]，只保留满足条件的
#   - 带转换分支：[a if 条件 else b for x in 数据]（if...else 写在 for 前面）
#   - 两个 for 可以嵌套：遍历"列表的列表"拍平成一维
#   - 读法从左到右：先 for、再 if 过滤、最后是前面的表达式

# 案例一：过滤 —— 只留及格的成绩
scores = [88, 45, 92, 59, 73]
passed = [s for s in scores if s >= 60]
print(f"及格成绩：{passed}")  # [88, 92, 73]

# 案例二：转换分支 —— if...else 写在 for 前面
# 场景：满 100 打 8 折，不满打 9 折
prices = [120, 80, 200, 50]
result = [p * 0.8 if p >= 100 else p * 0.9 for p in prices]
print(f"折后价：{result}")  # [96.0, 72.0, 160.0, 45.0]

# 案例三：组合过滤 + 转换 —— VIP 用户名变大写
# 场景：从用户列表里挑出 VIP，并转大写标识
users = [("小张", True), ("小李", False), ("小王", True)]
vip_names = [name.upper() for name, is_vip in users if is_vip]
print(f"VIP 用户：{vip_names}")  # ['小张', '小王'] -> ['小张'.upper(), '小王'.upper()]

# 案例四：嵌套 for —— 拍平二维列表
# 场景：每个订单有多个商品，要汇总所有商品名
orders = [["苹果", "牛奶"], ["面包"], ["鸡蛋", "酸奶", "可乐"]]
all_items = [item for order in orders for item in order]
print(f"全部商品：{all_items}")

# 组合示例：去掉所有空字符串再转小写
raw = ["  A ", "", "B ", "  ", "c"]
clean = [x.strip().lower() for x in raw if x.strip()]  # if 过滤纯空格
print(f"清洗结果：{clean}")  # ['a', 'b', 'c']

# ===== 练习题 =====
# 1. 用推导式从 [15, -3, 22, 0, -8, 7] 中只保留正数并乘 2，输出 [30, 44, 14]。
# 2. 用推导式把 [1, 2, 3, 4, 5, 6] 变成 ["偶数2", "奇数1", ...]：偶数输出 f"偶数{x}"，奇数输出 f"奇数{x}"。
# 3. 二维价格表 [[10, 20], [30, 40], [50, 60]]，用嵌套推导式拍平并只保留大于 25 的，输出 [30, 40, 50, 60]。
