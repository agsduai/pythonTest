# ===== 第1024课：推导式与内置函数-enumerate与zip =====
# 知识点：
#   - enumerate(列表)：同时拿到下标和元素，替代 range(len())
#   - enumerate(列表, start=1)：让计数从 1 开始，适合"第 1 名、第 2 名"
#   - zip(列表A, 列表B)：并行遍历两个列表，短的先结束
#   - zip 还能"转置"：把一行行数据变成一列列数据

# 案例一：enumerate 打印排行榜 —— 下标从 1 开始
# 场景：打印比赛名次和得分
scores = [98, 92, 88]
for rank, score in enumerate(scores, start=1):
    print(f"第 {rank} 名：{score} 分")

# 案例二：zip 合并商品和价格 —— 一起遍历
# 场景：商品名和价格是两个列表，要配对输出
goods = ["苹果", "牛奶", "面包"]
prices = [5.5, 8.0, 12.0]
for g, p in zip(goods, prices):
    print(f"{g}：{p} 元")
# 转成列表就是 [(商品, 价格), ...] 的元组列表
pairs = list(zip(goods, prices))
print(f"配对结果：{pairs}")

# 案例三：zip 转置 —— 行列互换
# 场景：订单表是 [(商品, 数量), ...]，要拆成"商品一列、数量一列"
rows = [("苹果", 3), ("牛奶", 2), ("面包", 1)]
names, counts = zip(*rows)  # 星号解包，一行拆两列
print(f"商品列：{names}，数量列：{counts}")

# 案例四：enumerate + dict —— 构建座位表
# 场景：给学员自动排座位号 A01、A02...
students = ["小张", "小李", "小王"]
seat_map = {f"A{i:02d}": name for i, name in enumerate(students, start=1)}
print(f"座位表：{seat_map}")

# 注意：zip 长度不齐时按短的截断，要严格配齐用 strict=True（3.10+）
ids = ["001", "002"]
names2 = ["小张", "小李", "小王"]
try:
    list(zip(ids, names2, strict=True))
except ValueError as e:
    print(f"长度不齐被拦截：{e}")

# ===== 练习题 =====
# 1. 用 enumerate 打印列表 ["a", "b", "c"]，格式为 "1. a"、"2. b"、"3. c"。
# 2. 有姓名列表 ["小张","小李"] 和成绩列表 [88, 92]，用 zip 合成字典 {"小张": 88, "小李": 92}（字典推导式 + zip）。
# 3. 三行数据 [("语文", 88), ("数学", 92), ("英语", 80)]，用 zip(*rows) 拆出科目和分数两列并分别打印。
