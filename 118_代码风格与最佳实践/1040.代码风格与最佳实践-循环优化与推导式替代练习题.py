# ===== 第1040课：代码风格与最佳实践-循环优化与推导式替代 =====
# 知识点：
#   - "循环里 append + 处理"的模式，多数能换成一行推导式
#   - 只需要"有没有/全都是"时用 any()/all()，别手动设标志位
#   - 计数/求和交给 sum()/len()，不要自己 count += 1
#   - 找第一个满足条件的元素：next + 生成器，避免遍历全表

# 案例一：append 模式改推导式
# 场景：挑出所有 VIP 用户名
users = [("小张", True), ("小李", False), ("小王", True)]
# 循环写法：
vip_names = []
for name, is_vip in users:
    if is_vip:
        vip_names.append(name)
print(f"循环写法：{vip_names}")
# 推导式写法：
print(f"推导式：{[name for name, is_vip in users if is_vip]}")

# 案例二：标志位改 any / all
# 场景：判断有没有人不及格
scores = [88, 45, 92]
# 循环 + 标志位（啰嗦）：
found_fail = False
for s in scores:
    if s < 60:
        found_fail = True
        break
print(f"循环判断：{found_fail}")
# any 一行（推荐）：
print(f"any 判断：{any(s < 60 for s in scores)}")
print(f"全及格：{all(s >= 60 for s in scores)}")

# 案例三：计数与求和交给内置函数
# 场景：统计正数个数和总和
nums = [5, -3, 8, 0, 2]
# 循环写法：
count = 0
total = 0
for n in nums:
    if n > 0:
        count += 1
        total += n
print(f"循环：{count} 个正数，总和 {total}")
# 内置函数一行：
print(f"内置：{sum(1 for n in nums if n > 0)} 个正数，总和 {sum(n for n in nums if n > 0)}")

# 案例四：找第一个满足的元素 —— next 短路查找
# 场景：找到第一个库存为 0 的商品
inventory = [("苹果", 10), ("牛奶", 0), ("面包", 5), ("酸奶", 0)]
# 循环 + break：
first_soldout = None
for name, stock in inventory:
    if stock == 0:
        first_soldout = name
        break
print(f"循环查找：{first_soldout}")
# next + 生成器（效果一样，写法紧凑）：
first = next((name for name, stock in inventory if stock == 0), "无缺货")
print(f"next 查找：{first}")

# 案例五：什么时候保留循环 —— 逻辑超过一行就别硬套推导式
# 有多步操作时，for 循环反而更清晰
for name, stock in inventory:
    if stock == 0:
        print(f"补货通知：{name} 缺货")  # 两步动作，用循环更明白
    elif stock < 5:
        print(f"预警：{name} 只剩 {stock} 件")

# ===== 练习题 =====
# 1. 用推导式替代循环：从 ["apple", "", "banana", " "] 中去掉空项并全部转大写。
# 2. 用 any/all 判断列表 [2, 4, 6, 8]：是否全是偶数？是否存在大于 5 的数？各输出一行。
# 3. 用 next 从 [("订单A", "已发货"), ("订单B", "待支付"), ("订单C", "待支付")] 里找第一个"待支付"的订单，找不到返回 "无"。
